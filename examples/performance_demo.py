#!/usr/bin/env python3
"""
Performance Framework Demo

This script demonstrates the comprehensive performance optimization capabilities
of the Gary-Zero Performance Framework.
"""

import asyncio
import os
import random
import sys
import time
from typing import Any

# Add framework to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.performance import (
    async_timer,
    auto_optimize,
    cached,
    get_cache_manager,
    get_performance_monitor,
    get_resource_optimizer,
    run_background,
    timer,
)


class PerformanceDemo:
    """Demo class showcasing performance optimization features."""

    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.monitor = get_performance_monitor()
        self.optimizer = get_resource_optimizer()

        # Demo data
        self.user_database = {
            i: {
                "id": i,
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "profile": {"score": random.randint(1, 100)}
            }
            for i in range(1000)
        }

    async def start(self):
        """Initialize performance monitoring."""
        print("🚀 Starting Performance Demo...")
        await self.monitor.start()

        # Register cache cleanup with optimizer
        self.optimizer.register_cache_cleanup(self.cache_manager.clear)

        print("✅ Performance monitoring started")

    async def stop(self):
        """Clean shutdown."""
        await self.monitor.stop()
        print("✅ Performance monitoring stopped")

    # === Caching Demonstrations ===

    @cached(ttl=300)  # Cache for 5 minutes
    @timer("database_lookup")
    def get_user(self, user_id: int) -> dict[str, Any]:
        """Simulate expensive database lookup with caching."""
        print(f"🔍 Database lookup for user {user_id}")
        time.sleep(0.1)  # Simulate database latency
        return self.user_database.get(user_id, {})

    @timer("batch_user_lookup")
    def get_users_batch(self, user_ids: list[int]) -> list[dict[str, Any]]:
        """Get multiple users with individual caching."""
        return [self.get_user(user_id) for user_id in user_ids]

    # === Performance Monitoring Demonstrations ===

    @async_timer("async_data_processing")
    async def process_user_data(self, user_ids: list[int]) -> dict[str, Any]:
        """Async data processing with performance monitoring."""
        print(f"⚡ Processing {len(user_ids)} users asynchronously...")

        # Simulate async processing
        users = []
        for user_id in user_ids:
            user = self.get_user(user_id)
            if user:
                await asyncio.sleep(0.01)  # Simulate async I/O
                users.append(user)

        # Record custom metrics
        self.monitor.record_counter("users_processed", len(users))
        self.monitor.record_gauge("processing_batch_size", len(user_ids))

        return {
            "total_users": len(users),
            "average_score": sum(u["profile"]["score"] for u in users) / len(users) if users else 0
        }

    @timer("cpu_intensive_task")
    @auto_optimize(memory_threshold=0.7, cpu_threshold=0.7)
    def cpu_intensive_computation(self, iterations: int = 100000) -> float:
        """CPU-intensive task with auto-optimization."""
        print(f"🔥 Running CPU-intensive computation ({iterations} iterations)...")

        result = 0
        for i in range(iterations):
            result += i ** 0.5

        return result

    async def background_task_demo(self) -> str:
        """Demonstrate background task processing."""
        print("🔄 Submitting background tasks...")

        # Submit multiple background tasks
        task_ids = []
        for i in range(3):
            task_id = await run_background(
                f"data_processing_{i}",
                self.process_user_data([i * 10 + j for j in range(10)]),
                priority=i  # Higher priority for later tasks
            )
            task_ids.append(task_id)

        # Wait for all tasks to complete
        from framework.performance.async_utils import get_task_manager
        task_manager = get_task_manager()
        results = await task_manager.wait_all(timeout=30.0)

        return f"Completed {len(results)} background tasks"

    def demonstrate_caching(self):
        """Demonstrate caching performance improvements."""
        print("\n📦 === CACHING DEMONSTRATION ===")

        user_ids = [1, 2, 3, 1, 2, 3, 4, 5]  # Note the duplicates

        # First call - will hit database
        start_time = time.time()
        users = self.get_users_batch(user_ids)
        first_duration = time.time() - start_time

        # Second call - should use cache for duplicates
        start_time = time.time()
        users_cached = self.get_users_batch(user_ids)
        second_duration = time.time() - start_time

        # Show cache statistics
        cache_stats = self.cache_manager.stats()

        print(f"First batch lookup: {first_duration:.3f}s")
        print(f"Second batch lookup: {second_duration:.3f}s")
        print(f"Speed improvement: {(first_duration / second_duration):.1f}x")
        print(f"Cache hit ratio: {cache_stats['hit_ratio']:.1%}")
        print(f"Cache size: {cache_stats['primary_cache_size']} items")

    async def demonstrate_async_performance(self):
        """Demonstrate async performance monitoring."""
        print("\n⚡ === ASYNC PERFORMANCE DEMONSTRATION ===")

        # Process multiple batches concurrently
        batch_tasks = [
            self.process_user_data([i * 20 + j for j in range(20)])
            for i in range(3)
        ]

        start_time = time.time()
        results = await asyncio.gather(*batch_tasks)
        duration = time.time() - start_time

        total_users = sum(r["total_users"] for r in results)
        avg_score = sum(r["average_score"] for r in results) / len(results)

        print(f"Processed {total_users} users in {duration:.2f}s")
        print(f"Average user score: {avg_score:.1f}")
        print(f"Processing rate: {total_users / duration:.0f} users/second")

    def demonstrate_resource_optimization(self):
        """Demonstrate resource optimization."""
        print("\n🧠 === RESOURCE OPTIMIZATION DEMONSTRATION ===")

        # Get initial resource status
        status_before = self.optimizer.get_resource_status()
        print(f"Memory usage before: {status_before['memory']['usage_percent']:.1f}%")
        print(f"CPU usage before: {status_before['cpu']['usage_percent']:.1f}%")

        # Run memory and CPU intensive tasks
        _ = self.cpu_intensive_computation(50000)

        # Create some memory pressure
        large_data = [[i] * 1000 for i in range(1000)]

        # Perform optimization
        memory_result = self.optimizer.optimize_memory()
        cpu_result = self.optimizer.optimize_cpu()

        status_after = self.optimizer.get_resource_status()

        print(f"Memory optimization: {memory_result.improvement_percent:.1f}% improvement")
        print(f"CPU optimization: {cpu_result.improvement_percent:.1f}% improvement")
        print(f"Memory usage after: {status_after['memory']['usage_percent']:.1f}%")

        # Clean up
        del large_data

    def show_performance_summary(self):
        """Show comprehensive performance summary."""
        print("\n📊 === PERFORMANCE SUMMARY ===")

        # Cache statistics
        cache_stats = self.cache_manager.stats()
        print("Cache Performance:")
        print(f"  Hit Ratio: {cache_stats['hit_ratio']:.1%}")
        print(f"  Total Requests: {cache_stats['total_requests']}")
        print(f"  Primary Cache Size: {cache_stats['primary_cache_size']}")

        # Performance metrics summary
        perf_summary = self.monitor.get_performance_summary(duration_seconds=300)
        print("\nOperation Performance (last 5 minutes):")

        for operation, metrics in perf_summary['operation_metrics'].items():
            print(f"  {operation}:")
            print(f"    Count: {metrics['count']}")
            print(f"    Avg Duration: {metrics['avg_duration']:.3f}s")
            print(f"    95th Percentile: {metrics['p95_duration']:.3f}s")

        # Resource usage
        resource_usage = perf_summary['resource_usage']
        print("\nResource Usage:")
        print(f"  Current CPU: {resource_usage['current']['cpu_percent']:.1f}%")
        print(f"  Current Memory: {resource_usage['current']['memory_percent']:.1f}%")
        print(f"  Average CPU: {resource_usage['average'].get('cpu_percent', 0):.1f}%")
        print(f"  Average Memory: {resource_usage['average'].get('memory_percent', 0):.1f}%")

        # Alerts
        if perf_summary['alerts']:
            print("\nAlerts:")
            for alert in perf_summary['alerts']:
                print(f"  ⚠️  {alert['type']}: {alert['message']}")

        # Optimization report
        opt_report = self.optimizer.generate_optimization_report()
        opt_summary = opt_report['optimization_summary']

        print("\nOptimization Summary:")
        print(f"  Total Optimizations: {opt_summary['total_optimizations']}")
        print(f"  Avg Memory Improvement: {opt_summary['avg_memory_improvement_percent']:.1f}%")
        print(f"  Avg CPU Improvement: {opt_summary['avg_cpu_improvement_percent']:.1f}%")

        if opt_report['recommendations']:
            print("\nRecommendations:")
            for rec in opt_report['recommendations']:
                print(f"  💡 {rec}")


async def main():
    """Run the performance demonstration."""
    demo = PerformanceDemo()

    try:
        await demo.start()

        # Run demonstrations
        demo.demonstrate_caching()
        await demo.demonstrate_async_performance()

        # Background task demo
        bg_result = await demo.background_task_demo()
        print(f"\n🔄 Background tasks: {bg_result}")

        # Resource optimization
        demo.demonstrate_resource_optimization()

        # Show final performance summary
        demo.show_performance_summary()

        print("\n🎉 Performance demonstration completed!")

    finally:
        await demo.stop()


if __name__ == "__main__":
    # Add some startup delay to let things initialize
    print("🔧 Initializing performance demo...")
    asyncio.run(main())
