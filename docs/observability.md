# Advanced Observability Framework

The Gary-Zero Observability Framework provides enterprise-grade monitoring, tracing, and performance analysis capabilities for AI agent applications.

## 🏗️ Architecture Overview

The observability framework consists of four core components:

### 1. Metrics Collection (`framework.observability.metrics`)
- **Real-time metrics collection** with automatic aggregation
- **Custom metric definitions** with labels and validation
- **Built-in system metrics** (CPU, memory, disk, network)
- **Application metrics** (requests, errors, model inference)
- **Export integration** for external monitoring systems

### 2. Distributed Tracing (`framework.observability.tracing`)
- **Automatic trace context propagation** across service boundaries
- **Span lifecycle management** with attributes and events
- **Performance correlation** with metrics data
- **Error tracking** and exception correlation
- **Integration with external tracing systems**

### 3. Health Monitoring (`framework.observability.health`)
- **Multi-level health checks** (system, application, dependencies)
- **Automatic health status aggregation** with configurable criticality
- **Alerting and notification** capabilities
- **Health history and trend analysis**
- **Kubernetes-compatible endpoints** (/health/ready, /health/live)

### 4. Performance Profiling (`framework.observability.profiling`)
- **CPU and memory profiling** with detailed analysis
- **Performance bottleneck identification** and recommendations
- **Custom performance metrics** collection
- **Performance trend tracking** over time
- **Integration with observability stack**

## 🚀 Quick Start

### Basic Setup

```python
from framework.observability.middleware import create_observability_stack

# Create complete observability stack
observability = create_observability_stack(
    service_name="gary-zero",
    enable_system_metrics=True,
    enable_tracing=True,
    enable_health_monitoring=True,
    enable_profiling=True
)

# Components are now available:
metrics = observability["metrics"]
tracer = observability["tracer"] 
health = observability["health"]
profiler = observability["profiler"]
```

### FastAPI Integration

```python
from fastapi import FastAPI
from framework.observability.middleware import ObservabilityMiddleware, HealthCheckEndpoints

app = FastAPI()

# Add observability middleware
app.add_middleware(
    ObservabilityMiddleware,
    metrics_collector=metrics,
    tracer=tracer,
    health_monitor=health,
    profiler=profiler
)

# Add health endpoints
health_endpoints = HealthCheckEndpoints(health, metrics)
app.get("/health")(health_endpoints.health_check)
app.get("/metrics")(health_endpoints.metrics_endpoint)
```

## 📊 Metrics Collection

### Built-in Metrics

The framework automatically collects system and application metrics:

- **System Metrics**: CPU, memory, disk usage, network I/O
- **HTTP Metrics**: Request count, duration, status codes
- **Agent Metrics**: Active sessions, task duration
- **Model Metrics**: Inference count, duration, token usage
- **Cache Metrics**: Hit/miss rates, performance
- **Error Metrics**: Error count by type and component

### Custom Metrics

Define and use custom metrics for your application:

```python
from framework.observability import MetricsRegistry, CustomMetric, MetricType

registry = MetricsRegistry()

# Define custom metric
conversation_metric = CustomMetric(
    name="agent_conversations_total",
    metric_type=MetricType.COUNTER,
    description="Total agent conversations",
    labels=["agent_type", "outcome"]
)

registry.register(conversation_metric)

# Use the metric
metrics.increment("agent_conversations_total", 1, {
    "agent_type": "chat",
    "outcome": "success"
})
```

### Metric Types

- **Counter**: Monotonically increasing values (requests, errors)
- **Gauge**: Point-in-time values (active connections, queue size)
- **Histogram**: Distribution of values with configurable buckets
- **Timer**: Duration measurements with automatic statistics

## 🔍 Distributed Tracing

### Automatic Tracing

The framework provides automatic tracing for HTTP requests and internal operations:

```python
# Automatic span creation via middleware
# Each HTTP request gets a trace with:
# - Request/response attributes
# - Performance timing
# - Error tracking
# - Context propagation
```

### Manual Tracing

Create custom spans for detailed operation tracking:

```python
from framework.observability import DistributedTracer

tracer = DistributedTracer("my-service")

# Context manager approach
with tracer.span("agent_conversation") as span:
    span.set_attribute("agent.type", "chat")
    span.add_event("conversation_started")
    
    # Nested operations
    with tracer.span("model_inference") as inference_span:
        inference_span.set_attribute("model.name", "gpt-4")
        # ... model inference code ...
    
    span.add_event("conversation_completed")
```

### Decorator Approach

Use decorators for automatic function tracing:

```python
from framework.observability.tracing import trace

@trace("user_authentication", attributes={"component": "auth"})
def authenticate_user(username, password):
    # Function automatically traced
    return verify_credentials(username, password)
```

### Context Propagation

Trace context is automatically propagated across service boundaries:

