"""
Unit tests for the performance monitoring module.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from collections import deque

from framework.performance.monitor import (
    PerformanceMetric,
    ResourceSnapshot,
    MetricsCollector,
    ResourceTracker,
    PerformanceMonitor,
    get_performance_monitor,
    timer,
    async_timer
)


class TestPerformanceMetric:
    """Test cases for PerformanceMetric dataclass."""
    
    def test_metric_creation(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric(
            name="test_metric",
            value=10.5,
            timestamp=time.time(),
            tags={"env": "test"},
            unit="seconds"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 10.5
        assert metric.tags == {"env": "test"}
        assert metric.unit == "seconds"
    
    def test_metric_defaults(self):
        """Test metric creation with default values."""
        timestamp = time.time()
        metric = PerformanceMetric(
            name="test_metric",
            value=5.0,
            timestamp=timestamp
        )
        
        assert metric.tags == {}
        assert metric.unit == ""


class TestResourceSnapshot:
    """Test cases for ResourceSnapshot dataclass."""
    
    def test_snapshot_creation(self):
        """Test creating a resource snapshot."""
        timestamp = time.time()
        snapshot = ResourceSnapshot(
            timestamp=timestamp,
            cpu_percent=45.2,
            memory_percent=60.1,
            memory_used_mb=1024.0,
            memory_available_mb=2048.0,
            disk_io_read_mb=100.5,
            disk_io_write_mb=50.2,
            network_sent_mb=25.1,
            network_recv_mb=30.4,
            process_count=150,
            load_average=[1.2, 1.5, 1.8]
        )
        
        assert snapshot.timestamp == timestamp
        assert snapshot.cpu_percent == 45.2
        assert snapshot.memory_percent == 60.1
        assert snapshot.load_average == [1.2, 1.5, 1.8]


class TestMetricsCollector:
    """Test cases for MetricsCollector class."""
    
    def test_collector_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector(max_history=500)
        assert collector.max_history == 500
        assert len(collector._metrics) == 0
    
    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()
        collector.record("test_metric", 10.5, tags={"env": "test"}, unit="ms")
        
        latest = collector.get_latest("test_metric")
        assert latest is not None
        assert latest.name == "test_metric"
        assert latest.value == 10.5
        assert latest.tags == {"env": "test"}
        assert latest.unit == "ms"
    
    def test_get_latest_nonexistent(self):
        """Test getting latest metric for non-existent metric."""
        collector = MetricsCollector()
        latest = collector.get_latest("nonexistent")
        assert latest is None
    
    def test_get_history(self):
        """Test getting metric history."""
        collector = MetricsCollector()
        
        # Record multiple metrics
        for i in range(5):
            collector.record("test_metric", float(i))
        
        history = collector.get_history("test_metric")
        assert len(history) == 5
        assert [m.value for m in history] == [0.0, 1.0, 2.0, 3.0, 4.0]
        
        # Test with limit
        limited_history = collector.get_history("test_metric", limit=3)
        assert len(limited_history) == 3
        assert [m.value for m in limited_history] == [2.0, 3.0, 4.0]
    
    def test_get_average(self):
        """Test getting average metric value."""
        collector = MetricsCollector()
        
        # Record metrics with known values
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for value in values:
            collector.record("test_metric", value)
        
        average = collector.get_average("test_metric")
        assert average == 3.0  # (1+2+3+4+5)/5
        
        # Test with duration filter
        time.sleep(0.1)  # Small delay
        collector.record("test_metric", 10.0)
        
        # Average within 1 second should include all values
        recent_avg = collector.get_average("test_metric", duration_seconds=1.0)
        assert recent_avg == (1.0 + 2.0 + 3.0 + 4.0 + 5.0 + 10.0) / 6
    
    def test_get_percentile(self):
        """Test getting percentile metric value."""
        collector = MetricsCollector()
        
        # Record metrics: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        for i in range(1, 11):
            collector.record("test_metric", float(i))
        
        # Test different percentiles
        p50 = collector.get_percentile("test_metric", 50)
        p95 = collector.get_percentile("test_metric", 95)
        p99 = collector.get_percentile("test_metric", 99)
        
        assert p50 == 5.0  # 50th percentile
        assert p95 == 9.0  # 95th percentile 
        assert p99 == 10.0  # 99th percentile
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        collector = MetricsCollector()
        
        collector.record("metric1", 1.0)
        collector.record("metric2", 2.0)
        
        # Clear specific metric
        collector.clear("metric1")
        assert collector.get_latest("metric1") is None
        assert collector.get_latest("metric2") is not None
        
        # Clear all metrics
        collector.clear()
        assert collector.get_latest("metric2") is None
    
    def test_max_history_limit(self):
        """Test that max_history limit is enforced."""
        collector = MetricsCollector(max_history=3)
        
        # Record more metrics than the limit
        for i in range(5):
            collector.record("test_metric", float(i))
        
        history = collector.get_history("test_metric")
        assert len(history) == 3
        assert [m.value for m in history] == [2.0, 3.0, 4.0]


class TestResourceTracker:
    """Test cases for ResourceTracker class."""
    
    @pytest.fixture
    def mock_psutil(self):
        """Mock psutil for testing."""
        with patch('framework.performance.monitor.psutil') as mock:
            # Mock CPU and memory
            mock.cpu_percent.return_value = 45.5
            
            mock_memory = Mock()
            mock_memory.percent = 60.2
            mock_memory.used = 1024 * 1024 * 1024  # 1GB in bytes
            mock_memory.available = 2048 * 1024 * 1024  # 2GB in bytes
            mock.virtual_memory.return_value = mock_memory
            
            # Mock disk I/O
            mock_disk_io = Mock()
            mock_disk_io.read_bytes = 1000000
            mock_disk_io.write_bytes = 500000
            mock.disk_io_counters.return_value = mock_disk_io
            
            # Mock network I/O
            mock_network = Mock()
            mock_network.bytes_sent = 2000000
            mock_network.bytes_recv = 1500000
            mock.net_io_counters.return_value = mock_network
            
            # Mock process count
            mock.pids.return_value = list(range(100))
            
            # Mock load average
            mock.getloadavg.return_value = (1.2, 1.5, 1.8)
            
            yield mock
    
    def test_tracker_initialization(self):
        """Test resource tracker initialization."""
        tracker = ResourceTracker(collection_interval=1.0, max_history=100)
        assert tracker.collection_interval == 1.0
        assert tracker.max_history == 100
        assert not tracker._running
    
    def test_get_resource_snapshot(self, mock_psutil):
        """Test getting a resource snapshot."""
        tracker = ResourceTracker()
        snapshot = tracker._get_resource_snapshot()
        
        assert isinstance(snapshot, ResourceSnapshot)
        assert snapshot.cpu_percent == 45.5
        assert snapshot.memory_percent == 60.2
        assert snapshot.memory_used_mb == 1024.0  # 1GB in MB
        assert snapshot.memory_available_mb == 2048.0  # 2GB in MB
        assert snapshot.process_count == 100
        assert snapshot.load_average == [1.2, 1.5, 1.8]
    
    def test_get_resource_snapshot_error_handling(self):
        """Test error handling in resource snapshot collection."""
        with patch('framework.performance.monitor.psutil.cpu_percent', side_effect=Exception("Test error")):
            tracker = ResourceTracker()
            snapshot = tracker._get_resource_snapshot()
            
            # Should return minimal snapshot on error
            assert snapshot.cpu_percent == 0.0
            assert snapshot.memory_percent == 0.0
    
    @pytest.mark.asyncio
    async def test_start_stop_tracking(self, mock_psutil):
        """Test starting and stopping resource tracking."""
        tracker = ResourceTracker(collection_interval=0.1)
        
        # Start tracking
        await tracker.start()
        assert tracker._running
        assert tracker._task is not None
        
        # Let it collect some data
        await asyncio.sleep(0.2)
        
        # Stop tracking
        await tracker.stop()
        assert not tracker._running
    
    def test_get_latest_snapshot(self, mock_psutil):
        """Test getting the latest snapshot."""
        tracker = ResourceTracker()
        
        # No snapshots initially
        assert tracker.get_latest_snapshot() is None
        
        # Add a snapshot manually
        snapshot = tracker._get_resource_snapshot()
        tracker._snapshots.append(snapshot)
        
        latest = tracker.get_latest_snapshot()
        assert latest is not None
        assert latest.cpu_percent == 45.5
    
    def test_get_snapshots_with_filters(self, mock_psutil):
        """Test getting snapshots with filters."""
        tracker = ResourceTracker()
        
        # Add multiple snapshots
        base_time = time.time()
        for i in range(5):
            snapshot = ResourceSnapshot(
                timestamp=base_time + i,
                cpu_percent=float(i * 10),
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=2000.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                process_count=100
            )
            tracker._snapshots.append(snapshot)
        
        # Test limit filter
        limited = tracker.get_snapshots(limit=3)
        assert len(limited) == 3
        assert [s.cpu_percent for s in limited] == [20.0, 30.0, 40.0]
        
        # Test time filter
        since_time = base_time + 2
        since_filtered = tracker.get_snapshots(since=since_time)
        assert len(since_filtered) == 3
        assert [s.cpu_percent for s in since_filtered] == [20.0, 30.0, 40.0]
    
    def test_get_average_usage(self, mock_psutil):
        """Test getting average resource usage."""
        tracker = ResourceTracker()
        
        # Add test snapshots
        snapshots = [
            ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=float(i * 10),
                memory_percent=float(i * 5),
                memory_used_mb=1000.0 + i * 100,
                memory_available_mb=2000.0,
                disk_io_read_mb=10.0,
                disk_io_write_mb=5.0,
                network_sent_mb=20.0,
                network_recv_mb=15.0,
                process_count=100
            )
            for i in range(5)
        ]
        
        for snapshot in snapshots:
            tracker._snapshots.append(snapshot)
        
        avg_usage = tracker.get_average_usage()
        
        assert avg_usage['cpu_percent'] == 20.0  # (0+10+20+30+40)/5
        assert avg_usage['memory_percent'] == 10.0  # (0+5+10+15+20)/5
        assert avg_usage['memory_used_mb'] == 1200.0  # (1000+1100+1200+1300+1400)/5


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create a performance monitor for testing."""
        return PerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_start_stop_monitor(self, monitor):
        """Test starting and stopping the performance monitor."""
        await monitor.start()
        # Should start resource tracking
        assert monitor.resources._running
        
        await monitor.stop()
        assert not monitor.resources._running
    
    def test_timer_context_manager(self, monitor):
        """Test timer context manager."""
        with monitor.timer("test_operation", tags={"env": "test"}):
            time.sleep(0.1)
        
        # Check that metric was recorded
        latest = monitor.metrics.get_latest("operation_duration_test_operation")
        assert latest is not None
        assert latest.value >= 0.1
        assert latest.tags == {"env": "test"}
        assert latest.unit == "seconds"
    
    def test_timed_decorator(self, monitor):
        """Test timed decorator."""
        @monitor.timed("decorated_function")
        def test_function():
            time.sleep(0.05)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Check that timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_decorated_function")
        assert latest is not None
        assert latest.value >= 0.05
    
    @pytest.mark.asyncio
    async def test_async_timed_decorator(self, monitor):
        """Test async timed decorator."""
        @monitor.async_timed("async_decorated_function")
        async def async_test_function():
            await asyncio.sleep(0.05)
            return "async_result"
        
        result = await async_test_function()
        assert result == "async_result"
        
        # Check that timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_async_decorated_function")
        assert latest is not None
        assert latest.value >= 0.05
    
    def test_record_counter(self, monitor):
        """Test recording counter metrics."""
        monitor.record_counter("test_counter", 5.0, tags={"type": "test"})
        
        latest = monitor.metrics.get_latest("counter_test_counter")
        assert latest is not None
        assert latest.value == 5.0
        assert latest.tags == {"type": "test"}
        assert latest.unit == "count"
    
    def test_record_gauge(self, monitor):
        """Test recording gauge metrics."""
        monitor.record_gauge("test_gauge", 42.5, tags={"metric": "gauge"})
        
        latest = monitor.metrics.get_latest("gauge_test_gauge")
        assert latest is not None
        assert latest.value == 42.5
        assert latest.tags == {"metric": "gauge"}
    
    def test_record_histogram(self, monitor):
        """Test recording histogram metrics."""
        monitor.record_histogram("test_histogram", 100.0, tags={"dist": "normal"})
        
        latest = monitor.metrics.get_latest("histogram_test_histogram")
        assert latest is not None
        assert latest.value == 100.0
        assert latest.tags == {"dist": "normal"}
    
    def test_get_performance_summary(self, monitor):
        """Test getting performance summary."""
        # Record some test metrics
        monitor.record_counter("api_calls", 10)
        monitor.record_gauge("active_connections", 25)
        
        with monitor.timer("test_operation"):
            time.sleep(0.01)
        
        summary = monitor.get_performance_summary(duration_seconds=60)
        
        assert 'timestamp' in summary
        assert 'duration_seconds' in summary
        assert 'resource_usage' in summary
        assert 'operation_metrics' in summary
        assert 'alerts' in summary
        
        # Check that operation metrics include our test operation
        assert 'test_operation' in summary['operation_metrics']
        operation_stats = summary['operation_metrics']['test_operation']
        assert 'count' in operation_stats
        assert 'avg_duration' in operation_stats
        assert operation_stats['count'] == 1
    
    def test_performance_summary_alerts(self, monitor):
        """Test performance summary alert generation."""
        # Mock high resource usage
        with patch.object(monitor.resources, 'get_latest_snapshot') as mock_snapshot:
            mock_snapshot.return_value = ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=85.0,  # High CPU
                memory_percent=90.0,  # High memory
                memory_used_mb=1000.0,
                memory_available_mb=100.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                process_count=100
            )
            
            summary = monitor.get_performance_summary()
            
            # Should have alerts for high CPU and memory
            assert len(summary['alerts']) == 2
            alert_types = [alert['type'] for alert in summary['alerts']]
            assert 'high_cpu' in alert_types
            assert 'high_memory' in alert_types
    
    def test_export_metrics_json(self, monitor):
        """Test exporting metrics in JSON format."""
        # Record some test metrics
        monitor.record_counter("test_counter", 1.0)
        monitor.record_gauge("test_gauge", 42.0)
        
        json_export = monitor.export_metrics(format="json")
        
        assert isinstance(json_export, str)
        # Should be valid JSON
        import json
        data = json.loads(json_export)
        assert isinstance(data, dict)
    
    def test_export_metrics_unsupported_format(self, monitor):
        """Test exporting metrics with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            monitor.export_metrics(format="xml")


class TestGlobalFunctions:
    """Test cases for global utility functions."""
    
    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, PerformanceMonitor)
    
    def test_global_timer_decorator(self):
        """Test global timer decorator."""
        @timer("global_test_operation")
        def test_function():
            time.sleep(0.01)
            return "done"
        
        result = test_function()
        assert result == "done"
        
        # Check that timing was recorded in the global monitor
        global_monitor = get_performance_monitor()
        latest = global_monitor.metrics.get_latest("operation_duration_global_test_operation")
        assert latest is not None
        assert latest.value >= 0.01
    
    @pytest.mark.asyncio
    async def test_global_async_timer_decorator(self):
        """Test global async timer decorator."""
        @async_timer("global_async_test_operation")
        async def async_test_function():
            await asyncio.sleep(0.01)
            return "async_done"
        
        result = await async_test_function()
        assert result == "async_done"
        
        # Check that timing was recorded in the global monitor
        global_monitor = get_performance_monitor()
        latest = global_monitor.metrics.get_latest("operation_duration_global_async_test_operation")
        assert latest is not None
        assert latest.value >= 0.01


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_metrics_collector_performance(self, benchmark):
        """Benchmark metrics collector performance."""
        collector = MetricsCollector()
        
        def record_metrics():
            for i in range(1000):
                collector.record(f"metric_{i % 10}", float(i))
        
        benchmark(record_metrics)
    
    def test_performance_monitor_timer_overhead(self, benchmark):
        """Benchmark performance monitor timer overhead."""
        monitor = PerformanceMonitor()
        
        def timed_operation():
            with monitor.timer("benchmark_operation"):
                pass  # Minimal operation
        
        benchmark(timed_operation)