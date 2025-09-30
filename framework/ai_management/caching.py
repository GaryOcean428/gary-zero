"""Model-specific caching strategies for performance optimization.

This module provides intelligent caching mechanisms for AI model responses,
including:
- Multi-level caching (memory, disk, distributed)
- Semantic similarity-based cache matching
- Dynamic TTL and invalidation strategies
- Cache warming and pre-loading
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategy types."""
    
    EXACT_MATCH = "exact_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    PREFIX_MATCH = "prefix_match"
    FUZZY_MATCH = "fuzzy_match"
    NEVER = "never"


class CacheLevel(str, Enum):
    """Cache level types."""
    
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"


@dataclass
class CacheConfig:
    """Cache configuration."""
    
    strategy: CacheStrategy
    levels: List[CacheLevel]
    ttl_seconds: int = 3600  # 1 hour default
    max_size_mb: int = 100
    similarity_threshold: float = 0.95
    enable_compression: bool = True
    warm_up_enabled: bool = True


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: int = 3600
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def update_access(self):
        """Update access statistics."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size_mb: int = 100):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size_mb = max_size_mb
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from memory cache."""
        entry = self.cache.get(key)
        
        if entry is None:
            self.misses += 1
            return None
        
        if entry.is_expired:
            await self.delete(key)
            self.misses += 1
            return None
        
        entry.update_access()
        self.hits += 1
        return entry
    
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in memory cache."""
        # Check size limits and evict if necessary
        await self._evict_if_needed()
        
        self.cache[key] = entry
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size_estimate_mb': self._estimate_size_mb()
        }
    
    def _estimate_size_mb(self) -> float:
        """Estimate cache size in MB."""
        total_size = 0
        for entry in self.cache.values():
            try:
                total_size += len(pickle.dumps(entry))
            except Exception:
                total_size += 1024  # Rough estimate
        
        return total_size / (1024 * 1024)
    
    async def _evict_if_needed(self):
        """Evict entries if size limit exceeded."""
        if self._estimate_size_mb() > self.max_size_mb:
            # Evict least recently used entries
            entries_by_access = sorted(
                self.cache.items(),
                key=lambda x: x[1].accessed_at
            )
            
            # Evict 20% of entries
            evict_count = max(1, len(entries_by_access) // 5)
            for key, _ in entries_by_access[:evict_count]:
                del self.cache[key]


class DiskCache(CacheBackend):
    """Disk-based cache backend."""
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 1000):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.hits = 0
        self.misses = 0
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from disk cache."""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            self.misses += 1
            return None
        
        try:
            with open(file_path, 'rb') as f:
                entry = pickle.load(f)
            
            if entry.is_expired:
                await self.delete(key)
                self.misses += 1
                return None
            
            entry.update_access()
            
            # Update file access time
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
            
            self.hits += 1
            return entry
            
        except Exception as e:
            logger.error(f"Failed to read cache entry {key}: {e}")
            await self.delete(key)
            self.misses += 1
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in disk cache."""
        file_path = self._get_file_path(key)
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
            
            # Clean up if needed
            await self._cleanup_if_needed()
            return True
            
        except Exception as e:
            logger.error(f"Failed to write cache entry {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from disk cache."""
        file_path = self._get_file_path(key)
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete cache entry {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all entries."""
        try:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink()
            self.hits = 0
            self.misses = 0
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'entries': len(cache_files),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size_mb': total_size / (1024 * 1024)
        }
    
    async def _cleanup_if_needed(self):
        """Clean up disk cache if size limit exceeded."""
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        if total_size > self.max_size_mb * 1024 * 1024:
            # Sort by access time and remove oldest
            files_by_time = sorted(cache_files, key=lambda f: f.stat().st_atime)
            
            # Remove 20% of files
            remove_count = max(1, len(files_by_time) // 5)
            for file_path in files_by_time[:remove_count]:
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove cache file {file_path}: {e}")


class DistributedCache(CacheBackend):
    """Redis-based distributed cache backend for AI model responses."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 1, password: Optional[str] = None,
                 key_prefix: str = "ai_cache:", ttl_seconds: int = 3600):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl = ttl_seconds
        
        # Connection pool for better performance
        self._pool = None
        self._use_fallback = False
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        # Initialize Redis connection
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with fallback."""
        try:
            import redis.asyncio as redis
            
            self._pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                encoding='utf-8',
                decode_responses=False,  # Keep binary for pickle
                max_connections=20
            )
            
            logger.info(f"Distributed cache initialized - Redis {self.host}:{self.port}")
            
        except ImportError:
            logger.warning("Redis library not available, distributed cache disabled")
            self._use_fallback = True
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self._use_fallback = True
    
    async def _get_redis_client(self):
        """Get Redis client with connection pooling."""
        if self._use_fallback:
            return None
        
        try:
            import redis.asyncio as redis
            return redis.Redis(connection_pool=self._pool)
        except Exception as e:
            logger.error(f"Failed to get Redis client: {e}")
            self._use_fallback = True
            return None
    
    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix."""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from distributed cache."""
        if self._use_fallback:
            return None
        
        client = await self._get_redis_client()
        if not client:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = await client.get(redis_key)
            
            if data is None:
                self.misses += 1
                return None
            
            # Deserialize the cache entry
            entry = pickle.loads(data)
            
            # Check if expired
            if entry.is_expired():
                await client.delete(redis_key)
                self.misses += 1
                return None
            
            self.hits += 1
            return entry
            
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.misses += 1
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in distributed cache."""
        if self._use_fallback:
            return False
        
        client = await self._get_redis_client()
        if not client:
            return False
        
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(entry)
            
            # Use TTL from entry or default
            ttl = self.default_ttl
            if entry.ttl and entry.ttl > 0:
                ttl = int(entry.ttl)
            
            await client.setex(redis_key, ttl, data)
            return True
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from distributed cache."""
        if self._use_fallback:
            return False
        
        client = await self._get_redis_client()
        if not client:
            return False
        
        try:
            redis_key = self._make_key(key)
            result = await client.delete(redis_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all entries with our prefix."""
        if self._use_fallback:
            return False
        
        client = await self._get_redis_client()
        if not client:
            return False
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = await client.keys(pattern)
            
            if keys:
                await client.delete(*keys)
            
            self.hits = 0
            self.misses = 0
            return True
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self._use_fallback:
            return {
                'backend': 'distributed_redis',
                'status': 'fallback_mode',
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0
            }
        
        client = await self._get_redis_client()
        if not client:
            return {'backend': 'distributed_redis', 'status': 'unavailable'}
        
        try:
            # Get Redis info
            info = await client.info('memory')
            pattern = f"{self.key_prefix}*"
            keys = await client.keys(pattern)
            
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'backend': 'distributed_redis',
                'status': 'active',
                'entries': len(keys),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'redis_memory_used_mb': info.get('used_memory', 0) / 1024 / 1024,
                'redis_connected_clients': info.get('connected_clients', 0)
            }
            
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {'backend': 'distributed_redis', 'status': 'error', 'error': str(e)}


