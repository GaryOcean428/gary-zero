"""
Multi-tier caching system for performance optimization.

Provides flexible caching with multiple backends and strategies:
- In-memory caching for fast access
- Persistent caching for durability
- Smart cache invalidation and TTL management
- Cache warming and preloading strategies
"""

import json
import pickle
import time
import weakref
from abc import ABC, abstractmethod
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional, Union, Callable, List
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get cache size."""
        pass


class MemoryCache(CacheBackend):
    """High-performance in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = RLock()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if 'expires_at' not in entry:
            return False
        return time.time() > entry['expires_at']
    
    def _evict_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if 'expires_at' in entry and current_time > entry['expires_at']
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries if over max_size."""
        if len(self._cache) <= self.max_size:
            return
        
        # Sort by access time and remove oldest
        sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
        to_remove = len(self._cache) - self.max_size
        
        for key, _ in sorted_keys[:to_remove]:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            self._evict_expired()
            
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if self._is_expired(entry):
                self.delete(key)
                return None
            
            # Update access time for LRU
            self._access_times[key] = time.time()
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        with self._lock:
            # First evict expired entries
            self._evict_expired()
            
            entry = {'value': value}
            
            # Set expiration time
            ttl_to_use = ttl if ttl is not None else self.default_ttl
            if ttl_to_use is not None:
                entry['expires_at'] = time.time() + ttl_to_use
            
            self._cache[key] = entry
            self._access_times[key] = time.time()
            
            # Then evict LRU if we're over the limit
            self._evict_lru()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            self._evict_expired()
            if key not in self._cache:
                return False
            return not self._is_expired(self._cache[key])
    
    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            self._evict_expired()
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._evict_expired()
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_ratio': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1),
                'memory_usage': sum(len(str(entry)) for entry in self._cache.values())
            }


class PersistentCache(CacheBackend):
    """File-based persistent cache with JSON/pickle serialization."""
    
    def __init__(self, cache_dir: str = ".cache", serializer: str = "json"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.serializer = serializer
        self._lock = RLock()
    
    def _get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data based on configured serializer."""
        if self.serializer == "json":
            return json.dumps(data, default=str).encode()
        elif self.serializer == "pickle":
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unknown serializer: {self.serializer}")
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data based on configured serializer."""
        if self.serializer == "json":
            return json.loads(data.decode())
        elif self.serializer == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"Unknown serializer: {self.serializer}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            path = self._get_path(key)
            if not path.exists():
                return None
            
            try:
                with open(path, 'rb') as f:
                    entry = self._deserialize(f.read())
                
                # Check expiration
                if 'expires_at' in entry and time.time() > entry['expires_at']:
                    self.delete(key)
                    return None
                
                return entry['value']
            except Exception as e:
                logger.warning(f"Failed to read cache entry {key}: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        with self._lock:
            path = self._get_path(key)
            
            entry = {'value': value}
            if ttl is not None:
                entry['expires_at'] = time.time() + ttl
            
            try:
                with open(path, 'wb') as f:
                    f.write(self._serialize(entry))
            except Exception as e:
                logger.error(f"Failed to write cache entry {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            path = self._get_path(key)
            if path.exists():
                try:
                    path.unlink()
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete cache entry {key}: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete cache file {cache_file}: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            path = self._get_path(key)
            if not path.exists():
                return False
            
            # Check if not expired
            return self.get(key) is not None
    
    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            return len(list(self.cache_dir.glob("*.cache")))


class CacheManager:
    """Multi-tier cache manager with fallback strategies."""
    
    def __init__(self, 
                 primary: Optional[CacheBackend] = None,
                 secondary: Optional[CacheBackend] = None):
        self.primary = primary or MemoryCache()
        self.secondary = secondary
        self._stats = {
            'hits': 0,
            'misses': 0,
            'primary_hits': 0,
            'secondary_hits': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback."""
        # Try primary cache first
        value = self.primary.get(key)
        if value is not None:
            self._stats['hits'] += 1
            self._stats['primary_hits'] += 1
            return value
        
        # Try secondary cache if available
        if self.secondary:
            value = self.secondary.get(key)
            if value is not None:
                # Promote to primary cache
                self.primary.set(key, value)
                self._stats['hits'] += 1
                self._stats['secondary_hits'] += 1
                return value
        
        self._stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in both cache tiers."""
        self.primary.set(key, value, ttl)
        if self.secondary:
            self.secondary.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from both cache tiers."""
        primary_deleted = self.primary.delete(key)
        secondary_deleted = self.secondary.delete(key) if self.secondary else False
        return primary_deleted or secondary_deleted
    
    def clear(self) -> None:
        """Clear both cache tiers."""
        self.primary.clear()
        if self.secondary:
            self.secondary.clear()
        
        # Reset stats
        self._stats = {
            'hits': 0,
            'misses': 0,
            'primary_hits': 0,
            'secondary_hits': 0
        }
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any cache tier."""
        return self.primary.exists(key) or (
            self.secondary and self.secondary.exists(key)
        )
    
    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_ratio = self._stats['hits'] / max(total_requests, 1)
        
        return {
            'hit_ratio': hit_ratio,
            'total_requests': total_requests,
            'primary_cache_size': self.primary.size(),
            'secondary_cache_size': self.secondary.size() if self.secondary else 0,
            **self._stats
        }
    
    def cache(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """Decorator for caching function results."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator


# Global cache manager instance
_default_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the default cache manager instance."""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager(
            primary=MemoryCache(max_size=1000, default_ttl=3600),
            secondary=PersistentCache()
        )
    return _default_cache_manager


def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results using the default cache manager."""
    return get_cache_manager().cache(ttl=ttl, key_func=key_func)