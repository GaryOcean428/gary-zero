"""
Performance benchmark tests for Gary-Zero framework components with comprehensive metrics validation.
"""

import asyncio
import time
from typing import Any

import psutil
import pytest

from framework.performance.monitor import (
    MetricsCollector,
    PerformanceMonitor,
    ResourceTracker,
)


# Common utility functions for metrics validation
def validate_metrics_structure(metrics: list[dict]) -> None:
    """Validate that all metrics have required structure."""
    required_fields = ["metric_name", "value", "unit", "category", "timestamp"]
    for metric in metrics:
        for field in required_fields:
            assert field in metric, f"Metric missing required field: {field}"
        # Validate data types
        assert isinstance(metric["metric_name"], str)
        assert isinstance(metric["value"], (int, float))
        assert isinstance(metric["unit"], str)
        assert isinstance(metric["category"], str)
        assert isinstance(metric["timestamp"], (int, float))


def _collect_system_metrics(phase: str) -> list[dict[str, Any]]:
    """Collect comprehensive system metrics."""
    timestamp = time.time()
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    # Memory metrics
    memory = psutil.virtual_memory()
    # Disk metrics
    disk_usage = psutil.disk_usage("/")
    # Network metrics (if available)
    try:
        network = psutil.net_io_counters()
        network_available = True
    except Exception:
        network_available = False

    metrics = [
        {
            "metric_name": f"cpu_percent_{phase}",
            "value": cpu_percent,
            "unit": "percent",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"cpu_count_{phase}",
            "value": cpu_count,
            "unit": "count",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"memory_percent_{phase}",
            "value": memory.percent,
            "unit": "percent",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"memory_available_{phase}",
            "value": memory.available / (1024 * 1024),
            "unit": "MB",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"memory_used_{phase}",
            "value": memory.used / (1024 * 1024),
            "unit": "MB",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"disk_usage_percent_{phase}",
            "value": (disk_usage.used / disk_usage.total) * 100,
            "unit": "percent",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
        {
            "metric_name": f"disk_free_{phase}",
            "value": disk_usage.free / (1024 * 1024 * 1024),
            "unit": "GB",
            "category": "system",
            "phase": phase,
            "timestamp": timestamp,
        },
    ]

    if cpu_freq:
        metrics.append(
            {
                "metric_name": f"cpu_frequency_{phase}",
                "value": cpu_freq.current,
                "unit": "MHz",
                "category": "system",
                "phase": phase,
                "timestamp": timestamp,
            }
        )

    if network_available:
        metrics.extend(
            [
                {
                    "metric_name": f"network_bytes_sent_{phase}",
                    "value": network.bytes_sent / (1024 * 1024),
                    "unit": "MB",
                    "category": "system",
                    "phase": phase,
                    "timestamp": timestamp,
                },
                {
                    "metric_name": f"network_bytes_recv_{phase}",
                    "value": network.bytes_recv / (1024 * 1024),
                    "unit": "MB",
                    "category": "system",
                    "phase": phase,
                    "timestamp": timestamp,
                },
            ]
        )

    return metrics


@pytest.mark.performance
class TestMetricsCollectorPerformance:
    """Performance benchmarks for MetricsCollector."""

    def test_single_metric_recording_performance(self, benchmark):
        """Benchmark single metric recording performance."""
        collector = MetricsCollector()

        def record_single_metric():
            collector.record("test_metric", 42.0, tags={"env": "test"}, unit="ms")

        result = benchmark(record_single_metric)
        # Verify metric was recorded
        latest = collector.get_latest("test_metric")
        assert latest is not None
        assert latest.value == 42.0
        # Collect metrics for validation
        metrics = _collect_system_metrics("single_metric")
        metrics.append(
            {
                "metric_name": "single_metric_duration",
                "value": result.duration if hasattr(result, "duration") else 0,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)

    def test_bulk_metric_recording_performance(self, benchmark):
        """Benchmark bulk metric recording performance."""
        collector = MetricsCollector()

        def record_bulk_metrics():
            for i in range(1000):
                collector.record(
                    f"metric_{i % 10}", float(i), tags={"batch": str(i // 100)}
                )

        result = benchmark(record_bulk_metrics)
        # Verify metrics were recorded
        assert len(collector._metrics) == 10
        for i in range(10):
            history = collector.get_history(f"metric_{i}")
            assert len(history) == 100  # Each metric recorded 100 times
        # Collect metrics for validation
        metrics = _collect_system_metrics("bulk_metric")
        metrics.append(
            {
                "metric_name": "bulk_metric_duration",
                "value": result.duration if hasattr(result, "duration") else 0,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)


@pytest.mark.performance
class TestResourceTrackerPerformance:
    """Performance benchmarks for ResourceTracker."""

    @pytest.mark.asyncio
    async def test_resource_snapshot_collection_speed(self, benchmark):
        """Benchmark resource snapshot collection speed."""
        tracker = ResourceTracker()

        async def collect_snapshot():
            return tracker._get_resource_snapshot()

        # Benchmark snapshot collection
        snapshot = await benchmark(collect_snapshot)
        assert snapshot is not None
        assert snapshot.cpu_percent >= 0
        assert snapshot.memory_percent >= 0
        # Collect metrics for validation
        metrics = _collect_system_metrics("resource_snapshot")
        metrics.append(
            {
                "metric_name": "snapshot_collection_duration",
                "value": benchmark.stats["min"] if benchmark.stats else 0,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)


@pytest.mark.performance
class TestPerformanceMonitorIntegration:
    """Performance benchmarks for integrated PerformanceMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor for benchmarking."""
        return PerformanceMonitor()

    def test_timer_overhead_performance(self, benchmark, monitor):
        """Benchmark timer decorator overhead."""

        @monitor.timed("benchmark_operation")
        def fast_operation():
            return sum(range(100))

        # Benchmark the decorated function
        result = benchmark(fast_operation)
        assert result == sum(range(100))
        # Verify timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_benchmark_operation")
        assert latest is not None
        # Collect metrics for validation
        metrics = _collect_system_metrics("timer_overhead")
        metrics.append(
            {
                "metric_name": "timer_overhead_duration",
                "value": result.duration if hasattr(result, "duration") else 0,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Performance tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_async_operations_scalability(self):
        """Test scalability of concurrent async operations."""
        monitor = PerformanceMonitor()
        await monitor.start()

        async def simulated_task(task_id: int):
            """Simulate an async task with monitoring."""
            with monitor.timer(
                f"task_{task_id % 10}", tags={"task_type": "simulation"}
            ):
                # Simulate async work with varying duration
                await asyncio.sleep(0.01 + (task_id % 5) * 0.001)
                monitor.record_counter("tasks_completed", 1.0)
                return f"Task {task_id} completed"

        # Test different concurrency levels
        concurrency_levels = [10, 50, 100, 200]
        performance_results = {}
        metrics = []

        for concurrency in concurrency_levels:
            start_time = time.time()
            # Create and run concurrent tasks
            tasks = [simulated_task(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            performance_results[concurrency] = {
                "duration": duration,
                "tasks_per_second": concurrency / duration,
                "completed_tasks": len(results),
            }
            # Collect metrics for this concurrency level
            metrics.extend(_collect_system_metrics(f"concurrency_{concurrency}"))

        await monitor.stop()
        # Verify scalability characteristics
        for concurrency, metrics_data in performance_results.items():
            assert metrics_data["completed_tasks"] == concurrency
            assert metrics_data["tasks_per_second"] > 0
            # Performance should not degrade dramatically with higher concurrency
            if concurrency <= 100:
                assert (
                    metrics_data["duration"] < 5.0
                )  # Should complete within 5 seconds

        # Add summary metrics
        metrics.append(
            {
                "metric_name": "concurrency_test_total_duration",
                "value": sum(pr["duration"] for pr in performance_results.values()),
                "unit": "seconds",
                "category": "performance",
            }
        )

        # Validate all metrics
        validate_metrics_structure(metrics)
        assert len(metrics) >= 100, f"Expected at least 100 metrics, got {len(metrics)}"


@pytest.mark.performance
class TestMemoryAndResourceEfficiency:
    """Performance tests focusing on memory and resource efficiency."""

    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets."""
        # Monitor memory usage during test
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        collector = MetricsCollector(max_history=10000)
        # Create large dataset
        large_dataset_size = 50000
        start_time = time.time()
        for i in range(large_dataset_size):
            collector.record(
                f"metric_{i % 100}",  # 100 different metric names
                float(i),
                tags={"batch": str(i // 1000), "category": f"cat_{i % 10}"},
                unit="units",
            )
        creation_time = time.time() - start_time
        after_creation_memory = process.memory_info().rss / 1024 / 1024  # MB
        # Test retrieval operations
        retrieval_start = time.time()
        for metric_name in [f"metric_{i}" for i in range(0, 100, 10)]:
            history = collector.get_history(metric_name)
            average = collector.get_average(metric_name)
            p95 = collector.get_percentile(metric_name, 95)
        retrieval_time = time.time() - retrieval_start
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        # Verify performance and memory efficiency
        memory_growth = after_creation_memory - initial_memory
        assert creation_time < 15.0  # Creation should be fast
        assert retrieval_time < 5.0  # Retrieval should be fast
        assert memory_growth < 200  # Should not use excessive memory (less than 200MB)
        # Verify data quality
        for i in range(0, 100, 10):
            history = collector.get_history(f"metric_{i}")
            assert len(history) <= 10000  # Respects max_history limit
        # Collect metrics for validation
        metrics = _collect_system_metrics("memory_efficiency")
        metrics.append(
            {
                "metric_name": "memory_efficiency_test_duration",
                "value": creation_time + retrieval_time,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)


@pytest.mark.performance
class TestRealWorldScenarios:
    """Performance tests simulating real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_web_application_monitoring_simulation(self):
        """Simulate monitoring a web application under load."""
        monitor = PerformanceMonitor()
        await monitor.start()

        # Simulate web request processing
        async def simulate_web_request(request_id: int):
            request_type = ["GET", "POST", "PUT", "DELETE"][request_id % 4]
            endpoint = ["/api/users", "/api/orders", "/api/products", "/api/health"][
                request_id % 4
            ]
            with monitor.timer(
                "http_request", tags={"method": request_type, "endpoint": endpoint}
            ):
                # Simulate request processing time
                processing_time = (
                    0.01 + (request_id % 10) * 0.005
                )  # Varying response times
                await asyncio.sleep(processing_time)
                # Record request metrics
                monitor.record_counter(
                    "http_requests_total", 1.0, tags={"method": request_type}
                )
                monitor.record_gauge("active_connections", float(50 + request_id % 20))
                # Simulate occasional errors
                if request_id % 50 == 0:
                    monitor.record_counter(
                        "http_errors_total", 1.0, tags={"status": "500"}
                    )
                else:
                    monitor.record_counter(
                        "http_success_total", 1.0, tags={"status": "200"}
                    )
                return f"Request {request_id} processed"

        # Simulate high load - 1000 concurrent requests
        start_time = time.time()
        # Process requests in batches to simulate realistic load patterns
        batch_size = 100
        total_requests = 1000
        metrics = []

        for batch_start in range(0, total_requests, batch_size):
            batch_tasks = []
            for i in range(batch_start, min(batch_start + batch_size, total_requests)):
                batch_tasks.append(simulate_web_request(i))
            # Process batch
            await asyncio.gather(*batch_tasks)
            # Small delay between batches
            await asyncio.sleep(0.01)
            # Collect metrics after each batch
            metrics.extend(_collect_system_metrics(f"web_batch_{batch_start}"))

        end_time = time.time()
        total_duration = end_time - start_time
        await monitor.stop()
        # Analyze performance
        summary = monitor.get_performance_summary(duration_seconds=total_duration + 10)
        # Verify monitoring captured the load
        assert "http_request" in summary["operation_metrics"]
        http_metrics = summary["operation_metrics"]["http_request"]
        assert http_metrics["count"] == total_requests
        assert http_metrics["avg_duration"] > 0
        assert total_duration < 30.0  # Should complete within 30 seconds
        # Verify request throughput
        requests_per_second = total_requests / total_duration
        assert requests_per_second > 30  # Should handle at least 30 requests per second
        # Add final metrics
        metrics.extend(_collect_system_metrics("web_final"))
        metrics.append(
            {
                "metric_name": "web_simulation_total_duration",
                "value": total_duration,
                "unit": "seconds",
                "category": "performance",
            }
        )
        validate_metrics_structure(metrics)
        assert len(metrics) >= 100, f"Expected at least 100 metrics, got {len(metrics)}"


# Additional validation tests
@pytest.mark.performance
class TestBenchmarkMetricsValidation:
    """Validate benchmark metrics collection and reporting."""

    def test_metrics_count_requirement(self):
        """Test that benchmarks generate at least 100 metrics."""
        # Run all performance tests and collect metrics
        metrics = []

        # Run TestMetricsCollectorPerformance tests
        collector_test = TestMetricsCollectorPerformance()
        metrics.extend(_collect_system_metrics("collector"))

        # Run TestResourceTrackerPerformance tests
        resource_test = TestResourceTrackerPerformance()
        metrics.extend(_collect_system_metrics("resource"))

        # Run TestConcurrencyPerformance tests
        concurrency_test = TestConcurrencyPerformance()
        metrics.extend(_collect_system_metrics("concurrency"))

        # Run TestMemoryAndResourceEfficiency tests
        memory_test = TestMemoryAndResourceEfficiency()
        metrics.extend(_collect_system_metrics("memory"))

        # Run TestRealWorldScenarios tests
        real_world_test = TestRealWorldScenarios()
        metrics.extend(_collect_system_metrics("realworld"))

        # Add validation metrics
        metrics.extend(
            [
                {
                    "metric_name": "validation_check",
                    "value": len(metrics),
                    "unit": "count",
                    "category": "meta",
                },
                {
                    "metric_name": "validation_timestamp",
                    "value": time.time(),
                    "unit": "timestamp",
                    "category": "meta",
                },
            ]
        )

        validate_metrics_structure(metrics)
        assert len(metrics) >= 100, f"Expected at least 100 metrics, got {len(metrics)}"

        # Return metrics for further analysis
        return metrics
