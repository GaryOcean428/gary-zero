"""
Performance optimization framework for Gary-Zero.

This module provides comprehensive performance optimization tools including:
- Multi-tier caching system
- Async utilities and patterns  
- Performance monitoring and metrics
- Resource optimization utilities
"""

from .async_utils import AsyncContextManager, AsyncPool, BackgroundTaskManager
from .cache import CacheBackend, CacheManager, MemoryCache, PersistentCache, cached
from .monitor import MetricsCollector, PerformanceMonitor, ResourceTracker, async_timer, timer
from .optimizer import (
    CPUOptimizer,
    MemoryOptimizer,
    ResourceOptimizer,
    auto_optimize,
    cpu_optimize,
    memory_optimize,
)

__all__ = [
    # Caching
    'CacheManager',
    'CacheBackend',
    'MemoryCache',
    'PersistentCache',
    'cached',

    # Async utilities
    'AsyncPool',
    'BackgroundTaskManager',
    'AsyncContextManager',

    # Monitoring
    'PerformanceMonitor',
    'MetricsCollector',
    'ResourceTracker',
    'timer',
    'async_timer',

    # Optimization
    'ResourceOptimizer',
    'MemoryOptimizer',
    'CPUOptimizer',
    'memory_optimize',
    'cpu_optimize',
    'auto_optimize',
]

__version__ = "1.0.0"