```python
# Inject context into HTTP headers
carrier = {}
tracer.inject_context(carrier)
# carrier now contains: {"x-trace-id": "...", "x-span-id": "..."}

# Extract context from headers
parent_span = tracer.extract_context(incoming_headers)
child_span = tracer.start_span("child_operation", parent_span=parent_span)
```

## 🏥 Health Monitoring

### Built-in Health Checks

The framework includes system-level health checks:

- **CPU Usage**: Monitors CPU utilization with thresholds
- **Memory Usage**: Tracks memory consumption and availability
- **Disk Usage**: Monitors disk space utilization

### Custom Health Checks

Create application-specific health checks:

```python
from framework.observability import HealthMonitor, HealthCheck, HealthCheckResult, HealthStatus

def database_health_check():
    try:
        # Check database connection
        execute_test_query()
        return HealthCheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful"
        )
    except Exception as e:
        return HealthCheckResult(
            name="database", 
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {str(e)}"
        )

# Register the check
health_check = HealthCheck(
    name="database",
    check_function=database_health_check,
    interval=30.0,  # Check every 30 seconds
    critical=True   # Affects overall health status
)

health_monitor.register_check(health_check)
```

### Convenience Health Checks

Pre-built health checks for common dependencies:

```python
from framework.observability.health import (
    create_database_check,
    create_redis_check,
    create_http_check
)

# Database connectivity
db_check = create_database_check(
    name="postgres",
    connection_string="postgresql://user:pass@localhost/db"
)

# Redis connectivity
redis_check = create_redis_check(
    name="cache",
    redis_url="redis://localhost:6379"
)

# External API health
api_check = create_http_check(
    name="openai_api",
    url="https://api.openai.com/v1/models",
    expected_status=200
)

health_monitor.register_check(db_check)
health_monitor.register_check(redis_check)
health_monitor.register_check(api_check)
```

### Health Status Aggregation

Overall health status is calculated based on individual checks:

- **Healthy**: All critical checks passing
- **Degraded**: Non-critical checks failing or critical checks degraded
- **Unhealthy**: One or more critical checks failing

## ⚡ Performance Profiling

### Automatic Profiling

Enable automatic profiling for slow requests:

```python
# Middleware automatically profiles requests that exceed threshold
middleware = ObservabilityMiddleware(
    app=app,
    profiler=profiler,
    profile_slow_requests=True,
    slow_request_threshold=1.0  # Profile requests > 1 second
)
```

### Manual Profiling

Profile specific operations:

```python
from framework.observability import PerformanceProfiler

profiler = PerformanceProfiler()

# Context manager approach
with profiler.profile("model_inference") as profile:
    result = expensive_model_operation()
    
# Function profiling
result, profile_result = profiler.profile_function(
    expensive_function, 
    arg1, 
    arg2
)

# Decorator approach
from framework.observability.profiling import profile_performance

@profile_performance("data_processing")
def process_large_dataset(data):
    # Function automatically profiled
    return analyze_data(data)
```

### Performance Analysis

Get detailed performance insights:

```python
# Get specific profile result
result = profiler.get_result("model_inference")
print(f"Duration: {result.duration:.3f}s")
print(f"CPU time: {result.cpu_stats['total_time']:.3f}s")
print(f"Peak memory: {result.memory_stats['peak_memory'] / 1024**2:.1f}MB")

# Analyze performance trends
trends = profiler.analyze_trends(["session1", "session2", "session3"])
print(f"Duration trend: {trends['duration']['trend']}")  # increasing/decreasing/stable

# Export results for analysis
profiler.export_results("performance_data.json")
```

### Performance Recommendations

The profiler automatically generates optimization recommendations:

```python
result = profiler.get_result("slow_operation")
for recommendation in result.recommendations:
    print(f"💡 {recommendation}")

# Example output:
# 💡 High call count in process_data - consider caching or optimization
# 💡 High memory growth detected - check for memory leaks
# 💡 Slow function calculate_similarity - consider optimization
```

## 🔧 Middleware Integration

### Complete Integration

The `ObservabilityMiddleware` provides transparent integration:

```python
app.add_middleware(
    ObservabilityMiddleware,
    metrics_collector=metrics,
    tracer=tracer,
    health_monitor=health,
    profiler=profiler,
    enable_detailed_profiling=False,
    profile_slow_requests=True,
    slow_request_threshold=1.0
)
```

### Features Provided

- **Automatic metrics** for all HTTP requests
- **Distributed tracing** with context propagation
- **Request/response headers** with observability metadata
- **Error tracking** and correlation
- **Performance profiling** for slow requests
- **Active request tracking**

### Headers Added

The middleware adds observability headers to responses:

```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 0.234s
X-Trace-ID: 7d8c4f2a-3b9e-4d1c-8f6a-2e5b9c8d7f3a
X-Span-ID: 4a8b3c9d-2f7e-4a1b-9c5d-8e3f2a6b1c4d
```

