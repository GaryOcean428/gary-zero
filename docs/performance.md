# Performance Optimization Framework

The Gary-Zero Performance Framework provides comprehensive performance optimization tools for high-performance applications.


## Overview

The framework includes four main components:

- **Caching System**: Multi-tier caching with in-memory and persistent storage
- **Async Utilities**: Enhanced async patterns and background task management
- **Performance Monitoring**: Real-time metrics collection and resource tracking
- **Resource Optimization**: Automatic memory and CPU optimization


## Quick Start

```python
from framework.performance import (
    get_cache_manager, get_performance_monitor, get_resource_optimizer,
    cached, timer, auto_optimize
)

# Initialize performance monitoring
monitor = get_performance_monitor()
await monitor.start()

# Use caching decorator
@cached(ttl=300)  # Cache for 5 minutes
def expensive_computation(data):
    # Expensive operation
    return process_data(data)

# Use timing decorator
@timer("api_call")
def make_api_call():
    # API call code
    return response

# Use auto-optimization decorator
@auto_optimize(memory_threshold=0.8)
def memory_intensive_task():
    # Memory-intensive operation
    return result
```


## Caching System

### Multi-Tier Caching

The caching system supports multiple storage tiers for optimal performance:

```python
from framework.performance.cache import CacheManager, MemoryCache, PersistentCache

# Create multi-tier cache
cache_manager = CacheManager(
    primary=MemoryCache(max_size=1000, default_ttl=3600),
    secondary=PersistentCache(cache_dir=".cache")
)

# Basic operations
cache_manager.set("key", "value", ttl=300)
value = cache_manager.get("key")
cache_manager.delete("key")
cache_manager.clear()

# Check cache statistics
stats = cache_manager.stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
```

### Cache Decorators

```python
# Function-level caching
@cache_manager.cache(ttl=600)
def get_user_data(user_id):
    return database.get_user(user_id)

# Custom cache key generation
@cache_manager.cache(
    ttl=300,
    key_func=lambda user_id, include_profile: f"user_{user_id}_{include_profile}"
)
def get_user_with_profile(user_id, include_profile=True):
    return database.get_user_with_profile(user_id, include_profile)
```

### Memory Cache Features

- **LRU Eviction**: Automatically evicts least recently used items
- **TTL Support**: Time-based expiration with configurable defaults
- **Thread Safety**: Safe for concurrent access
- **Memory Efficiency**: Optimized memory usage with weak references

```python
from framework.performance.cache import MemoryCache

cache = MemoryCache(
    max_size=1000,      # Maximum number of items
    default_ttl=3600    # Default TTL in seconds
)

# Set with custom TTL
cache.set("temporary", "value", ttl=60)

# Get cache statistics
stats = cache.stats()
print(f"Cache size: {stats['size']}/{stats['max_size']}")
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
print(f"Memory usage: {stats['memory_usage']} bytes")
```

### Persistent Cache Features

- **Multiple Serialization Formats**: JSON and Pickle support
- **File-Based Storage**: Survives application restarts
- **TTL Support**: Persistent expiration tracking
- **Safe Concurrency**: File locking for concurrent access

```python
from framework.performance.cache import PersistentCache

# JSON serialization (human-readable)
json_cache = PersistentCache(
    cache_dir=".cache",
    serializer="json"
)

# Pickle serialization (supports complex objects)
pickle_cache = PersistentCache(
    cache_dir=".cache",
    serializer="pickle"
)

# Store complex objects
cache.set("model", trained_model, ttl=86400)  # Cache for 24 hours
```


## Async Utilities

### Background Task Management

```python
from framework.performance.async_utils import BackgroundTaskManager, get_task_manager

# Get default task manager
task_manager = get_task_manager()

# Submit background task
async def process_data(data):
    # Long-running data processing
    return processed_result

task_id = await task_manager.submit("data_processing", process_data(large_dataset))

# Wait for completion
result = await task_manager.wait(task_id, timeout=300)

# Check task status
status = task_manager.get_task_status(task_id)
print(f"Task status: {status['status']}")
print(f"Duration: {status['duration']} seconds")
```

### Async Connection Pooling

```python
from framework.performance.async_utils import AsyncPool

# Create database connection pool
def create_db_connection():
    return database.connect()

db_pool = AsyncPool(
    factory=create_db_connection,
    max_size=10,
    min_size=2,
    timeout=30.0,
    cleanup_func=lambda conn: conn.close()
)

# Use connection from pool
async with db_pool.get() as connection:
    result = await connection.execute(query)

# Manual acquire/release
connection = await db_pool.acquire()
try:
    result = await connection.execute(query)
finally:
    await db_pool.release(connection)
```

### Async Decorators

```python
from framework.performance.async_utils import async_timeout, async_retry

# Add timeout to async functions
@async_timeout(30.0)
async def api_call():
    response = await http_client.get(url)
    return response.json()

# Add retry logic with exponential backoff
@async_retry(max_attempts=3, delay=1.0, backoff=2.0)
async def flaky_operation():
    response = await unreliable_service.call()
    if response.status_code != 200:
        raise Exception("Service unavailable")
    return response.data
```