class ModelCacheManager:
    """Manages model-specific caching with multiple strategies."""
    
    def __init__(self, config: CacheConfig, cache_dir: Optional[Path] = None):
        self.config = config
        self.cache_dir = cache_dir or Path("model_cache")
        
        # Initialize cache backends
        self.backends: Dict[CacheLevel, CacheBackend] = {}
        
        if CacheLevel.MEMORY in config.levels:
            self.backends[CacheLevel.MEMORY] = MemoryCache(config.max_size_mb)
        
        if CacheLevel.DISK in config.levels:
            self.backends[CacheLevel.DISK] = DiskCache(
                self.cache_dir, config.max_size_mb * 2
            )
        
        # Add distributed cache backend (Redis)
        if CacheLevel.DISTRIBUTED in config.levels:
            redis_config = getattr(config, 'redis_config', {})
            self.backends[CacheLevel.DISTRIBUTED] = DistributedCache(**redis_config)
        
        self.warm_up_cache = {}
        if config.warm_up_enabled:
            self._load_warm_up_cache()
    
    def _load_warm_up_cache(self):
        """Load warm-up cache entries."""
        warm_up_file = self.cache_dir / "warm_up.json"
        if warm_up_file.exists():
            try:
                with open(warm_up_file, 'r') as f:
                    self.warm_up_cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load warm-up cache: {e}")
    
    def _save_warm_up_cache(self):
        """Save warm-up cache entries."""
        if not self.config.warm_up_enabled:
            return
        
        warm_up_file = self.cache_dir / "warm_up.json"
        try:
            self.cache_dir.mkdir(exist_ok=True)
            with open(warm_up_file, 'w') as f:
                json.dump(self.warm_up_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save warm-up cache: {e}")
    
    def _generate_cache_key(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate cache key for request."""
        key_data = {
            'model': model_name,
            'prompt': prompt,
            'parameters': parameters
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def get_cached_response(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached response if available."""
        if self.config.strategy == CacheStrategy.NEVER:
            return None
        
        cache_key = self._generate_cache_key(model_name, prompt, parameters)
        
        # Try each cache level in order
        for level in self.config.levels:
            backend = self.backends.get(level)
            if backend:
                entry = await backend.get(cache_key)
                if entry:
                    logger.debug(f"Cache hit for {model_name} at level {level.value}")
                    
                    # Propagate to higher levels
                    await self._propagate_to_upper_levels(level, cache_key, entry)
                    
                    return entry.value
        
        # Check semantic similarity if enabled
        if self.config.strategy == CacheStrategy.SEMANTIC_SIMILARITY:
            similar_response = await self._find_similar_cached_response(
                model_name, prompt, parameters
            )
            if similar_response:
                return similar_response
        
        logger.debug(f"Cache miss for {model_name}")
        return None
    
    async def cache_response(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any],
        response: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Cache a model response."""
        if self.config.strategy == CacheStrategy.NEVER:
            return False
        
        cache_key = self._generate_cache_key(model_name, prompt, parameters)
        
        entry = CacheEntry(
            key=cache_key,
            value=response,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            ttl_seconds=ttl_seconds or self.config.ttl_seconds,
            metadata={
                'model_name': model_name,
                'prompt_length': len(prompt),
                'parameters': parameters
            }
        )
        
        # Store in all configured levels
        success = True
        for level in self.config.levels:
            backend = self.backends.get(level)
            if backend:
                level_success = await backend.set(cache_key, entry)
                success = success and level_success
        
        # Add to warm-up cache if frequently accessed
        if self.config.warm_up_enabled:
            self._maybe_add_to_warm_up(cache_key, model_name, prompt, parameters)
        
        return success
    
    async def _propagate_to_upper_levels(
        self,
        found_level: CacheLevel,
        cache_key: str,
        entry: CacheEntry
    ):
        """Propagate cache entry to upper levels."""
        level_order = [CacheLevel.MEMORY, CacheLevel.DISK, CacheLevel.DISTRIBUTED]
        found_index = level_order.index(found_level)
        
        # Propagate to levels above the one where we found the entry
        for i in range(found_index):
            level = level_order[i]
            if level in self.config.levels and level in self.backends:
                await self.backends[level].set(cache_key, entry)
    
    async def _find_similar_cached_response(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """Find semantically similar cached response."""
        # This is a simplified implementation
        # In practice, you'd use embedding similarity
        
        # For now, just check for prefix matches
        if self.config.strategy == CacheStrategy.PREFIX_MATCH:
            return await self._find_prefix_match(model_name, prompt, parameters)
        
        return None
    
    async def _find_prefix_match(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """Find cache entry with matching prompt prefix."""
        # Check memory cache for prefix matches
        memory_backend = self.backends.get(CacheLevel.MEMORY)
        if isinstance(memory_backend, MemoryCache):
            for entry in memory_backend.cache.values():
                if (
                    entry.metadata.get('model_name') == model_name and
                    not entry.is_expired and
                    prompt.startswith(entry.metadata.get('original_prompt', '')[:50])
                ):
                    return entry.value
        
        return None
    
    def _maybe_add_to_warm_up(
        self,
        cache_key: str,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ):
        """Maybe add entry to warm-up cache."""
        # Track access frequency
        if cache_key not in self.warm_up_cache:
            self.warm_up_cache[cache_key] = {
                'model_name': model_name,
                'prompt': prompt[:100],  # Store truncated prompt
                'parameters': parameters,
                'access_count': 1
            }
        else:
            self.warm_up_cache[cache_key]['access_count'] += 1
        
        # Periodically save warm-up cache
        if len(self.warm_up_cache) % 100 == 0:
            self._save_warm_up_cache()
    
    async def warm_up_models(self, model_names: List[str]):
        """Pre-load frequently used model responses."""
        if not self.config.warm_up_enabled:
            return
        
        # Identify frequently accessed prompts for each model
        for cache_key, entry_data in self.warm_up_cache.items():
            if (
                entry_data['model_name'] in model_names and
                entry_data['access_count'] >= 5  # Threshold for warm-up
            ):
                # Check if already cached
                cached = await self.get_cached_response(
                    entry_data['model_name'],
                    entry_data['prompt'],
                    entry_data['parameters']
                )
                
                if not cached:
                    logger.info(f"Would warm up cache for {entry_data['model_name']}")
                    # In practice, you'd make actual model calls here
    
    async def invalidate_model_cache(self, model_name: str) -> bool:
        """Invalidate all cache entries for a specific model."""
        success = True
        
        for backend in self.backends.values():
            if isinstance(backend, MemoryCache):
                # Remove entries for this model
                keys_to_remove = [
                    key for key, entry in backend.cache.items()
                    if entry.metadata.get('model_name') == model_name
                ]
                for key in keys_to_remove:
                    await backend.delete(key)
            
            elif isinstance(backend, DiskCache):
                # More complex for disk cache - would need to load and check
                # For now, just log
                logger.info(f"Model {model_name} cache invalidation requested")
        
        # Clean warm-up cache
        self.warm_up_cache = {
            k: v for k, v in self.warm_up_cache.items()
            if v.get('model_name') != model_name
        }
        self._save_warm_up_cache()
        
        return success
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'config': {
                'strategy': self.config.strategy.value,
                'levels': [level.value for level in self.config.levels],
                'ttl_seconds': self.config.ttl_seconds,
                'max_size_mb': self.config.max_size_mb
            },
            'levels': {}
        }
        
        for level, backend in self.backends.items():
            stats['levels'][level.value] = await backend.get_stats()
        
        # Warm-up cache stats
        if self.config.warm_up_enabled:
            stats['warm_up'] = {
                'entries': len(self.warm_up_cache),
                'top_models': self._get_top_warm_up_models()
            }
        
        return stats
    
    def _get_top_warm_up_models(self) -> List[Dict[str, Any]]:
        """Get top models by warm-up cache access count."""
        model_counts = {}
        for entry_data in self.warm_up_cache.values():
            model = entry_data['model_name']
            if model not in model_counts:
                model_counts[model] = 0
            model_counts[model] += entry_data['access_count']
        
        return [
            {'model': model, 'access_count': count}
            for model, count in sorted(
                model_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
    
    async def clear_all_caches(self) -> bool:
        """Clear all cache levels."""
        success = True
        for backend in self.backends.values():
            level_success = await backend.clear()
            success = success and level_success
        
        # Clear warm-up cache
        self.warm_up_cache.clear()
        self._save_warm_up_cache()
        
        return success