## 📈 Monitoring Endpoints

### Health Endpoints

Standard health check endpoints for monitoring systems:

```python
# Basic health check
GET /health
{
  "status": "healthy",
  "message": "All checks passing",
  "timestamp": 1640995200.0,
  "checks": {
    "total": 5,
    "healthy": 5,
    "unhealthy": 0
  },
  "details": {
    "database": {"status": "healthy", "message": "Connection OK"},
    "redis": {"status": "healthy", "message": "Cache operational"}
  }
}

# Kubernetes readiness probe
GET /health/ready
{
  "status": "ready",
  "timestamp": 1640995200.0
}

# Kubernetes liveness probe  
GET /health/live
{
  "status": "alive",
  "timestamp": 1640995200.0
}
```

### Metrics Endpoint

Prometheus-compatible metrics endpoint:

```python
GET /metrics
{
  "metrics_count": 25,
  "prometheus_format": "system_cpu_percent 45.2\nrequest_count{method=\"GET\",endpoint=\"/api\"} 1250\n...",
  "timestamp": 1640995200.0
}
```

## 🔍 Advanced Usage

### Custom Exporters

Create custom exporters for external systems:

```python
def prometheus_exporter(metrics):
    """Export metrics to Prometheus"""
    for metric in metrics:
        # Send to Prometheus pushgateway
        send_to_prometheus(metric)

def datadog_exporter(spans):
    """Export spans to Datadog"""
    for span in spans:
        # Send to Datadog APM
        send_to_datadog(span)

# Register exporters
metrics.add_export_callback(prometheus_exporter)
tracer.add_exporter(datadog_exporter)
```

### Alert Integration

Set up alerting for health check failures:

```python
def alert_callback(check_name, result):
    """Send alert on health check failure"""
    if result.status == HealthStatus.UNHEALTHY:
        send_alert(f"Health check {check_name} failed: {result.message}")

health_monitor.add_alert_callback(alert_callback)
```

### System Monitoring

Enable continuous system monitoring:

```python
profiler.start_system_monitoring()

# Get system statistics
stats = profiler.get_system_stats(limit=100)
cpu_stats = stats["cpu"]
memory_stats = stats["memory"]

# Monitor trends
for stat in cpu_stats[-10:]:  # Last 10 measurements
    print(f"CPU: {stat['cpu_percent']:.1f}% at {stat['timestamp']}")
```

## 🛠️ Configuration

### Environment Variables

Configure observability via environment variables:

```bash
# Metrics configuration
GARY_ZERO_METRICS_ENABLED=true
GARY_ZERO_METRICS_FLUSH_INTERVAL=60
GARY_ZERO_METRICS_BUFFER_SIZE=10000

# Tracing configuration  
GARY_ZERO_TRACING_ENABLED=true
GARY_ZERO_TRACING_SAMPLE_RATE=1.0
GARY_ZERO_TRACING_SERVICE_NAME=gary-zero

# Health monitoring
GARY_ZERO_HEALTH_CHECK_INTERVAL=30
GARY_ZERO_HEALTH_ALERT_THRESHOLD=3

# Profiling
GARY_ZERO_PROFILING_ENABLED=false
GARY_ZERO_PROFILING_SLOW_THRESHOLD=1.0
```

### Programmatic Configuration

```python
# Custom configuration
observability = create_observability_stack(
    service_name="custom-service",
    enable_system_metrics=True,
    enable_tracing=True,
    enable_health_monitoring=True,
    enable_profiling=False
)

# Configure components
metrics = observability["metrics"]
metrics.flush_interval = 30.0  # Custom flush interval

tracer = observability["tracer"] 
tracer.sample_rate = 0.1  # Sample 10% of traces

health = observability["health"]
health.check_interval = 15.0  # Check every 15 seconds
```

## 📊 Best Practices

### Metrics

1. **Use appropriate metric types** for your use case
2. **Add meaningful labels** but avoid high cardinality
3. **Set reasonable flush intervals** to balance performance and freshness
4. **Monitor metric growth** to prevent memory issues

### Tracing

1. **Use descriptive operation names** for easy identification
2. **Add relevant attributes** to spans for debugging
3. **Configure sampling** for high-traffic services
4. **Propagate context** across service boundaries

### Health Monitoring

1. **Mark critical dependencies** as critical checks
2. **Set appropriate timeouts** for health checks
3. **Implement graceful degradation** for non-critical failures
4. **Monitor health check performance** to avoid cascading failures

### Profiling

1. **Use profiling selectively** to minimize overhead
2. **Profile representative workloads** for accurate insights
3. **Analyze trends over time** rather than single measurements
4. **Act on recommendations** to improve performance

## 🔗 Integration Examples

See the complete integration example in `examples/observability_demo.py` for a comprehensive demonstration of all observability features working together in a realistic Gary-Zero application scenario.