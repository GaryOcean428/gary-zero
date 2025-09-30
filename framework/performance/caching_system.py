"""
Advanced Caching System for Gary-Zero
Multi-layer caching with Redis compatibility and intelligent cache strategies
"""

import time
import hashlib
import json
import threading
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import pickle
import weakref
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(str, Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In, First Out


class CacheLevel(str, Enum):
    """Cache levels"""
    L1_MEMORY = "l1_memory"  # In-memory cache
    L2_REDIS = "l2_redis"    # Redis cache
    L3_DISK = "l3_disk"      # Disk-based cache


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def touch(self):
        """Update access metadata"""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def size(self) -> int:
        """Calculate entry size in bytes"""
        if self.size_bytes == 0:
            try:
                self.size_bytes = len(pickle.dumps(self.value))
            except:
                self.size_bytes = len(str(self.value).encode('utf-8'))
        return self.size_bytes


class CacheBackend(ABC):
    """Abstract cache backend interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value by key"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all keys"""
        pass
    
    @abstractmethod
    async def keys(self) -> List[str]:
        """Get all keys"""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with advanced eviction strategies"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, 
                 strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.strategy = strategy
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: OrderedDict = OrderedDict()
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                await self._remove_entry(key)
                self._misses += 1
                return None
            
            # Update access metadata
            entry.touch()
            self._hits += 1
            
            # Update access order for LRU
            if self.strategy in [CacheStrategy.LRU, CacheStrategy.FIFO]:
                self._access_order.move_to_end(key)
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value by key"""
        async with self._lock:
            # Create new entry
            entry = CacheEntry(key=key, value=value, ttl=ttl)
            entry_size = entry.size()
            
            # Check if we need to make space
            await self._ensure_space(entry_size)
            
            # Store entry
            self._cache[key] = entry
            self._access_order[key] = time.time()
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        async with self._lock:
            return await self._remove_entry(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                await self._remove_entry(key)
                return False
            
            return True
    
    async def clear(self) -> bool:
        """Clear all keys"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            return True
    
    async def keys(self) -> List[str]:
        """Get all keys"""
        async with self._lock:
            valid_keys = []
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
                else:
                    valid_keys.append(key)
            
            # Clean up expired keys
            for key in expired_keys:
                await self._remove_entry(key)
            
            return valid_keys
    
    async def _ensure_space(self, needed_bytes: int):
        """Ensure there's enough space for new entry"""
        # Check memory limit
        current_memory = sum(entry.size() for entry in self._cache.values())
        
        while (len(self._cache) >= self.max_size or 
               current_memory + needed_bytes > self.max_memory_bytes):
            
            if not self._cache:
                break
            
            # Find key to evict based on strategy
            evict_key = await self._select_eviction_key()
            if evict_key:
                await self._remove_entry(evict_key)
                current_memory = sum(entry.size() for entry in self._cache.values())
                self._evictions += 1
            else:
                break
    
    async def _select_eviction_key(self) -> Optional[str]:
        """Select key for eviction based on strategy"""
        if not self._cache:
            return None
        
        if self.strategy == CacheStrategy.LRU:
            # Least recently used
            return min(self._cache.keys(), 
                      key=lambda k: self._cache[k].accessed_at)
        
        elif self.strategy == CacheStrategy.LFU:
            # Least frequently used
            return min(self._cache.keys(), 
                      key=lambda k: self._cache[k].access_count)
        
        elif self.strategy == CacheStrategy.TTL:
            # Shortest TTL remaining (or oldest if no TTL)
            def ttl_key(k):
                entry = self._cache[k]
                if entry.ttl is None:
                    return entry.created_at
                return entry.created_at + entry.ttl
            
            return min(self._cache.keys(), key=ttl_key)
        
        elif self.strategy == CacheStrategy.FIFO:
            # First in, first out
            return next(iter(self._access_order))
        
        return next(iter(self._cache))
    
    async def _remove_entry(self, key: str) -> bool:
        """Remove entry from cache"""
        if key in self._cache:
            del self._cache[key]
        
        if key in self._access_order:
            del self._access_order[key]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        current_memory = sum(entry.size() for entry in self._cache.values())
        
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._evictions,
            "memory_used_mb": round(current_memory / 1024 / 1024, 2),
            "memory_limit_mb": round(self.max_memory_bytes / 1024 / 1024, 2),
            "strategy": self.strategy.value
        }


