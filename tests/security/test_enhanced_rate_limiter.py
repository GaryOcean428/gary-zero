"""Tests for enhanced rate limiting functionality."""

import asyncio
import pytest
import time
from datetime import datetime

from framework.security.enhanced_rate_limiter import (
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    EnhancedRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    create_rate_limiter,
)


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            burst_limit=3
        )
        self.limiter = SlidingWindowRateLimiter(self.config)
    
    @pytest.mark.asyncio
    async def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        for i in range(3):
            result = await self.limiter.is_allowed("user1", 5, 60)
            assert result.allowed
            assert result.remaining == 5 - i - 1
    
    @pytest.mark.asyncio
    async def test_denies_requests_over_limit(self):
        """Test that requests over limit are denied."""
        # Use up the limit
        for i in range(5):
            result = await self.limiter.is_allowed("user1", 5, 60)
            assert result.allowed
        
        # Next request should be denied
        result = await self.limiter.is_allowed("user1", 5, 60)
        assert not result.allowed
        assert result.remaining == 0
        assert result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_different_users_independent_limits(self):
        """Test that different users have independent limits."""
        # User1 uses up their limit
        for i in range(5):
            result = await self.limiter.is_allowed("user1", 5, 60)
            assert result.allowed
        
        # User2 should still be able to make requests
        result = await self.limiter.is_allowed("user2", 5, 60)
        assert result.allowed
        assert result.remaining == 4
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_minute_limit(self):
        """Test minute-based rate limiting."""
        # Use up minute limit
        for i in range(self.config.requests_per_minute):
            result = await self.limiter.check_rate_limit("user1")
            assert result.allowed
        
        # Next request should be denied due to minute limit
        result = await self.limiter.check_rate_limit("user1")
        assert not result.allowed
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_burst_limit(self):
        """Test burst limit enforcement."""
        # Use up burst limit quickly
        for i in range(self.config.burst_limit):
            result = await self.limiter.check_rate_limit("user1")
            assert result.allowed
        
        # Next request should be denied due to burst limit
        result = await self.limiter.check_rate_limit("user1")
        assert not result.allowed
    
    def test_clear_limits(self):
        """Test clearing rate limits."""
        self.limiter._windows["user1:minute"].append(time.time())
        self.limiter._windows["user2:minute"].append(time.time())
        
        # Clear specific user
        self.limiter.clear_limits("user1")
        assert len([k for k in self.limiter._windows.keys() if k.startswith("user1")]) == 0
        assert len([k for k in self.limiter._windows.keys() if k.startswith("user2")]) > 0
        
        # Clear all
        self.limiter.clear_limits()
        assert len(self.limiter._windows) == 0


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.limiter = TokenBucketRateLimiter()
    
    @pytest.mark.asyncio
    async def test_allows_requests_with_tokens(self):
        """Test that requests are allowed when tokens are available."""
        result = await self.limiter.is_allowed("user1", capacity=10, refill_rate=1)
        assert result.allowed
        assert result.remaining == 9
    
    @pytest.mark.asyncio
    async def test_denies_requests_without_tokens(self):
        """Test that requests are denied when no tokens available."""
        # Use up all tokens
        for i in range(5):
            result = await self.limiter.is_allowed("user1", capacity=5, refill_rate=1)
            assert result.allowed
        
        # Next request should be denied
        result = await self.limiter.is_allowed("user1", capacity=5, refill_rate=1)
        assert not result.allowed
        assert result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens are refilled over time."""
        # Use up all tokens
        for i in range(5):
            result = await self.limiter.is_allowed("user1", capacity=5, refill_rate=10)
            assert result.allowed
        
        # Wait for refill (simulate time passing)
        await asyncio.sleep(0.1)  # 0.1 seconds * 10 tokens/sec = 1 token
        
        # Should be able to make another request
        result = await self.limiter.is_allowed("user1", capacity=5, refill_rate=10, tokens_required=1)
        assert result.allowed
    
    @pytest.mark.asyncio
    async def test_multiple_tokens_required(self):
        """Test requesting multiple tokens at once."""
        # Should allow 5-token request from full bucket
        result = await self.limiter.is_allowed("user1", capacity=10, refill_rate=1, tokens_required=5)
        assert result.allowed
        assert result.remaining == 5
        
        # Should deny 6-token request (only 5 remaining)
        result = await self.limiter.is_allowed("user1", capacity=10, refill_rate=1, tokens_required=6)
        assert not result.allowed


class TestEnhancedRateLimiter:
    """Test enhanced rate limiter with multiple algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5
        )
        self.limiter = EnhancedRateLimiter(self.config)
    
    @pytest.mark.asyncio
    async def test_default_endpoint_rate_limiting(self):
        """Test rate limiting for default endpoint."""
        # Should allow requests within limit
        for i in range(5):
            result = await self.limiter.check_rate_limit("user1")
            assert result.allowed
        
        # Should deny when over limit
        result = await self.limiter.check_rate_limit("user1")
        assert not result.allowed
    
    @pytest.mark.asyncio
    async def test_endpoint_specific_rate_limiting(self):
        """Test endpoint-specific rate limiting."""
        # Chat endpoint has lower limits
        for i in range(5):  # burst limit for chat
            result = await self.limiter.check_rate_limit("user1", "api.chat")
            assert result.allowed
        
        # Next request should be denied
        result = await self.limiter.check_rate_limit("user1", "api.chat")
        assert not result.allowed
        
        # But tool endpoint should still work
        result = await self.limiter.check_rate_limit("user1", "api.tool")
        assert result.allowed
    
    @pytest.mark.asyncio
    async def test_token_bucket_limiting(self):
        """Test token bucket rate limiting."""
        result = await self.limiter.check_token_bucket("user1", capacity=5, refill_rate=1)
        assert result.allowed
        assert result.remaining == 4
    
    @pytest.mark.asyncio
    async def test_global_rate_limiting(self):
        """Test global rate limiting across all users."""
        # Should allow requests within global limit
        for i in range(3):
            result = await self.limiter.check_global_rate_limit(5, 60)
            assert result.allowed
        
        # Should still allow more requests (not at limit yet)
        result = await self.limiter.check_global_rate_limit(5, 60)
        assert result.allowed
    
    def test_get_rate_limit_info(self):
        """Test getting rate limit configuration."""
        info = self.limiter.get_rate_limit_info("user1", "api.chat")
        assert info["endpoint"] == "api.chat"
        assert info["requests_per_minute"] == 30  # Chat endpoint limit
        assert info["burst_limit"] == 5
    
    def test_add_endpoint_config(self):
        """Test adding new endpoint configuration."""
        new_config = RateLimitConfig(
            requests_per_minute=20,
            requests_per_hour=200,
            burst_limit=8
        )
        
        self.limiter.add_endpoint_config("api.custom", new_config)
        
        info = self.limiter.get_rate_limit_info("user1", "api.custom")
        assert info["requests_per_minute"] == 20
        assert info["burst_limit"] == 8
    
    def test_clear_user_limits(self):
        """Test clearing limits for specific user."""
        # Create some rate limit state
        self.limiter.limiter._windows["rate_limit:user1:minute"].append(time.time())
        
        # Clear user limits
        self.limiter.clear_user_limits("user1")
        
        # Should have cleared the state
        remaining_keys = [k for k in self.limiter.limiter._windows.keys() if "user1" in k]
        assert len(remaining_keys) == 0


