"""Multi-level caching system for the Gary-Zero framework.

Implements sophisticated caching strategies including:
- Memory caching with LRU eviction
- Redis-backed distributed caching
- Function-level caching decorators
- Cache invalidation strategies
- Performance monitoring
"""

import asyncio
import hashlib
import pickle
import time
import logging
from typing import Any, Callable, Dict, Optional, Union, TypeVar, Awaitable
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass 
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """In-memory LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if entry has expired
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._cache[key]
                self._stats.misses += 1
                return None
            
            # Update access metadata
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats.hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        async with self._lock:
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            entry = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = entry
                
                # Evict oldest if at capacity
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats.evictions += 1
            
            self._stats.sets += 1
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count."""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats
    
    def get_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisCache:
    """Redis-backed cache for distributed systems."""
    
    def __init__(self, redis_client, key_prefix: str = "cache:", default_ttl: Optional[int] = None):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._stats = CacheStats()
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Any:
        """Get value from Redis cache."""
        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)
            
            if data is None:
                self._stats.misses += 1
                return None
            
            # Deserialize value
            value = pickle.loads(data)
            self._stats.hits += 1
            return value
            
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            self._stats.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache."""
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl or self.default_ttl:
                await self.redis.setex(redis_key, ttl or self.default_ttl, data)
            else:
                await self.redis.set(redis_key, data)
            
            self._stats.sets += 1
            
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries with prefix."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats


class MultiLevelCache:
    """Multi-level cache with memory (L1) and Redis (L2) backends."""
    
    def __init__(
        self,
        l1_cache: LRUCache,
        l2_cache: Optional[RedisCache] = None,
        l1_ttl: int = 60,  # L1 cache TTL in seconds
        l2_ttl: int = 3600  # L2 cache TTL in seconds
    ):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self._stats = CacheStats()
    
    async def get(self, key: str) -> Any:
        """Get value from multi-level cache."""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            self._stats.hits += 1
            return value
        
        # Try L2 cache if available
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                # Populate L1 cache
                await self.l1_cache.set(key, value, self.l1_ttl)
                self._stats.hits += 1
                return value
        
        self._stats.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in multi-level cache."""
        # Set in L1 cache
        await self.l1_cache.set(key, value, ttl or self.l1_ttl)
        
        # Set in L2 cache if available
        if self.l2_cache:
            await self.l2_cache.set(key, value, ttl or self.l2_ttl)
        
        self._stats.sets += 1
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels."""
        l1_deleted = await self.l1_cache.delete(key)
        l2_deleted = True
        
        if self.l2_cache:
            l2_deleted = await self.l2_cache.delete(key)
        
        return l1_deleted or l2_deleted
    
    async def clear(self) -> None:
        """Clear all cache levels."""
        await self.l1_cache.clear()
        if self.l2_cache:
            await self.l2_cache.clear()
    
    def get_combined_stats(self) -> Dict[str, CacheStats]:
        """Get statistics from all cache levels."""
        stats = {
            'combined': self._stats,
            'l1': self.l1_cache.get_stats()
        }
        
        if self.l2_cache:
            stats['l2'] = self.l2_cache.get_stats()
        
        return stats


def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = pickle.dumps((args, sorted(kwargs.items())))
    return hashlib.sha256(key_data).hexdigest()


def cached(
    cache: Union[LRUCache, RedisCache, MultiLevelCache],
    ttl: Optional[int] = None,
    key_prefix: str = "",
    skip_if: Optional[Callable[..., bool]] = None
):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance to use
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        skip_if: Function to determine if caching should be skipped
    """
    def decorator(func: Callable[..., Union[T, Awaitable[T]]]) -> Callable[..., Union[T, Awaitable[T]]]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if skip_if and skip_if(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Generate cache key
            key = f"{key_prefix}{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache.set(key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to handle async cache operations
            async def run():
                if skip_if and skip_if(*args, **kwargs):
                    return func(*args, **kwargs)
                
                key = f"{key_prefix}{func.__name__}:{cache_key_generator(*args, **kwargs)}"
                
                cached_result = await cache.get(key)
                if cached_result is not None:
                    return cached_result
                
                result = func(*args, **kwargs)
                
                if result is not None:
                    await cache.set(key, result, ttl)
                
                return result
            
            # Run async operations in event loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(run())
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(run())
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CacheManager:
    """Manager for multiple cache instances and strategies."""
    
    def __init__(self):
        self._caches: Dict[str, Union[LRUCache, RedisCache, MultiLevelCache]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def register_cache(self, name: str, cache: Union[LRUCache, RedisCache, MultiLevelCache]) -> None:
        """Register a cache instance."""
        self._caches[name] = cache
        logger.info(f"Registered cache: {name}")
    
    def get_cache(self, name: str) -> Optional[Union[LRUCache, RedisCache, MultiLevelCache]]:
        """Get cache instance by name."""
        return self._caches.get(name)
    
    async def clear_all_caches(self) -> None:
        """Clear all registered caches."""
        for name, cache in self._caches.items():
            try:
                await cache.clear()
                logger.info(f"Cleared cache: {name}")
            except Exception as e:
                logger.error(f"Error clearing cache {name}: {e}")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics from all caches."""
        stats = {}
        for name, cache in self._caches.items():
            try:
                if hasattr(cache, 'get_combined_stats'):
                    stats[name] = cache.get_combined_stats()
                else:
                    stats[name] = cache.get_stats()
            except Exception as e:
                logger.error(f"Error getting stats for cache {name}: {e}")
                stats[name] = {"error": str(e)}
        
        return stats
    
    async def start_cleanup_task(self, interval: int = 300) -> None:
        """Start periodic cleanup task for expired entries."""
        if self._cleanup_task:
            return
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    
                    for name, cache in self._caches.items():
                        if hasattr(cache, 'cleanup_expired'):
                            expired_count = await cache.cleanup_expired()
                            if expired_count > 0:
                                logger.info(f"Cleaned up {expired_count} expired entries from cache: {name}")
                        elif hasattr(cache, 'l1_cache') and hasattr(cache.l1_cache, 'cleanup_expired'):
                            expired_count = await cache.l1_cache.cleanup_expired()
                            if expired_count > 0:
                                logger.info(f"Cleaned up {expired_count} expired entries from L1 cache: {name}")
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cache cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("Started cache cleanup task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped cache cleanup task")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def create_cache_hierarchy(redis_client=None) -> MultiLevelCache:
    """Create a default cache hierarchy with memory L1 and optional Redis L2."""
    l1_cache = LRUCache(max_size=1000, default_ttl=300)  # 5 minutes
    l2_cache = None
    
    if redis_client:
        l2_cache = RedisCache(redis_client, default_ttl=3600)  # 1 hour
    
    return MultiLevelCache(l1_cache, l2_cache)