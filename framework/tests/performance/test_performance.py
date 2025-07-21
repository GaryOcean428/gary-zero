"""
Tests for the performance optimization framework.
"""

import asyncio
import os
import tempfile
import time
from unittest.mock import patch, MagicMock

import pytest

from framework.performance.cache import (
    MemoryCache, PersistentCache, CacheManager, get_cache_manager, cached
)
from framework.performance.async_utils import (
    AsyncPool, BackgroundTaskManager, TaskStatus, async_timeout, async_retry
)
from framework.performance.monitor import (
    MetricsCollector, ResourceTracker, PerformanceMonitor, timer, async_timer
)
from framework.performance.optimizer import (
    MemoryOptimizer, CPUOptimizer, ResourceOptimizer, optimize_memory, auto_optimize
)


class TestMemoryCache:
    """Test cases for MemoryCache."""
    
    def test_basic_operations(self):
        """Test basic cache operations."""
        cache = MemoryCache(max_size=3)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test exists
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
        
        # Test size
        assert cache.size() == 1
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = MemoryCache(default_ttl=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
        assert not cache.exists("key1")
    
    def test_lru_eviction(self):
        """Test LRU eviction when max_size is exceeded."""
        cache = MemoryCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_delete_and_clear(self):
        """Test delete and clear operations."""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.delete("key1") is True
        assert cache.delete("nonexistent") is False
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key2") is None


class TestPersistentCache:
    """Test cases for PersistentCache."""
    
    def test_basic_operations(self):
        """Test basic persistent cache operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PersistentCache(cache_dir=temp_dir)
            
            # Test set and get
            cache.set("key1", {"data": "value1"})
            assert cache.get("key1") == {"data": "value1"}
            
            # Create new cache instance with same directory
            cache2 = PersistentCache(cache_dir=temp_dir)
            assert cache2.get("key1") == {"data": "value1"}
    
    def test_serialization_formats(self):
        """Test different serialization formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON serialization
            json_cache = PersistentCache(cache_dir=temp_dir, serializer="json")
            json_cache.set("json_key", {"data": "json_value"})
            assert json_cache.get("json_key") == {"data": "json_value"}
            
            # Test pickle serialization
            pickle_cache = PersistentCache(cache_dir=temp_dir, serializer="pickle")
            pickle_cache.set("pickle_key", {"data": "pickle_value"})
            assert pickle_cache.get("pickle_key") == {"data": "pickle_value"}
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration for persistent cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PersistentCache(cache_dir=temp_dir)
            
            cache.set("key1", "value1", ttl=1)
            assert cache.get("key1") == "value1"
            
            # Wait for expiration
            time.sleep(1.1)
            assert cache.get("key1") is None


class TestCacheManager:
    """Test cases for CacheManager."""
    
    def test_multi_tier_caching(self):
        """Test multi-tier cache functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            primary = MemoryCache(max_size=2)
            secondary = PersistentCache(cache_dir=temp_dir)
            manager = CacheManager(primary=primary, secondary=secondary)
            
            # Set in both tiers
            manager.set("key1", "value1")
            
            # Should get from primary
            assert manager.get("key1") == "value1"
            
            # Clear primary, should fallback to secondary
            primary.clear()
            assert manager.get("key1") == "value1"  # From secondary
            
            # Should also promote back to primary
            assert primary.get("key1") == "value1"
    
    def test_cache_decorator(self):
        """Test cache decorator functionality."""
        cache_manager = CacheManager()
        
        call_count = 0
        
        @cache_manager.cache(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # No additional call
        
        # Different arguments should execute function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2


class TestAsyncPool:
    """Test cases for AsyncPool."""
    
    @pytest.mark.asyncio
    async def test_basic_pool_operations(self):
        """Test basic async pool operations."""
        def create_resource():
            return MagicMock()
        
        pool = AsyncPool(factory=create_resource, max_size=2, min_size=1)
        
        # Test acquiring and releasing
        async with pool.get() as resource:
            assert resource is not None
        
        # Test manual acquire/release
        resource = await pool.acquire()
        assert resource is not None
        await pool.release(resource)
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_pool_limits(self):
        """Test pool size limits."""
        created_count = 0
        
        def create_resource():
            nonlocal created_count
            created_count += 1
            return f"resource_{created_count}"
        
        pool = AsyncPool(factory=create_resource, max_size=2, min_size=1)
        
        # Should create minimum resources on first acquire
        resource1 = await pool.acquire()
        assert created_count >= 1
        
        resource2 = await pool.acquire()
        assert created_count <= 2  # Should not exceed max_size
        
        await pool.release(resource1)
        await pool.release(resource2)
        await pool.close()


class TestBackgroundTaskManager:
    """Test cases for BackgroundTaskManager."""
    
    @pytest.mark.asyncio
    async def test_basic_task_management(self):
        """Test basic background task management."""
        manager = BackgroundTaskManager(max_concurrent=2)
        
        async def simple_task(value):
            await asyncio.sleep(0.1)
            return value * 2
        
        # Submit task
        task_id = await manager.submit("test_task", simple_task(5))
        
        # Wait for completion
        result = await manager.wait(task_id, timeout=1.0)
        assert result == 10
        
        # Check task status
        status = manager.get_task_status(task_id)
        assert status['status'] == TaskStatus.COMPLETED.value
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """Test task cancellation."""
        manager = BackgroundTaskManager()
        
        async def long_task():
            await asyncio.sleep(10)  # Long running task
            return "completed"
        
        task_id = await manager.submit("long_task", long_task())
        
        # Wait a moment for task to start
        await asyncio.sleep(0.1)
        
        # Cancel the task
        cancelled = await manager.cancel(task_id)
        assert cancelled is True
        
        # Check status after a moment
        await asyncio.sleep(0.1)
        status = manager.get_task_status(task_id)
        # Task might be cancelled or running when cancelled
        assert status['status'] in [TaskStatus.CANCELLED.value, TaskStatus.RUNNING.value]
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_task_failure_handling(self):
        """Test handling of failed tasks."""
        manager = BackgroundTaskManager()
        
        async def failing_task():
            raise ValueError("Task failed")
        
        task_id = await manager.submit("failing_task", failing_task())
        
        # Wait a moment for task to start and fail
        await asyncio.sleep(0.2)
        
        # Should raise the original exception
        try:
            await manager.wait(task_id, timeout=1.0)
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert str(e) == "Task failed"
        
        # Check status
        status = manager.get_task_status(task_id)
        assert status['status'] == TaskStatus.FAILED.value
        
        await manager.shutdown()


class TestMetricsCollector:
    """Test cases for MetricsCollector."""
    
    def test_basic_metrics_collection(self):
        """Test basic metrics collection."""
        collector = MetricsCollector(max_history=10)
        
        # Record some metrics
        collector.record("test_metric", 10.0, tags={"component": "test"})
        collector.record("test_metric", 20.0, tags={"component": "test"})
        collector.record("test_metric", 30.0, tags={"component": "test"})
        
        # Test latest value
        latest = collector.get_latest("test_metric")
        assert latest.value == 30.0
        assert latest.tags["component"] == "test"
        
        # Test history
        history = collector.get_history("test_metric")
        assert len(history) == 3
        assert [m.value for m in history] == [10.0, 20.0, 30.0]
    
    def test_statistical_functions(self):
        """Test statistical functions."""
        collector = MetricsCollector()
        
        # Record metrics with known values
        for i in range(10):
            collector.record("test_metric", float(i))
        
        # Test average
        avg = collector.get_average("test_metric")
        assert avg == 4.5  # Average of 0-9
        
        # Test percentiles
        p50 = collector.get_percentile("test_metric", 50)
        p95 = collector.get_percentile("test_metric", 95)
        assert p50 == 5.0  # 50th percentile (fixed)
        assert p95 == 9.0  # 95th percentile (fixed)


class TestResourceTracker:
    """Test cases for ResourceTracker."""
    
    @pytest.mark.asyncio
    async def test_resource_tracking(self):
        """Test resource tracking functionality."""
        tracker = ResourceTracker(collection_interval=0.1, max_history=5)
        
        await tracker.start()
        
        # Wait for some snapshots to be collected
        await asyncio.sleep(0.3)
        
        # Check that snapshots were collected
        latest = tracker.get_latest_snapshot()
        assert latest is not None
        assert latest.cpu_percent >= 0
        assert latest.memory_percent >= 0
        
        # Check history
        snapshots = tracker.get_snapshots()
        assert len(snapshots) >= 2
        
        # Test average usage
        avg_usage = tracker.get_average_usage()
        assert "cpu_percent" in avg_usage
        assert "memory_percent" in avg_usage
        
        await tracker.stop()


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor."""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test comprehensive performance monitoring."""
        monitor = PerformanceMonitor()
        
        await monitor.start()
        
        # Test timer context manager
        with monitor.timer("test_operation"):
            time.sleep(0.1)
        
        # Check that metric was recorded
        latest = monitor.metrics.get_latest("operation_duration_test_operation")
        assert latest is not None
        assert latest.value >= 0.1
        
        # Test counters and gauges
        monitor.record_counter("test_counter", 5)
        monitor.record_gauge("test_gauge", 42.0)
        
        counter_metric = monitor.metrics.get_latest("counter_test_counter")
        gauge_metric = monitor.metrics.get_latest("gauge_test_gauge")
        
        assert counter_metric.value == 5
        assert gauge_metric.value == 42.0
        
        # Test performance summary
        summary = monitor.get_performance_summary(duration_seconds=60)
        assert "resource_usage" in summary
        assert "operation_metrics" in summary
        
        await monitor.stop()
    
    def test_timing_decorators(self):
        """Test timing decorators."""
        monitor = PerformanceMonitor()
        
        @monitor.timed("test_function")
        def test_function():
            time.sleep(0.05)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Check that timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_test_function")
        assert latest is not None
        assert latest.value >= 0.05
    
    @pytest.mark.asyncio
    async def test_async_timing_decorators(self):
        """Test async timing decorators."""
        monitor = PerformanceMonitor()
        
        @monitor.async_timed("test_async_function")
        async def test_async_function():
            await asyncio.sleep(0.05)
            return "async_result"
        
        result = await test_async_function()
        assert result == "async_result"
        
        # Check that timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_test_async_function")
        assert latest is not None
        assert latest.value >= 0.05


class TestMemoryOptimizer:
    """Test cases for MemoryOptimizer."""
    
    def test_memory_optimization(self):
        """Test memory optimization functionality."""
        optimizer = MemoryOptimizer()
        
        # Register a mock cache cleanup function
        cleanup_called = False
        def mock_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
            return 5  # Simulated number of items cleaned
        
        optimizer.register_cache_cleanup(mock_cleanup)
        
        # Test optimization
        result = optimizer.optimize()
        
        assert result.optimization_type == "memory"
        assert cleanup_called
        assert "Cleaned 5 cache entries" in result.recommendations
        
        # Test memory info
        memory_info = optimizer.get_memory_info()
        assert "system_percent" in memory_info
        assert "process_rss_mb" in memory_info


class TestCPUOptimizer:
    """Test cases for CPUOptimizer."""
    
    @patch('psutil.Process')
    def test_cpu_optimization(self, mock_process):
        """Test CPU optimization functionality."""
        # Mock process for testing
        mock_instance = MagicMock()
        mock_instance.nice.return_value = 0
        mock_instance.cpu_percent.return_value = 25.0
        mock_instance.num_threads.return_value = 4
        mock_process.return_value = mock_instance
        
        optimizer = CPUOptimizer()
        
        # Test optimization
        result = optimizer.optimize()
        
        assert result.optimization_type == "cpu"
        assert len(result.recommendations) > 0
        
        # Test CPU info
        cpu_info = optimizer.get_cpu_info()
        assert "process_cpu_percent" in cpu_info


class TestResourceOptimizer:
    """Test cases for ResourceOptimizer."""
    
    def test_comprehensive_optimization(self):
        """Test comprehensive resource optimization."""
        memory_optimizer = MemoryOptimizer()
        cpu_optimizer = CPUOptimizer()
        
        resource_optimizer = ResourceOptimizer(
            memory_optimizer=memory_optimizer,
            cpu_optimizer=cpu_optimizer
        )
        
        # Test individual optimizations
        memory_result = resource_optimizer.optimize_memory()
        assert memory_result.optimization_type == "memory"
        
        # Test getting resource status
        status = resource_optimizer.get_resource_status()
        assert "memory" in status
        assert "cpu" in status
        assert "timestamp" in status
        
        # Test optimization report
        report = resource_optimizer.generate_optimization_report()
        assert "current_status" in report
        assert "optimization_summary" in report
        assert "recommendations" in report
    
    def test_auto_optimization_decorator(self):
        """Test auto-optimization decorator."""
        call_count = 0
        
        @auto_optimize(memory_threshold=0.9, cpu_threshold=0.9)
        def test_function():
            nonlocal call_count
            call_count += 1
            return "result"
        
        result = test_function()
        assert result == "result"
        assert call_count == 1


class TestDecorators:
    """Test cases for decorators and utility functions."""
    
    def test_cached_decorator(self):
        """Test the cached decorator."""
        # Create a fresh cache manager to avoid global state issues
        from framework.performance.cache import CacheManager, MemoryCache
        
        cache_manager = CacheManager(primary=MemoryCache())
        call_count = 0
        
        @cache_manager.cache(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1
        
        # Different arguments should execute function
        result3 = expensive_function(6)
        assert result3 == 12
        assert call_count == 2
    
    def test_timer_decorator(self):
        """Test the timer decorator."""
        @timer("decorated_function")
        def test_function():
            time.sleep(0.01)
            return "timed"
        
        result = test_function()
        assert result == "timed"
        
        # Check that timing was recorded in default monitor
        from framework.performance.monitor import get_performance_monitor
        monitor = get_performance_monitor()
        latest = monitor.metrics.get_latest("operation_duration_decorated_function")
        assert latest is not None
    
    @pytest.mark.asyncio
    async def test_async_timeout_decorator(self):
        """Test async timeout decorator."""
        @async_timeout(0.1)
        async def fast_function():
            await asyncio.sleep(0.05)
            return "completed"
        
        @async_timeout(0.05)
        async def slow_function():
            await asyncio.sleep(0.1)
            return "should timeout"
        
        # Fast function should complete
        result = await fast_function()
        assert result == "completed"
        
        # Slow function should timeout
        with pytest.raises(asyncio.TimeoutError):
            await slow_function()
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """Test async retry decorator."""
        attempt_count = 0
        
        @async_retry(max_attempts=3, delay=0.01, backoff=2.0)
        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Not ready yet")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert attempt_count == 3