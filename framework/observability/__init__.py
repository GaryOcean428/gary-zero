"""
Advanced Observability and Monitoring Framework

This module provides comprehensive observability capabilities including:
- Metrics collection and aggregation
- Distributed tracing and spans
- Health monitoring and alerting
- Performance profiling and analysis
- Custom observability hooks and middleware
"""

from .metrics import MetricsCollector, MetricsRegistry, CustomMetric
from .tracing import DistributedTracer, TraceContext, Span
from .health import HealthMonitor, HealthCheck, HealthStatus
from .profiling import PerformanceProfiler, ProfilerContext

# Optional middleware import
try:
    from .middleware import ObservabilityMiddleware
    __all__ = [
        "MetricsCollector",
        "MetricsRegistry", 
        "CustomMetric",
        "DistributedTracer",
        "TraceContext",
        "Span",
        "HealthMonitor",
        "HealthCheck",
        "HealthStatus",
        "PerformanceProfiler",
        "ProfilerContext",
        "ObservabilityMiddleware",
    ]
except ImportError:
    __all__ = [
        "MetricsCollector",
        "MetricsRegistry", 
        "CustomMetric",
        "DistributedTracer",
        "TraceContext",
        "Span",
        "HealthMonitor",
        "HealthCheck",
        "HealthStatus",
        "PerformanceProfiler",
        "ProfilerContext",
    ]