## Performance Monitoring

### Real-Time Metrics Collection

```python
from framework.performance.monitor import PerformanceMonitor, get_performance_monitor

# Get default monitor
monitor = get_performance_monitor()
await monitor.start()

# Record custom metrics
monitor.record_counter("api_requests", 1, tags={"endpoint": "/users"})
monitor.record_gauge("queue_size", 42)
monitor.record_histogram("response_time", 0.123)

# Use timing context manager
with monitor.timer("database_query", tags={"table": "users"}):
    results = database.query("SELECT * FROM users")

# Get performance summary
summary = monitor.get_performance_summary(duration_seconds=300)
print(f"Average CPU: {summary['resource_usage']['average']['cpu_percent']:.1f}%")
print(f"Average Memory: {summary['resource_usage']['average']['memory_percent']:.1f}%")
```

### Resource Tracking

```python
from framework.performance.monitor import ResourceTracker

# Create resource tracker
tracker = ResourceTracker(
    collection_interval=5.0,  # Collect every 5 seconds
    max_history=720          # Keep 1 hour of history
)

await tracker.start()

# Get latest resource snapshot
snapshot = tracker.get_latest_snapshot()
print(f"CPU: {snapshot.cpu_percent}%")
print(f"Memory: {snapshot.memory_percent}%")
print(f"Disk I/O: {snapshot.disk_io_read_mb:.1f}MB read, {snapshot.disk_io_write_mb:.1f}MB write")

# Get historical averages
avg_usage = tracker.get_average_usage(duration_seconds=3600)  # Last hour
print(f"Average CPU over last hour: {avg_usage['cpu_percent']:.1f}%")
```

### Performance Decorators

```python
from framework.performance.monitor import timer, async_timer

# Time synchronous functions
@timer("user_lookup")
def get_user(user_id):
    return database.get_user(user_id)

# Time asynchronous functions
@async_timer("async_processing")
async def process_async_task(data):
    result = await async_processor.process(data)
    return result

# Access timing data
monitor = get_performance_monitor()
avg_time = monitor.metrics.get_average("operation_duration_user_lookup", duration_seconds=3600)
print(f"Average user lookup time: {avg_time:.3f} seconds")
```


## Resource Optimization

### Automatic Resource Optimization

```python
from framework.performance.optimizer import get_resource_optimizer, optimize_memory

# Get default optimizer
optimizer = get_resource_optimizer()

# Manual optimization
memory_result = optimizer.optimize_memory()
print(f"Memory optimization: {memory_result.improvement_percent:.1f}% improvement")

cpu_result = optimizer.optimize_cpu()
print(f"CPU optimization: {cpu_result.improvement_percent:.1f}% improvement")

# Optimize all resources
results = optimizer.optimize_all(memory_threshold=0.8, cpu_threshold=0.8)
for result in results:
    print(f"{result.optimization_type}: {result.improvement_percent:.1f}% improvement")
```

### Memory Optimization

```python
from framework.performance.optimizer import MemoryOptimizer

memory_optimizer = MemoryOptimizer()

# Register cache cleanup functions
def cleanup_user_cache():
    user_cache.clear()
    return len(user_cache)

memory_optimizer.register_cache_cleanup(cleanup_user_cache)

# Register weak cache references for automatic cleanup
memory_optimizer.register_weak_cache(some_cache_object)

# Perform optimization
result = memory_optimizer.optimize()
print(f"Memory freed: {result.improvement:.2f}")
print("Recommendations:")
for recommendation in result.recommendations:
    print(f"  - {recommendation}")
```

### Auto-Optimization

```python
from framework.performance.optimizer import auto_optimize

# Decorator for automatic optimization
@auto_optimize(memory_threshold=0.8, cpu_threshold=0.8)
def resource_intensive_function():
    # Function that may use significant resources
    return process_large_dataset()

# Start automatic optimization background process
optimizer = get_resource_optimizer()
optimizer.start_auto_optimization(
    interval=300.0,          # Every 5 minutes
    memory_threshold=0.8,    # Optimize if memory > 80%
    cpu_threshold=0.8        # Optimize if CPU > 80%
)

# Stop auto-optimization
optimizer.stop_auto_optimization()
```

### Resource Status Monitoring

```python
# Get comprehensive resource status
status = optimizer.get_resource_status()
print(f"Memory usage: {status['memory']['usage_percent']:.1f}%")
print(f"CPU usage: {status['cpu']['usage_percent']:.1f}%")
print(f"Auto-optimization active: {status['auto_optimization_active']}")

# Generate optimization report
report = optimizer.generate_optimization_report()
print(f"Total optimizations: {report['optimization_summary']['total_optimizations']}")
print(f"Average memory improvement: {report['optimization_summary']['avg_memory_improvement_percent']:.1f}%")

print("Recommendations:")
for recommendation in report['recommendations']:
    print(f"  - {recommendation}")
```


## Integration Example

Here's a complete example integrating all performance components:

