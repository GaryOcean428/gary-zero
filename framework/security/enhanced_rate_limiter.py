"""Enhanced rate limiting with sliding window algorithm and Redis backend support.

Provides sophisticated rate limiting capabilities including:
- Sliding window rate limiting
- Token bucket algorithm
- Per-user and per-endpoint limits
- Distributed rate limiting with Redis
- Rate limit status tracking
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size_seconds: int = 60


class SlidingWindowRateLimiter:
    """Sliding window rate limiter with memory backend."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._windows: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed within rate limit."""
        async with self._lock:
            now = time.time()
            window = self._windows[key]
            
            # Remove old entries outside the window
            while window and window[0] <= now - window_seconds:
                window.popleft()
            
            # Check if we're within limit
            current_count = len(window)
            
            if current_count >= limit:
                # Calculate when the oldest entry will expire
                if window:
                    oldest_entry = window[0]
                    reset_time = datetime.fromtimestamp(oldest_entry + window_seconds)
                    retry_after = int((oldest_entry + window_seconds) - now)
                else:
                    reset_time = datetime.now() + timedelta(seconds=window_seconds)
                    retry_after = window_seconds
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            # Add current request
            window.append(now)
            
            # Calculate next reset time
            reset_time = datetime.fromtimestamp(now + window_seconds)
            
            return RateLimitResult(
                allowed=True,
                remaining=limit - current_count - 1,
                reset_time=reset_time
            )
    
    async def check_rate_limit(self, key: str) -> RateLimitResult:
        """Check rate limit using configured limits."""
        # Check minute limit first
        minute_result = await self.is_allowed(
            f"{key}:minute", 
            self.config.requests_per_minute, 
            60
        )
        
        if not minute_result.allowed:
            return minute_result
        
        # Check hour limit
        hour_result = await self.is_allowed(
            f"{key}:hour", 
            self.config.requests_per_hour, 
            3600
        )
        
        if not hour_result.allowed:
            return hour_result
        
        # Check burst limit
        burst_result = await self.is_allowed(
            f"{key}:burst", 
            self.config.burst_limit, 
            10  # 10 second burst window
        )
        
        return burst_result
    
    def clear_limits(self, key: str = None) -> None:
        """Clear rate limits for a key or all keys."""
        if key:
            keys_to_remove = [k for k in self._windows.keys() if k.startswith(key)]
            for k in keys_to_remove:
                del self._windows[k]
        else:
            self._windows.clear()


class TokenBucketRateLimiter:
    """Token bucket rate limiter for bursty traffic."""
    
    @dataclass
    class Bucket:
        """Token bucket state."""
        tokens: float
        last_refill: float
        capacity: float
        refill_rate: float  # tokens per second
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucketRateLimiter.Bucket] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(
        self, 
        key: str, 
        capacity: float, 
        refill_rate: float, 
        tokens_required: float = 1.0
    ) -> RateLimitResult:
        """Check if request is allowed using token bucket algorithm."""
        async with self._lock:
            now = time.time()
            
            # Get or create bucket
            if key not in self._buckets:
                self._buckets[key] = self.Bucket(
                    tokens=capacity,
                    last_refill=now,
                    capacity=capacity,
                    refill_rate=refill_rate
                )
            
            bucket = self._buckets[key]
            
            # Refill tokens based on elapsed time
            elapsed = now - bucket.last_refill
            bucket.tokens = min(
                bucket.capacity,
                bucket.tokens + (elapsed * bucket.refill_rate)
            )
            bucket.last_refill = now
            
            # Check if we have enough tokens
            if bucket.tokens >= tokens_required:
                bucket.tokens -= tokens_required
                
                # Calculate when bucket will be full again
                time_to_full = (bucket.capacity - bucket.tokens) / bucket.refill_rate
                reset_time = datetime.fromtimestamp(now + time_to_full)
                
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket.tokens),
                    reset_time=reset_time
                )
            else:
                # Calculate when we'll have enough tokens
                tokens_needed = tokens_required - bucket.tokens
                wait_time = tokens_needed / bucket.refill_rate
                reset_time = datetime.fromtimestamp(now + wait_time)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=int(wait_time)
                )


