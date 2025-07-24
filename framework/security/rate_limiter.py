"""Rate limiting system for API endpoints and tool execution."""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int
    window_size: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_allowance: int = 0  # additional requests allowed in burst


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        async with self._lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available."""
        if self.tokens >= tokens:
            return 0
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


class SlidingWindowCounter:
    """Sliding window counter for rate limiting."""

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def add_request(self) -> int:
        """Add a request and return current count in window."""
        async with self._lock:
            now = time.time()
            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()

            self.requests.append(now)
            return len(self.requests)

    async def get_count(self) -> int:
        """Get current request count in window."""
        async with self._lock:
            now = time.time()
            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()

            return len(self.requests)


class RateLimiter:
    """Comprehensive rate limiting system."""

    def __init__(self):
        self.configs: dict[str, RateLimitConfig] = {}
        self.counters: dict[str, dict[str, SlidingWindowCounter]] = defaultdict(dict)
        self.buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        self.fixed_windows: dict[str, dict[str, tuple[int, float]]] = defaultdict(dict)

    def configure_limit(self, endpoint: str, config: RateLimitConfig) -> None:
        """Configure rate limit for an endpoint."""
        self.configs[endpoint] = config

    def configure_global_limits(self) -> None:
        """Configure default rate limits for common endpoints."""
        # User input rate limiting
        self.configure_limit(
            "user_input",
            RateLimitConfig(
                max_requests=100,
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
            ),
        )

        # Tool execution rate limiting
        self.configure_limit(
            "tool_execution",
            RateLimitConfig(
                max_requests=50,
                window_size=60,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                burst_allowance=10,
            ),
        )

        # API endpoint rate limiting
        self.configure_limit(
            "api_call",
            RateLimitConfig(
                max_requests=1000,
                window_size=3600,  # 1 hour
                strategy=RateLimitStrategy.SLIDING_WINDOW,
            ),
        )

        # Configuration changes
        self.configure_limit(
            "config_change",
            RateLimitConfig(
                max_requests=20,
                window_size=300,  # 5 minutes
                strategy=RateLimitStrategy.FIXED_WINDOW,
            ),
        )

    async def check_limit(self, endpoint: str, identifier: str) -> None:
        """Check if request is within rate limit."""
        if endpoint not in self.configs:
            return  # No limit configured

        config = self.configs[endpoint]

        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            await self._check_sliding_window(endpoint, identifier, config)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            await self._check_token_bucket(endpoint, identifier, config)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            await self._check_fixed_window(endpoint, identifier, config)

    async def _check_sliding_window(
        self, endpoint: str, identifier: str, config: RateLimitConfig
    ) -> None:
        """Check sliding window rate limit."""
        if identifier not in self.counters[endpoint]:
            self.counters[endpoint][identifier] = SlidingWindowCounter(
                config.window_size
            )

        counter = self.counters[endpoint][identifier]
        current_count = await counter.add_request()

        if current_count > config.max_requests:
            raise RateLimitExceeded(
                f"Rate limit exceeded for {endpoint}: {current_count}/{config.max_requests} "
                f"requests in {config.window_size}s",
                retry_after=config.window_size,
            )

    async def _check_token_bucket(
        self, endpoint: str, identifier: str, config: RateLimitConfig
    ) -> None:
        """Check token bucket rate limit."""
        if identifier not in self.buckets[endpoint]:
            refill_rate = config.max_requests / config.window_size
            capacity = config.max_requests + config.burst_allowance
            self.buckets[endpoint][identifier] = TokenBucket(capacity, refill_rate)

        bucket = self.buckets[endpoint][identifier]
        if not await bucket.consume():
            wait_time = bucket.get_wait_time()
            raise RateLimitExceeded(
                f"Rate limit exceeded for {endpoint}: token bucket empty",
                retry_after=wait_time,
            )

    async def _check_fixed_window(
        self, endpoint: str, identifier: str, config: RateLimitConfig
    ) -> None:
        """Check fixed window rate limit."""
        now = time.time()
        window_start = int(now // config.window_size) * config.window_size

        if identifier not in self.fixed_windows[endpoint]:
            self.fixed_windows[endpoint][identifier] = (0, window_start)

        count, last_window = self.fixed_windows[endpoint][identifier]

        if last_window != window_start:
            # New window, reset count
            count = 0
            last_window = window_start

        count += 1
        self.fixed_windows[endpoint][identifier] = (count, last_window)

        if count > config.max_requests:
            retry_after = window_start + config.window_size - now
            raise RateLimitExceeded(
                f"Rate limit exceeded for {endpoint}: {count}/{config.max_requests} "
                f"requests in current window",
                retry_after=retry_after,
            )

    async def get_limit_status(self, endpoint: str, identifier: str) -> dict[str, any]:
        """Get current rate limit status for an endpoint and identifier."""
        if endpoint not in self.configs:
            return {"status": "no_limit"}

        config = self.configs[endpoint]

        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            if identifier in self.counters[endpoint]:
                counter = self.counters[endpoint][identifier]
                current_count = await counter.get_count()
                return {
                    "status": "active",
                    "strategy": "sliding_window",
                    "current_requests": current_count,
                    "max_requests": config.max_requests,
                    "window_size": config.window_size,
                    "remaining": max(0, config.max_requests - current_count),
                }

        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            if identifier in self.buckets[endpoint]:
                bucket = self.buckets[endpoint][identifier]
                return {
                    "status": "active",
                    "strategy": "token_bucket",
                    "tokens_available": int(bucket.tokens),
                    "capacity": bucket.capacity,
                    "refill_rate": bucket.refill_rate,
                }

        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            if identifier in self.fixed_windows[endpoint]:
                count, window_start = self.fixed_windows[endpoint][identifier]
                now = time.time()
                current_window = int(now // config.window_size) * config.window_size

                if window_start != current_window:
                    count = 0

                return {
                    "status": "active",
                    "strategy": "fixed_window",
                    "current_requests": count,
                    "max_requests": config.max_requests,
                    "window_size": config.window_size,
                    "remaining": max(0, config.max_requests - count),
                    "window_reset": current_window + config.window_size,
                }

        return {
            "status": "configured",
            "strategy": config.strategy.value,
            "max_requests": config.max_requests,
            "window_size": config.window_size,
        }

    def reset_limits(
        self, endpoint: str | None = None, identifier: str | None = None
    ) -> None:
        """Reset rate limits for endpoint/identifier."""
        if endpoint is None:
            # Reset all limits
            self.counters.clear()
            self.buckets.clear()
            self.fixed_windows.clear()
        elif identifier is None:
            # Reset all limits for endpoint
            if endpoint in self.counters:
                self.counters[endpoint].clear()
            if endpoint in self.buckets:
                self.buckets[endpoint].clear()
            if endpoint in self.fixed_windows:
                self.fixed_windows[endpoint].clear()
        else:
            # Reset specific endpoint/identifier
            if endpoint in self.counters and identifier in self.counters[endpoint]:
                del self.counters[endpoint][identifier]
            if endpoint in self.buckets and identifier in self.buckets[endpoint]:
                del self.buckets[endpoint][identifier]
            if (
                endpoint in self.fixed_windows
                and identifier in self.fixed_windows[endpoint]
            ):
                del self.fixed_windows[endpoint][identifier]