```python
import asyncio
from framework.performance import *

class HighPerformanceService:
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.monitor = get_performance_monitor()
        self.optimizer = get_resource_optimizer()

    async def start(self):
        """Initialize performance monitoring and optimization."""
        await self.monitor.start()
        self.optimizer.start_auto_optimization(interval=300.0)

        # Register cache cleanup with optimizer
        self.optimizer.register_cache_cleanup(self.cache_manager.clear)

    async def stop(self):
        """Clean shutdown of performance systems."""
        await self.monitor.stop()
        self.optimizer.stop_auto_optimization()

    @cached(ttl=300)
    @timer("user_data_fetch")
    @auto_optimize(memory_threshold=0.8)
    def get_user_data(self, user_id):
        """Get user data with caching, timing, and auto-optimization."""
        with self.monitor.timer("database_query"):
            return database.get_user(user_id)

    @async_timer("async_task_processing")
    async def process_background_task(self, data):
        """Process data in background with performance monitoring."""
        task_manager = get_task_manager()

        async def processing_task():
            with self.monitor.timer("data_processing"):
                return await heavy_data_processing(data)

        task_id = await task_manager.submit("data_processing", processing_task())
        return await task_manager.wait(task_id)

    def get_performance_report(self):
        """Get comprehensive performance report."""
        return {
            'cache_stats': self.cache_manager.stats(),
            'performance_summary': self.monitor.get_performance_summary(),
            'optimization_report': self.optimizer.generate_optimization_report()
        }

# Usage
async def main():
    service = HighPerformanceService()
    await service.start()

    try:
        # Use the service
        user_data = service.get_user_data(123)
        result = await service.process_background_task(large_dataset)

        # Get performance report
        report = service.get_performance_report()
        print(f"Cache hit ratio: {report['cache_stats']['hit_ratio']:.2%}")

    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
```


## Configuration

### Environment Variables

```bash
# Cache configuration
CACHE_MAX_SIZE=1000
CACHE_DEFAULT_TTL=3600
CACHE_DIR=.cache

# Performance monitoring
PERF_MONITOR_ENABLED=true
PERF_RESOURCE_TRACKING_INTERVAL=5.0
PERF_METRICS_MAX_HISTORY=1000

# Resource optimization
OPTIMIZER_AUTO_ENABLED=true
OPTIMIZER_MEMORY_THRESHOLD=0.8
OPTIMIZER_CPU_THRESHOLD=0.8
OPTIMIZER_INTERVAL=300.0
```

### Programmatic Configuration

```python
from framework.performance import *

# Configure cache manager
cache_manager = CacheManager(
    primary=MemoryCache(max_size=2000, default_ttl=7200),
    secondary=PersistentCache(cache_dir="/var/cache/app", serializer="pickle")
)

# Configure performance monitor
monitor = PerformanceMonitor(
    metrics_collector=MetricsCollector(max_history=2000),
    resource_tracker=ResourceTracker(
        collection_interval=1.0,  # More frequent collection
        max_history=3600         # 1 hour at 1-second intervals
    )
)

# Configure resource optimizer
optimizer = ResourceOptimizer(
    memory_optimizer=MemoryOptimizer(),
    cpu_optimizer=CPUOptimizer(),
    auto_optimize_interval=600.0  # 10-minute intervals
)
```


## Best Practices

### Caching

1. **Use appropriate TTL values** based on data volatility
2. **Monitor cache hit ratios** and adjust cache sizes accordingly
3. **Use tags for cache invalidation** when related data changes
4. **Choose serialization format** based on data complexity and performance needs

### Async Utilities

1. **Set appropriate timeouts** for async operations
2. **Use connection pooling** for expensive resources
3. **Monitor background task queues** to prevent backlog
4. **Handle task failures gracefully** with retry logic

### Performance Monitoring

1. **Collect metrics consistently** across all components
2. **Set up alerting** for performance thresholds
3. **Use tags to segment metrics** by component or operation
4. **Export metrics** to external monitoring systems

### Resource Optimization

1. **Set conservative thresholds** to avoid over-optimization
2. **Monitor optimization effectiveness** through metrics
3. **Register cleanup functions** for custom caches and resources
4. **Use auto-optimization** for production environments


## Troubleshooting

### Common Issues

**High Memory Usage**

```python
# Check memory status
optimizer = get_resource_optimizer()
status = optimizer.get_resource_status()
print(status['memory'])

# Force memory optimization
result = optimizer.optimize_memory()
print(result.recommendations)
```

**Performance Bottlenecks**

```python
# Analyze operation timings
monitor = get_performance_monitor()
summary = monitor.get_performance_summary(duration_seconds=3600)

for operation, metrics in summary['operation_metrics'].items():
    if metrics['avg_duration'] > 1.0:  # Slow operations
        print(f"Slow operation: {operation} ({metrics['avg_duration']:.2f}s avg)")
```

**Cache Misses**

```python
# Check cache statistics
cache_manager = get_cache_manager()
stats = cache_manager.stats()

if stats['hit_ratio'] < 0.8:  # Low hit ratio
    print("Consider:")
    print("- Increasing cache size")
    print("- Adjusting TTL values")
    print("- Reviewing cache key strategy")
```

For more detailed information, see the API documentation in `docs/api/performance/`.