class RedisRateLimiter:
    """Redis-backed rate limiter for distributed systems."""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._lua_script = None
    
    async def _get_lua_script(self):
        """Get or create the Lua script for atomic operations."""
        if not self._lua_script:
            script = """
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            
            -- Remove old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            
            -- Count current entries
            local current = redis.call('ZCARD', key)
            
            if current < limit then
                -- Add current request
                redis.call('ZADD', key, now, now)
                redis.call('EXPIRE', key, window)
                return {1, limit - current - 1}
            else
                return {0, 0}
            end
            """
            self._lua_script = self.redis.register_script(script)
        
        return self._lua_script
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed using Redis backend."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")
        
        now = time.time()
        script = await self._get_lua_script()
        
        try:
            result = await script(keys=[key], args=[window_seconds, limit, now])
            allowed, remaining = result
            
            if allowed:
                reset_time = datetime.fromtimestamp(now + window_seconds)
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=reset_time
                )
            else:
                # Get the oldest entry to calculate retry time
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int((oldest_time + window_seconds) - now)
                    reset_time = datetime.fromtimestamp(oldest_time + window_seconds)
                else:
                    retry_after = window_seconds
                    reset_time = datetime.fromtimestamp(now + window_seconds)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
        
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            # Fallback: allow request but log error
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=datetime.now() + timedelta(minutes=1)
            )


class EnhancedRateLimiter:
    """Enhanced rate limiter with multiple algorithms and backends."""
    
    def __init__(
        self, 
        config: RateLimitConfig,
        redis_client=None,
        use_redis: bool = False
    ):
        self.config = config
        self.use_redis = use_redis and redis_client is not None
        
        if self.use_redis:
            self.limiter = RedisRateLimiter(redis_client)
        else:
            self.limiter = SlidingWindowRateLimiter(config)
        
        self.token_bucket = TokenBucketRateLimiter()
        
        # Rate limit configurations for different endpoints
        self.endpoint_configs = {
            'api.chat': RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                burst_limit=5
            ),
            'api.tool': RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_limit=10
            ),
            'api.upload': RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                burst_limit=2
            ),
            'auth.login': RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=20,
                burst_limit=3
            )
        }
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        endpoint: str = 'default',
        tokens_required: float = 1.0
    ) -> RateLimitResult:
        """
        Check rate limit for user and endpoint.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint identifier
            tokens_required: Number of tokens required (for token bucket)
        
        Returns:
            RateLimitResult with allow/deny decision
        """
        # Get configuration for endpoint
        config = self.endpoint_configs.get(endpoint, self.config)
        
        # Create composite key
        key = f"rate_limit:{user_id}:{endpoint}"
        
        if self.use_redis:
            # Use Redis sliding window
            minute_result = await self.limiter.is_allowed(
                f"{key}:minute", 
                config.requests_per_minute, 
                60
            )
            
            if not minute_result.allowed:
                return minute_result
            
            hour_result = await self.limiter.is_allowed(
                f"{key}:hour", 
                config.requests_per_hour, 
                3600
            )
            
            return hour_result
        else:
            # Use memory-based sliding window
            return await self.limiter.check_rate_limit(key)
    
    async def check_token_bucket(
        self, 
        user_id: str, 
        capacity: float = 10.0, 
        refill_rate: float = 1.0,
        tokens_required: float = 1.0
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        key = f"token_bucket:{user_id}"
        return await self.token_bucket.is_allowed(
            key, capacity, refill_rate, tokens_required
        )
    
    async def check_global_rate_limit(self, limit: int, window_seconds: int) -> RateLimitResult:
        """Check global rate limit across all users."""
        key = "global_rate_limit"
        
        if self.use_redis:
            return await self.limiter.is_allowed(key, limit, window_seconds)
        else:
            return await self.limiter.is_allowed(key, limit, window_seconds)
    
    def get_rate_limit_info(self, user_id: str, endpoint: str = 'default') -> Dict[str, any]:
        """Get rate limit configuration for user and endpoint."""
        config = self.endpoint_configs.get(endpoint, self.config)
        
        return {
            'endpoint': endpoint,
            'requests_per_minute': config.requests_per_minute,
            'requests_per_hour': config.requests_per_hour,
            'burst_limit': config.burst_limit,
            'window_size_seconds': config.window_size_seconds
        }
    
    def add_endpoint_config(self, endpoint: str, config: RateLimitConfig) -> None:
        """Add rate limit configuration for a new endpoint."""
        self.endpoint_configs[endpoint] = config
        logger.info(f"Added rate limit config for endpoint: {endpoint}")
    
    def clear_user_limits(self, user_id: str) -> None:
        """Clear all rate limits for a specific user."""
        if hasattr(self.limiter, 'clear_limits'):
            self.limiter.clear_limits(f"rate_limit:{user_id}")
        
        # Clear token bucket limits
        key = f"token_bucket:{user_id}"
        if key in self.token_bucket._buckets:
            del self.token_bucket._buckets[key]
        
        logger.info(f"Cleared rate limits for user: {user_id}")


# Factory function for creating rate limiters
def create_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    burst_limit: int = 10,
    redis_client=None,
    use_redis: bool = False
) -> EnhancedRateLimiter:
    """Create a rate limiter with the specified configuration."""
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        burst_limit=burst_limit
    )
    
    return EnhancedRateLimiter(
        config=config,
        redis_client=redis_client,
        use_redis=use_redis
    )