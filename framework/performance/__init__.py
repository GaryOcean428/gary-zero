"""
Performance optimization framework for Gary-Zero.

This module provides comprehensive performance optimization tools including:
- Multi-tier caching system
- Async utilities and patterns  
- Performance monitoring and metrics
- Resource optimization utilities
"""

from .cache import CacheManager, CacheBackend, MemoryCache, PersistentCache
from .async_utils import AsyncPool, BackgroundTaskManager, AsyncContextManager
from .monitor import PerformanceMonitor, MetricsCollector, ResourceTracker
from .optimizer import ResourceOptimizer, MemoryOptimizer, CPUOptimizer

__all__ = [
    # Caching
    'CacheManager',
    'CacheBackend', 
    'MemoryCache',
    'PersistentCache',
    
    # Async utilities
    'AsyncPool',
    'BackgroundTaskManager',
    'AsyncContextManager',
    
    # Monitoring
    'PerformanceMonitor',
    'MetricsCollector',
    'ResourceTracker',
    
    # Optimization
    'ResourceOptimizer',
    'MemoryOptimizer',
    'CPUOptimizer',
]

__version__ = "1.0.0"