class RedisCacheBackend(CacheBackend):
    """Redis cache backend (simulated for now)"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # For now, use memory cache as fallback
        self._fallback = MemoryCacheBackend(max_size=10000)
        
        logger.info(f"Redis cache backend initialized (using fallback)")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.exists(key)
    
    async def clear(self) -> bool:
        """Clear all keys from Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.clear()
    
    async def keys(self) -> List[str]:
        """Get all keys from Redis"""
        # TODO: Implement actual Redis connection
        return await self._fallback.keys()


class MultiLevelCache:
    """
    Multi-level cache system with L1 (memory), L2 (Redis), L3 (disk) support
    """
    
    def __init__(self, l1_config: Optional[Dict] = None, 
                 l2_config: Optional[Dict] = None,
                 l3_config: Optional[Dict] = None):
        
        # Initialize cache levels
        self.levels: Dict[CacheLevel, CacheBackend] = {}
        
        # L1 Memory cache (always present)
        l1_config = l1_config or {}
        self.levels[CacheLevel.L1_MEMORY] = MemoryCacheBackend(**l1_config)
        
        # L2 Redis cache (optional)
        if l2_config:
            self.levels[CacheLevel.L2_REDIS] = RedisCacheBackend(**l2_config)
        
        # L3 Disk cache (optional, not implemented yet)
        if l3_config:
            logger.info("L3 disk cache not implemented yet")
        
        # Statistics
        self._stats = {level: {"hits": 0, "misses": 0} for level in self.levels}
        
        logger.info(f"Multi-level cache initialized with {len(self.levels)} levels")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all levels)"""
        
        # Try each level in order
        for level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_DISK]:
            if level not in self.levels:
                continue
            
            backend = self.levels[level]
            value = await backend.get(key)
            
            if value is not None:
                self._stats[level]["hits"] += 1
                
                # Promote to higher levels
                await self._promote_to_higher_levels(key, value, level)
                
                return value
            else:
                self._stats[level]["misses"] += 1
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None, 
                  levels: Optional[List[CacheLevel]] = None) -> bool:
        """Set value in cache (writes to specified levels)"""
        
        if levels is None:
            levels = list(self.levels.keys())
        
        success = True
        for level in levels:
            if level in self.levels:
                backend = self.levels[level]
                if not await backend.set(key, value, ttl):
                    success = False
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels"""
        success = True
        for backend in self.levels.values():
            if not await backend.delete(key):
                success = False
        return success
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache level"""
        for backend in self.levels.values():
            if await backend.exists(key):
                return True
        return False
    
    async def clear(self, levels: Optional[List[CacheLevel]] = None) -> bool:
        """Clear specified cache levels"""
        if levels is None:
            levels = list(self.levels.keys())
        
        success = True
        for level in levels:
            if level in self.levels:
                if not await self.levels[level].clear():
                    success = False
        
        return success
    
    async def _promote_to_higher_levels(self, key: str, value: Any, found_level: CacheLevel):
        """Promote cache entry to higher levels"""
        level_order = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_DISK]
        found_index = level_order.index(found_level)
        
        # Promote to all higher levels
        for i in range(found_index):
            higher_level = level_order[i]
            if higher_level in self.levels:
                await self.levels[higher_level].set(key, value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {"levels": {}}
        
        for level, backend in self.levels.items():
            level_stats = self._stats[level].copy()
            
            # Add backend-specific stats if available
            if hasattr(backend, 'get_stats'):
                level_stats.update(backend.get_stats())
            
            stats["levels"][level.value] = level_stats
        
        # Calculate overall stats
        total_hits = sum(self._stats[level]["hits"] for level in self.levels)
        total_misses = sum(self._stats[level]["misses"] for level in self.levels)
        total_requests = total_hits + total_misses
        
        stats["total"] = {
            "hits": total_hits,
            "misses": total_misses,
            "requests": total_requests,
            "hit_rate_percent": (total_hits / total_requests * 100) if total_requests > 0 else 0
        }
        
        return stats


# Caching decorators
def cached(ttl: Optional[float] = None, key_prefix: str = "", 
           cache_instance: Optional[MultiLevelCache] = None):
    """Decorator for caching function results"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = cache_instance or get_default_cache()
        
        async def async_wrapper(*args, **kwargs) -> T:
            # Generate cache key
            key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = await cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Store in cache
            await cache.set(key, result, ttl)
            return result
        
        def sync_wrapper(*args, **kwargs) -> T:
            # For sync functions, run async cache operations in event loop
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(key_pattern: str, cache_instance: Optional[MultiLevelCache] = None):
    """Decorator to invalidate cache entries after function execution"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = cache_instance or get_default_cache()
        
        async def async_wrapper(*args, **kwargs) -> T:
            # Execute function first
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Invalidate cache pattern
            await _invalidate_pattern(cache, key_pattern, args, kwargs)
            return result
        
        def sync_wrapper(*args, **kwargs) -> T:
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = "") -> str:
    """Generate cache key from function and arguments"""
    
    # Create base key from function name and module
    base_key = f"{func.__module__}.{func.__name__}"
    
    # Add arguments to key
    args_str = ""
    if args:
        args_str = "_".join(str(arg) for arg in args)
    
    kwargs_str = ""
    if kwargs:
        kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Combine and hash for consistent length
    full_key = f"{prefix}:{base_key}:{args_str}:{kwargs_str}"
    return hashlib.md5(full_key.encode()).hexdigest()


async def _invalidate_pattern(cache: MultiLevelCache, pattern: str, args: tuple, kwargs: dict):
    """Invalidate cache entries matching pattern"""
    # For now, just delete exact key
    # TODO: Implement pattern matching for wildcard invalidation
    await cache.delete(pattern)


# Global cache instance
_default_cache: Optional[MultiLevelCache] = None


def get_default_cache() -> MultiLevelCache:
    """Get or create default cache instance"""
    global _default_cache
    if _default_cache is None:
        _default_cache = MultiLevelCache(
            l1_config={"max_size": 1000, "max_memory_mb": 50},
            l2_config=None  # Redis not configured by default
        )
    return _default_cache


def configure_cache(l1_config: Optional[Dict] = None,
                   l2_config: Optional[Dict] = None,
                   l3_config: Optional[Dict] = None) -> MultiLevelCache:
    """Configure global cache instance"""
    global _default_cache
    _default_cache = MultiLevelCache(l1_config, l2_config, l3_config)
    return _default_cache


# Example usage
if __name__ == "__main__":
    async def main():
        # Create cache
        cache = MultiLevelCache(
            l1_config={"max_size": 100, "max_memory_mb": 10}
        )
        
        # Test basic operations
        await cache.set("test_key", {"data": "test_value"}, ttl=60)
        value = await cache.get("test_key")
        print(f"Cached value: {value}")
        
        # Test decorator
        @cached(ttl=30)
        async def expensive_operation(x: int) -> int:
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * x
        
        # First call - will be cached
        result1 = await expensive_operation(5)
        
        # Second call - will use cache
        result2 = await expensive_operation(5)
        
        print(f"Results: {result1}, {result2}")
        print(f"Cache stats: {cache.get_stats()}")
    
    asyncio.run(main())