class TestRateLimitConfig:
    """Test rate limit configuration."""
    
    def test_config_creation(self):
        """Test creating rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_limit=10,
            window_size_seconds=60
        )
        
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_limit == 10
        assert config.window_size_seconds == 60


class TestRateLimitResult:
    """Test rate limit result."""
    
    def test_result_creation(self):
        """Test creating rate limit result."""
        result = RateLimitResult(
            allowed=True,
            remaining=5,
            reset_time=datetime.now(),
            retry_after=None
        )
        
        assert result.allowed
        assert result.remaining == 5
        assert result.retry_after is None


def test_create_rate_limiter_factory():
    """Test rate limiter factory function."""
    limiter = create_rate_limiter(
        requests_per_minute=30,
        requests_per_hour=500,
        burst_limit=8
    )
    
    assert isinstance(limiter, EnhancedRateLimiter)
    assert limiter.config.requests_per_minute == 30
    assert limiter.config.requests_per_hour == 500
    assert limiter.config.burst_limit == 8


class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(requests_per_minute=5)
        self.limiter = SlidingWindowRateLimiter(self.config)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_same_user(self):
        """Test concurrent requests from the same user."""
        async def make_request():
            return await self.limiter.is_allowed("user1", 5, 60)
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Only 5 should be allowed
        allowed_count = sum(1 for result in results if result.allowed)
        denied_count = sum(1 for result in results if not result.allowed)
        
        assert allowed_count == 5
        assert denied_count == 5
    
    @pytest.mark.asyncio
    async def test_zero_limit(self):
        """Test behavior with zero rate limit."""
        result = await self.limiter.is_allowed("user1", 0, 60)
        assert not result.allowed
        assert result.remaining == 0
    
    @pytest.mark.asyncio
    async def test_very_large_limit(self):
        """Test behavior with very large rate limit."""
        result = await self.limiter.is_allowed("user1", 1000000, 60)
        assert result.allowed
        assert result.remaining == 999999