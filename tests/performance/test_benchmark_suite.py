"""
Performance benchmark tests for Gary-Zero framework components.
"""

import asyncio
import pytest
import time
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import json
import tempfile
import os

from framework.performance.monitor import (
    PerformanceMonitor,
    MetricsCollector,
    ResourceTracker,
    PerformanceMetric
)


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
    
    def test_bulk_metric_recording_performance(self, benchmark):
        """Benchmark bulk metric recording performance."""
        collector = MetricsCollector()
        
        def record_bulk_metrics():
            for i in range(1000):
                collector.record(f"metric_{i % 10}", float(i), tags={"batch": str(i // 100)})
        
        result = benchmark(record_bulk_metrics)
        
        # Verify metrics were recorded
        assert len(collector._metrics) == 10
        for i in range(10):
            history = collector.get_history(f"metric_{i}")
            assert len(history) == 100  # Each metric recorded 100 times
    
    def test_concurrent_metric_recording_performance(self, benchmark):
        """Benchmark concurrent metric recording performance."""
        collector = MetricsCollector()
        
        def concurrent_recording():
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for thread_id in range(4):
                    def record_metrics(tid=thread_id):
                        for i in range(250):  # 250 * 4 = 1000 total
                            collector.record(
                                f"concurrent_metric_{tid}",
                                float(i),
                                tags={"thread": str(tid)}
                            )
                    
                    futures.append(executor.submit(record_metrics))
                
                # Wait for all threads to complete
                for future in futures:
                    future.result()
        
        result = benchmark(concurrent_recording)
        
        # Verify all metrics were recorded safely
        assert len(collector._metrics) == 4
        for thread_id in range(4):
            history = collector.get_history(f"concurrent_metric_{thread_id}")
            assert len(history) == 250
    
    def test_metric_retrieval_performance(self, benchmark):
        """Benchmark metric retrieval performance."""
        collector = MetricsCollector()
        
        # Pre-populate with metrics
        for i in range(10000):
            collector.record("performance_metric", float(i))
        
        def retrieve_metrics():
            # Test various retrieval operations
            latest = collector.get_latest("performance_metric")
            history = collector.get_history("performance_metric", limit=1000)
            average = collector.get_average("performance_metric")
            p95 = collector.get_percentile("performance_metric", 95)
            return latest, len(history), average, p95
        
        result = benchmark(retrieve_metrics)
        latest, history_len, average, p95 = result
        
        assert latest is not None
        assert history_len == 1000
        assert average is not None
        assert p95 is not None
    
    def test_memory_usage_with_large_dataset(self):
        """Test memory usage with large metric datasets."""
        collector = MetricsCollector(max_history=50000)
        
        # Measure initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Record large number of metrics
        start_time = time.time()
        for i in range(50000):
            collector.record("memory_test_metric", float(i), tags={"batch": str(i // 1000)})
        recording_time = time.time() - start_time
        
        # Measure memory after recording
        after_recording_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_recording_memory - initial_memory
        
        # Verify performance constraints
        assert recording_time < 10.0  # Should complete within 10 seconds
        assert memory_increase < 100  # Should use less than 100MB additional memory
        
        # Verify data integrity
        history = collector.get_history("memory_test_metric")
        assert len(history) == 50000
        assert history[-1].value == 49999.0


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
    
    @pytest.mark.asyncio
    async def test_continuous_monitoring_performance(self):
        """Test performance of continuous resource monitoring."""
        tracker = ResourceTracker(collection_interval=0.1)  # Very fast collection
        
        start_time = time.time()
        await tracker.start()
        
        # Let it collect for 2 seconds
        await asyncio.sleep(2.0)
        
        await tracker.stop()
        end_time = time.time()
        
        # Verify collection efficiency
        snapshots = tracker.get_snapshots()
        collection_duration = end_time - start_time
        
        # Should have collected approximately 20 snapshots (2s / 0.1s interval)
        assert len(snapshots) >= 15  # Allow some tolerance
        assert len(snapshots) <= 25
        
        # CPU usage should be reasonable
        if snapshots:
            avg_cpu = sum(s.cpu_percent for s in snapshots) / len(snapshots)
            # Monitoring itself shouldn't cause high CPU usage
            assert avg_cpu < 50.0  # Less than 50% average CPU during monitoring
    
    @pytest.mark.asyncio
    async def test_snapshot_retrieval_performance(self, benchmark):
        """Benchmark snapshot retrieval performance."""
        tracker = ResourceTracker()
        
        # Pre-populate with snapshots
        for i in range(1000):
            snapshot = tracker._get_resource_snapshot()
            tracker._snapshots.append(snapshot)
        
        def retrieve_snapshots():
            # Test various retrieval operations
            latest = tracker.get_latest_snapshot()
            recent_100 = tracker.get_snapshots(limit=100)
            since_now = tracker.get_snapshots(since=time.time() - 60)
            avg_usage = tracker.get_average_usage(60.0)
            return latest, len(recent_100), len(since_now), avg_usage
        
        result = benchmark(retrieve_snapshots)
        latest, recent_count, since_count, avg_usage = result
        
        assert latest is not None
        assert recent_count == 100
        assert isinstance(avg_usage, dict)


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
    
    @pytest.mark.asyncio
    async def test_async_timer_overhead_performance(self, benchmark, monitor):
        """Benchmark async timer decorator overhead."""
        @monitor.async_timed("async_benchmark_operation")
        async def async_fast_operation():
            await asyncio.sleep(0.001)  # Very small delay
            return sum(range(100))
        
        async def run_async_benchmark():
            return await async_fast_operation()
        
        # Benchmark the async decorated function
        result = await run_async_benchmark()
        
        assert result == sum(range(100))
        
        # Verify timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_async_benchmark_operation")
        assert latest is not None
    
    def test_context_manager_overhead_performance(self, benchmark, monitor):
        """Benchmark context manager timer overhead."""
        def operation_with_timer():
            with monitor.timer("context_benchmark"):
                return sum(range(1000))
        
        result = benchmark(operation_with_timer)
        
        assert result == sum(range(1000))
        
        # Verify timing was recorded
        latest = monitor.metrics.get_latest("operation_duration_context_benchmark")
        assert latest is not None
    
    def test_multiple_concurrent_timers_performance(self, benchmark, monitor):
        """Benchmark performance with multiple concurrent timers."""
        def concurrent_operations():
            results = []
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for i in range(4):
                    @monitor.timed(f"concurrent_op_{i}")
                    def operation(op_id=i):
                        # Simulate some work
                        total = 0
                        for j in range(1000):
                            total += j * op_id
                        return total
                    
                    futures.append(executor.submit(operation))
                
                # Wait for all operations to complete
                for future in futures:
                    results.append(future.result())
            
            return results
        
        results = benchmark(concurrent_operations)
        
        assert len(results) == 4
        
        # Verify all timers recorded metrics
        for i in range(4):
            latest = monitor.metrics.get_latest(f"operation_duration_concurrent_op_{i}")
            assert latest is not None
    
    def test_performance_summary_generation_speed(self, benchmark, monitor):
        """Benchmark performance summary generation speed."""
        # Pre-populate with various metrics
        for i in range(1000):
            monitor.record_counter(f"counter_{i % 10}", 1.0)
            monitor.record_gauge(f"gauge_{i % 5}", float(i))
            
            with monitor.timer(f"operation_{i % 3}"):
                time.sleep(0.001)  # Small delay to generate realistic timing data
        
        def generate_summary():
            return monitor.get_performance_summary(duration_seconds=60)
        
        summary = benchmark(generate_summary)
        
        # Verify summary quality
        assert 'timestamp' in summary
        assert 'resource_usage' in summary
        assert 'operation_metrics' in summary
        assert len(summary['operation_metrics']) > 0


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
            with monitor.timer(f"task_{task_id % 10}", tags={"task_type": "simulation"}):
                # Simulate async work with varying duration
                await asyncio.sleep(0.01 + (task_id % 5) * 0.001)
                monitor.record_counter("tasks_completed", 1.0)
                return f"Task {task_id} completed"
        
        # Test different concurrency levels
        concurrency_levels = [10, 50, 100, 200]
        performance_results = {}
        
        for concurrency in concurrency_levels:
            start_time = time.time()
            
            # Create and run concurrent tasks
            tasks = [simulated_task(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            performance_results[concurrency] = {
                'duration': duration,
                'tasks_per_second': concurrency / duration,
                'completed_tasks': len(results)
            }
        
        await monitor.stop()
        
        # Verify scalability characteristics
        for concurrency, metrics in performance_results.items():
            assert metrics['completed_tasks'] == concurrency
            assert metrics['tasks_per_second'] > 0
            
            # Performance should not degrade dramatically with higher concurrency
            if concurrency <= 100:
                assert metrics['duration'] < 5.0  # Should complete within 5 seconds
    
    def test_thread_safety_under_load(self, benchmark):
        """Test thread safety of components under high load."""
        collector = MetricsCollector()
        results = {"errors": 0, "successful_operations": 0}
        
        def stress_test_thread_safety():
            def worker_thread(worker_id: int):
                try:
                    for i in range(1000):
                        # Perform various operations that should be thread-safe
                        collector.record(f"worker_{worker_id}_metric", float(i))
                        
                        if i % 10 == 0:
                            latest = collector.get_latest(f"worker_{worker_id}_metric")
                            if latest:
                                results["successful_operations"] += 1
                        
                        if i % 50 == 0:
                            history = collector.get_history(f"worker_{worker_id}_metric", limit=10)
                            if history:
                                results["successful_operations"] += 1
                                
                except Exception as e:
                    results["errors"] += 1
            
            # Run multiple worker threads concurrently
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for worker_id in range(8):
                    futures.append(executor.submit(worker_thread, worker_id))
                
                # Wait for all workers to complete
                for future in futures:
                    future.result()
        
        benchmark(stress_test_thread_safety)
        
        # Verify thread safety - no errors and successful operations
        assert results["errors"] == 0
        assert results["successful_operations"] > 0
        
        # Verify data integrity
        for worker_id in range(8):
            history = collector.get_history(f"worker_{worker_id}_metric")
            assert len(history) == 1000  # All metrics should be recorded


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
                unit="units"
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
        assert retrieval_time < 5.0   # Retrieval should be fast
        assert memory_growth < 200    # Should not use excessive memory (less than 200MB)
        
        # Verify data quality
        for i in range(0, 100, 10):
            history = collector.get_history(f"metric_{i}")
            assert len(history) <= 10000  # Respects max_history limit
    
    def test_garbage_collection_efficiency(self):
        """Test garbage collection efficiency with metric cleanup."""
        collector = MetricsCollector(max_history=1000)
        
        # Create and clear metrics multiple times to test GC
        for cycle in range(10):
            # Create many metrics
            for i in range(5000):
                collector.record(f"gc_test_metric_{cycle}", float(i))
            
            # Force garbage collection
            gc.collect()
            
            # Clear metrics to trigger cleanup
            collector.clear(f"gc_test_metric_{cycle}")
        
        # Verify memory is properly cleaned up
        process = psutil.Process()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # After cleanup, memory should be reasonable
        assert final_memory < 500  # Less than 500MB
        
        # Verify collector state is clean
        assert len(collector._metrics) == 0
    
    @pytest.mark.asyncio
    async def test_resource_tracker_efficiency(self):
        """Test ResourceTracker memory and CPU efficiency."""
        tracker = ResourceTracker(collection_interval=0.05, max_history=2000)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu_times = process.cpu_times()
        
        # Run tracker for a period
        await tracker.start()
        start_time = time.time()
        
        # Let it collect data for 5 seconds
        await asyncio.sleep(5.0)
        
        await tracker.stop()
        end_time = time.time()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu_times = process.cpu_times()
        
        # Calculate resource usage
        memory_increase = final_memory - initial_memory
        cpu_time_used = (final_cpu_times.user - initial_cpu_times.user) + \
                       (final_cpu_times.system - initial_cpu_times.system)
        
        # Verify efficiency
        snapshots = tracker.get_snapshots()
        collection_rate = len(snapshots) / (end_time - start_time)
        
        assert memory_increase < 50  # Should use less than 50MB additional memory
        assert cpu_time_used < 1.0   # Should use less than 1 second of CPU time
        assert collection_rate >= 15  # Should collect at reasonable rate (≥15 snapshots/second)
        assert len(snapshots) <= 2000  # Should respect max_history


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
            endpoint = ["/api/users", "/api/orders", "/api/products", "/api/health"][request_id % 4]
            
            with monitor.timer("http_request", tags={"method": request_type, "endpoint": endpoint}):
                # Simulate request processing time
                processing_time = 0.01 + (request_id % 10) * 0.005  # Varying response times
                await asyncio.sleep(processing_time)
                
                # Record request metrics
                monitor.record_counter("http_requests_total", 1.0, tags={"method": request_type})
                monitor.record_gauge("active_connections", float(50 + request_id % 20))
                
                # Simulate occasional errors
                if request_id % 50 == 0:
                    monitor.record_counter("http_errors_total", 1.0, tags={"status": "500"})
                else:
                    monitor.record_counter("http_success_total", 1.0, tags={"status": "200"})
                
                return f"Request {request_id} processed"
        
        # Simulate high load - 1000 concurrent requests
        start_time = time.time()
        
        # Process requests in batches to simulate realistic load patterns
        batch_size = 100
        total_requests = 1000
        
        for batch_start in range(0, total_requests, batch_size):
            batch_tasks = []
            for i in range(batch_start, min(batch_start + batch_size, total_requests)):
                batch_tasks.append(simulate_web_request(i))
            
            # Process batch
            await asyncio.gather(*batch_tasks)
            
            # Small delay between batches
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        await monitor.stop()
        
        # Analyze performance
        summary = monitor.get_performance_summary(duration_seconds=total_duration + 10)
        
        # Verify monitoring captured the load
        assert 'http_request' in summary['operation_metrics']
        http_metrics = summary['operation_metrics']['http_request']
        
        assert http_metrics['count'] == total_requests
        assert http_metrics['avg_duration'] > 0
        assert total_duration < 30.0  # Should complete within 30 seconds
        
        # Verify request throughput
        requests_per_second = total_requests / total_duration
        assert requests_per_second > 30  # Should handle at least 30 requests per second
    
    def test_data_processing_pipeline_monitoring(self, benchmark):
        """Simulate monitoring a data processing pipeline."""
        monitor = PerformanceMonitor()
        
        def simulate_data_pipeline():
            # Simulate pipeline stages
            stages = [
                ("data_extraction", 0.02),
                ("data_validation", 0.01),
                ("data_transformation", 0.05),
                ("data_loading", 0.03)
            ]
            
            pipeline_results = []
            
            for batch_id in range(100):  # Process 100 batches
                batch_results = {}
                
                for stage_name, base_duration in stages:
                    with monitor.timer(stage_name, tags={"batch_id": str(batch_id)}):
                        # Simulate varying processing times
                        processing_time = base_duration + (batch_id % 5) * 0.001
                        time.sleep(processing_time)
                        
                        # Record stage metrics
                        monitor.record_counter(f"{stage_name}_processed", 1.0)
                        monitor.record_gauge(f"{stage_name}_queue_size", float(10 - batch_id % 10))
                        
                        batch_results[stage_name] = "completed"
                
                pipeline_results.append(batch_results)
                
                # Record pipeline completion
                monitor.record_counter("pipeline_batches_completed", 1.0)
            
            return pipeline_results
        
        results = benchmark(simulate_data_pipeline)
        
        # Verify pipeline completion
        assert len(results) == 100
        
        # Verify monitoring data
        for stage_name, _ in [("data_extraction", 0), ("data_validation", 0), 
                             ("data_transformation", 0), ("data_loading", 0)]:
            stage_metrics = monitor.metrics.get_history(f"operation_duration_{stage_name}")
            assert len(stage_metrics) == 100  # Each stage processed 100 batches
    
    @pytest.mark.asyncio 
    async def test_microservices_monitoring_simulation(self):
        """Simulate monitoring a microservices architecture."""
        # Create separate monitors for different services
        services = {
            "user-service": PerformanceMonitor(),
            "order-service": PerformanceMonitor(),
            "payment-service": PerformanceMonitor(),
            "notification-service": PerformanceMonitor()
        }
        
        # Start all monitors
        for monitor in services.values():
            await monitor.start()
        
        async def simulate_service_operation(service_name: str, operation: str, duration: float):
            monitor = services[service_name]
            
            with monitor.timer(f"{service_name}_{operation}"):
                await asyncio.sleep(duration)
                
                # Record service-specific metrics
                monitor.record_counter(f"{service_name}_operations", 1.0, 
                                     tags={"operation": operation})
                monitor.record_gauge(f"{service_name}_cpu_usage", 
                                   float(20 + hash(service_name) % 30))
        
        # Simulate inter-service communication patterns
        async def simulate_user_workflow():
            # User registration workflow
            await simulate_service_operation("user-service", "register", 0.02)
            await simulate_service_operation("notification-service", "send_welcome", 0.01)
            
        async def simulate_order_workflow():
            # Order processing workflow
            await simulate_service_operation("user-service", "authenticate", 0.005)
            await simulate_service_operation("order-service", "create_order", 0.03)
            await simulate_service_operation("payment-service", "process_payment", 0.08)
            await simulate_service_operation("order-service", "update_status", 0.01)
            await simulate_service_operation("notification-service", "send_confirmation", 0.01)
        
        # Run concurrent workflows
        workflows = []
        for _ in range(50):  # 50 user registrations
            workflows.append(simulate_user_workflow())
        for _ in range(30):  # 30 order processes
            workflows.append(simulate_order_workflow())
        
        start_time = time.time()
        await asyncio.gather(*workflows)
        end_time = time.time()
        
        # Stop all monitors
        for monitor in services.values():
            await monitor.stop()
        
        total_duration = end_time - start_time
        
        # Verify microservices monitoring
        assert total_duration < 20.0  # Should complete within 20 seconds
        
        # Verify each service recorded metrics
        for service_name, monitor in services.items():
            summary = monitor.get_performance_summary(duration_seconds=total_duration + 5)
            assert len(summary['operation_metrics']) > 0
            
            # Verify service-specific operations were recorded
            operation_names = list(summary['operation_metrics'].keys())
            service_operations = [op for op in operation_names if service_name in op]
            assert len(service_operations) > 0