"""
Observability Middleware for HTTP and Application Integration

Provides transparent observability integration with:
- Automatic request/response metrics
- Distributed tracing propagation
- Health check endpoints
- Performance monitoring
- Error tracking and alerting
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional, Awaitable
import logging

# Optional dependency handling
try:
    from fastapi import Request, Response, HTTPException
    from fastapi.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    # Create dummy classes for type hints
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app
    class Request:
        pass
    class Response:
        pass
    class HTTPException:
        pass

from .metrics import MetricsCollector
from .tracing import DistributedTracer, SpanKind, SpanStatus
from .health import HealthMonitor
from .profiling import PerformanceProfiler


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Comprehensive observability middleware for FastAPI applications"""
    
    def __init__(self,
                 app,
                 metrics_collector = None,
                 tracer = None,
                 health_monitor = None,
                 profiler = None,
                 enable_detailed_profiling: bool = False,
                 profile_slow_requests: bool = True,
                 slow_request_threshold: float = 1.0):
        
        if not HAS_FASTAPI:
            raise ImportError("FastAPI is required for ObservabilityMiddleware")
            
        super().__init__(app)
        
        self.metrics_collector = metrics_collector
        self.tracer = tracer
        self.health_monitor = health_monitor
        self.profiler = profiler
        self.enable_detailed_profiling = enable_detailed_profiling
        self.profile_slow_requests = profile_slow_requests
        self.slow_request_threshold = slow_request_threshold
        
        # Request tracking
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request with full observability"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract basic request info
        method = request.method
        url_path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")
        client_ip = self._get_client_ip(request)
        
        # Start distributed tracing
        span = None
        if self.tracer:
            # Extract parent context from headers
            parent_span = self.tracer.extract_context(dict(request.headers))
            
            span = self.tracer.start_span(
                operation_name=f"{method} {url_path}",
                parent_span=parent_span,
                kind=SpanKind.SERVER,
                attributes={
                    "http.method": method,
                    "http.url": str(request.url),
                    "http.user_agent": user_agent,
                    "client.ip": client_ip,
                    "request.id": request_id
                }
            )
            
            # Set span as current context
            if span:
                self.tracer.context.set_current_span(span)
                
        # Start profiling if enabled
        profiler_context = None
        if (self.profiler and 
            (self.enable_detailed_profiling or 
             (self.profile_slow_requests and self._should_profile_request(request)))):
            profiler_context = self.profiler.profile(
                session_id=f"request_{request_id}",
                profile_cpu=True,
                profile_memory=True
            )
            profiler_context.__enter__()
            
        # Track active request
        self._active_requests[request_id] = {
            "method": method,
            "path": url_path,
            "start_time": start_time,
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        # Record request start metrics
        if self.metrics_collector:
            self.metrics_collector.increment("request_count", 1, {
                "method": method,
                "endpoint": url_path,
                "status": "started"
            })
            self.metrics_collector.record("agent_active_sessions", len(self._active_requests))
            
        response = None
        status_code = 500
        error_occurred = False
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Check for error status codes
            if status_code >= 400:
                error_occurred = True
                
        except HTTPException as e:
            status_code = e.status_code
            error_occurred = True
            
            # Create error response
            response = Response(
                content=f"HTTP {e.status_code}: {e.detail}",
                status_code=e.status_code,
                headers=e.headers
            )
            
            # Update span with error
            if span:
                span.set_status(SpanStatus.ERROR, f"HTTP {e.status_code}: {e.detail}")
                span.set_attribute("error", True)
                span.set_attribute("error.type", "HTTPException")
                span.set_attribute("error.message", e.detail)
                
        except Exception as e:
            status_code = 500
            error_occurred = True
            
            # Create error response
            response = Response(
                content="Internal Server Error",
                status_code=500
            )
            
            # Update span with error
            if span:
                span.set_status(SpanStatus.ERROR, str(e))
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                
            # Log error
            self.logger.error(f"Request {request_id} failed: {e}", exc_info=True)
            
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Finalize span
            if span:
                span.set_attribute("http.status_code", status_code)
                span.set_attribute("request.duration", duration)
                self.tracer.finish_span(span)
                self.tracer.context.set_current_span(None)
                
            # Finalize profiling
            if profiler_context:
                try:
                    profiler_context.__exit__(None, None, None)
                except Exception as e:
                    self.logger.warning(f"Error finalizing profiler: {e}")
                    
            # Record final metrics
            if self.metrics_collector:
                # Request completion
                self.metrics_collector.increment("request_count", 1, {
                    "method": method,
                    "endpoint": url_path,
                    "status": str(status_code)
                })
                
                # Request duration
                self.metrics_collector.record("request_duration", duration, {
                    "method": method,
                    "endpoint": url_path
                })
                
                # Error metrics
                if error_occurred:
                    self.metrics_collector.increment("error_count", 1, {
                        "error_type": "http_error",
                        "component": "middleware"
                    })
                    
                # Update active sessions
                self.metrics_collector.record("agent_active_sessions", len(self._active_requests) - 1)
                
            # Remove from active requests
            self._active_requests.pop(request_id, None)
            
            # Add observability headers to response
            if response:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                if span:
                    response.headers["X-Trace-ID"] = span.trace_id
                    response.headers["X-Span-ID"] = span.span_id
                    
        return response
        
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
            
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        # Fall back to direct client
        if hasattr(request.client, "host"):
            return request.client.host
            
        return "unknown"
        
    def _should_profile_request(self, request: Request) -> bool:
        """Determine if this request should be profiled"""
        # Skip profiling for health checks and static assets
        skip_patterns = ["/health", "/metrics", "/static", "/favicon.ico"]
        path = request.url.path
        
        for pattern in skip_patterns:
            if path.startswith(pattern):
                return False
                
        return True
        
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active requests"""
        return dict(self._active_requests)


class HealthCheckEndpoints:
    """Health check endpoints for observability"""
    
    def __init__(self,
                 health_monitor: HealthMonitor,
                 metrics_collector: Optional[MetricsCollector] = None):
        self.health_monitor = health_monitor
        self.metrics_collector = metrics_collector
        
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check endpoint"""
        return self.health_monitor.get_overall_health()
        
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness check for Kubernetes"""
        health = self.health_monitor.get_overall_health()
        
        # Consider system ready if not unhealthy
        if health["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail="Service not ready")
            
        return {"status": "ready", "timestamp": time.time()}
        
    async def liveness_check(self) -> Dict[str, Any]:
        """Liveness check for Kubernetes"""
        # Simple liveness check - service is alive if it can respond
        return {"status": "alive", "timestamp": time.time()}
        
    async def metrics_endpoint(self) -> Dict[str, Any]:
        """Metrics endpoint for Prometheus-style scraping"""
        if not self.metrics_collector:
            raise HTTPException(status_code=404, detail="Metrics not enabled")
            
        metrics = self.metrics_collector.get_all_metrics()
        
        # Convert to Prometheus-style format
        prometheus_metrics = []
        for metric in metrics:
            labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
            if labels_str:
                prometheus_metrics.append(f"{metric.name}{{{labels_str}}} {metric.value}")
            else:
                prometheus_metrics.append(f"{metric.name} {metric.value}")
                
        return {
            "metrics_count": len(metrics),
            "prometheus_format": "\n".join(prometheus_metrics),
            "timestamp": time.time()
        }


def create_observability_middleware(
    metrics_collector = None,
    tracer = None,
    health_monitor = None,
    profiler = None,
    **kwargs
):
    """Factory function to create observability middleware"""
    
    if not HAS_FASTAPI:
        print("⚠️ FastAPI not available - middleware creation skipped")
        return None
    
    def middleware_factory(app):
        return ObservabilityMiddleware(
            app=app,
            metrics_collector=metrics_collector,
            tracer=tracer,
            health_monitor=health_monitor,
            profiler=profiler,
            **kwargs
        )
        
    return middleware_factory


# Utility functions for observability setup
def setup_observability_logging():
    """Configure logging for observability components"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set levels for observability components
    logging.getLogger("observability.metrics").setLevel(logging.WARNING)
    logging.getLogger("observability.tracing").setLevel(logging.WARNING)
    logging.getLogger("observability.health").setLevel(logging.INFO)
    logging.getLogger("observability.profiling").setLevel(logging.WARNING)


def create_observability_stack(
    service_name: str = "gary-zero",
    enable_system_metrics: bool = True,
    enable_tracing: bool = True,
    enable_health_monitoring: bool = True,
    enable_profiling: bool = False
) -> Dict[str, Any]:
    """Create a complete observability stack"""
    
    components = {}
    
    # Metrics collection
    if enable_system_metrics:
        from .metrics import MetricsCollector, MetricsRegistry
        registry = MetricsRegistry()
        collector = MetricsCollector(
            registry=registry,
            enable_system_metrics=True
        )
        collector.start()
        components["metrics"] = collector
        components["metrics_registry"] = registry
        
    # Distributed tracing
    if enable_tracing:
        from .tracing import DistributedTracer, set_global_tracer
        tracer = DistributedTracer(service_name=service_name)
        tracer.start()
        set_global_tracer(tracer)
        components["tracer"] = tracer
        
    # Health monitoring
    if enable_health_monitoring:
        from .health import HealthMonitor
        health_monitor = HealthMonitor()
        health_monitor.start()
        components["health"] = health_monitor
        
    # Performance profiling
    if enable_profiling:
        from .profiling import PerformanceProfiler, set_global_profiler
        profiler = PerformanceProfiler()
        profiler.start_system_monitoring()
        set_global_profiler(profiler)
        components["profiler"] = profiler
        
    # Create middleware
    components["middleware"] = create_observability_middleware(
        metrics_collector=components.get("metrics"),
        tracer=components.get("tracer"),
        health_monitor=components.get("health"),
        profiler=components.get("profiler")
    )
    
    # Health check endpoints
    if "health" in components:
        components["health_endpoints"] = HealthCheckEndpoints(
            health_monitor=components["health"],
            metrics_collector=components.get("metrics")
        )
        
    return components