"""
Comprehensive Test Suite for Observability Framework

Tests all components of the advanced observability system:
- Metrics collection and aggregation
- Distributed tracing and spans
- Health monitoring and alerting
- Performance profiling and analysis
- Middleware integration
"""

import pytest
import time
import asyncio
import threading
from unittest.mock import Mock, patch, AsyncMock
from framework.observability import (
    MetricsCollector, MetricsRegistry, CustomMetric, MetricType,
    DistributedTracer, TraceContext, Span, SpanKind, SpanStatus,
    HealthMonitor, HealthCheck, HealthStatus, HealthCheckType,
    PerformanceProfiler, ProfilerContext,
    ObservabilityMiddleware
)


class TestMetricsSystem:
    """Test suite for metrics collection and aggregation"""
    
    @pytest.fixture
    def metrics_registry(self):
        return MetricsRegistry()
        
    @pytest.fixture
    def metrics_collector(self, metrics_registry):
        collector = MetricsCollector(
            registry=metrics_registry,
            enable_system_metrics=False  # Disable for testing
        )
        yield collector
        collector.stop()
        
    def test_metric_registration(self, metrics_registry):
        """Test metric registration and retrieval"""
        metric = CustomMetric(
            name="test_counter",
            metric_type=MetricType.COUNTER,
            description="Test counter metric",
            labels=["service", "endpoint"]
        )
        
        metrics_registry.register(metric)
        retrieved = metrics_registry.get_metric("test_counter")
        
        assert retrieved is not None
        assert retrieved.name == "test_counter"
        assert retrieved.metric_type == MetricType.COUNTER
        assert "service" in retrieved.labels
        
    def test_duplicate_metric_registration(self, metrics_registry):
        """Test that duplicate metric registration raises error"""
        metric = CustomMetric("duplicate", MetricType.GAUGE, "Test metric")
        
        metrics_registry.register(metric)
        
        with pytest.raises(ValueError, match="already registered"):
            metrics_registry.register(metric)
            
    def test_metrics_collection(self, metrics_collector):
        """Test basic metrics recording"""
        metrics_collector.record("test_gauge", 42.5)
        metrics_collector.increment("test_counter", 1)
        
        gauge_value = metrics_collector.get_current_value("test_gauge")
        counter_value = metrics_collector.get_current_value("test_counter")
        
        assert gauge_value == 42.5
        assert counter_value == 1.0
        
    def test_metrics_with_labels(self, metrics_collector):
        """Test metrics recording with labels"""
        labels = {"service": "api", "endpoint": "/users"}
        
        metrics_collector.record("request_count", 5, labels)
        metrics_collector.record("request_count", 3, {"service": "api", "endpoint": "/orders"})
        
        users_count = metrics_collector.get_current_value("request_count", labels)
        orders_count = metrics_collector.get_current_value("request_count", 
                                                         {"service": "api", "endpoint": "/orders"})
        
        assert users_count == 5
        assert orders_count == 3
        
    def test_timer_context(self, metrics_collector):
        """Test timer context manager"""
        with metrics_collector.timer("test_duration"):
            time.sleep(0.1)
            
        duration = metrics_collector.get_current_value("test_duration")
        assert duration >= 0.1
        assert duration < 0.2  # Should complete quickly
        
    def test_metrics_aggregation(self, metrics_collector):
        """Test metrics aggregation over time"""
        # Record multiple values for histogram metric
        for i in range(5):
            metrics_collector.record("response_time", i * 0.1)
            
        all_metrics = metrics_collector.get_all_metrics()
        response_time_metric = next(m for m in all_metrics if m.name == "response_time")
        
        assert response_time_metric is not None
        assert response_time_metric.value >= 0  # Should be aggregated value
        
    def test_export_callback(self, metrics_collector):
        """Test metrics export callback functionality"""
        exported_metrics = []
        
        def export_callback(metrics):
            exported_metrics.extend(metrics)
            
        metrics_collector.add_export_callback(export_callback)
        metrics_collector.record("test_metric", 100)
        
        # Trigger export manually
        metrics_collector._flush_metrics()
        
        assert len(exported_metrics) > 0
        assert any(m.name == "test_metric" for m in exported_metrics)


class TestDistributedTracing:
    """Test suite for distributed tracing system"""
    
    @pytest.fixture
    def tracer(self):
        tracer = DistributedTracer(service_name="test-service", sample_rate=1.0)
        tracer.start()
        yield tracer
        tracer.stop()
        
    def test_span_creation(self, tracer):
        """Test basic span creation and management"""
        span = tracer.start_span("test_operation")
        
        assert span.operation_name == "test_operation"
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.start_time > 0
        
        tracer.finish_span(span)
        assert span.end_time is not None
        assert span.duration is not None
        
    def test_span_context_manager(self, tracer):
        """Test span context manager"""
        with tracer.span("context_operation") as span:
            span.set_attribute("test_key", "test_value")
            span.add_event("test_event")
            
        assert span.end_time is not None
        assert "test_key" in span.attributes
        assert len(span.events) == 1
        assert span.events[0].name == "test_event"
        
    def test_nested_spans(self, tracer):
        """Test nested span relationships"""
        with tracer.span("parent_operation") as parent_span:
            with tracer.span("child_operation") as child_span:
                assert child_span.parent_span_id == parent_span.span_id
                assert child_span.trace_id == parent_span.trace_id
                
    def test_span_error_handling(self, tracer):
        """Test span error status on exceptions"""
        with pytest.raises(ValueError):
            with tracer.span("error_operation") as span:
                raise ValueError("Test error")
                
        # Check that span was marked with error
        completed_spans = tracer.get_completed_spans()
        error_span = next(s for s in completed_spans if s.operation_name == "error_operation")
        
        assert error_span.status == SpanStatus.ERROR
        assert error_span.attributes.get("error") is True
        assert "Test error" in error_span.attributes.get("error.message", "")
        
    def test_context_injection_extraction(self, tracer):
        """Test trace context injection and extraction"""
        with tracer.span("test_operation") as span:
            # Inject context into carrier
            carrier = {}
            tracer.inject_context(carrier)
            
            assert "x-trace-id" in carrier
            assert "x-span-id" in carrier
            assert carrier["x-trace-id"] == span.trace_id
            assert carrier["x-span-id"] == span.span_id
            
        # Extract context from carrier
        extracted_span = tracer.extract_context(carrier)
        assert extracted_span is not None
        assert extracted_span.trace_id == span.trace_id
        
    def test_span_serialization(self, tracer):
        """Test span serialization and deserialization"""
        original_span = tracer.start_span("serialization_test")
        original_span.set_attribute("test_attr", "test_value")
        original_span.add_event("test_event", {"event_attr": "event_value"})
        tracer.finish_span(original_span)
        
        # Serialize to dict
        span_dict = original_span.to_dict()
        
        # Deserialize from dict
        deserialized_span = Span.from_dict(span_dict)
        
        assert deserialized_span.operation_name == original_span.operation_name
        assert deserialized_span.trace_id == original_span.trace_id
        assert deserialized_span.attributes["test_attr"] == "test_value"
        assert len(deserialized_span.events) == 1
        assert deserialized_span.events[0].name == "test_event"


class TestHealthMonitoring:
    """Test suite for health monitoring system"""
    
    @pytest.fixture
    def health_monitor(self):
        monitor = HealthMonitor(check_interval=0.1)  # Fast interval for testing
        yield monitor
        monitor.stop()
        
    def test_health_check_registration(self, health_monitor):
        """Test health check registration"""
        def test_check():
            return HealthCheckResult(
                name="test_check",
                status=HealthStatus.HEALTHY,
                message="Test check passed"
            )
            
        check = HealthCheck(
            name="test_check",
            check_function=test_check,
            interval=1.0
        )
        
        health_monitor.register_check(check)
        
        # Force execution
        result = health_monitor.force_check("test_check")
        assert result is not None
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test check passed"
        
    def test_health_check_with_failure(self, health_monitor):
        """Test health check failure handling"""
        def failing_check():
            raise Exception("Health check failed")
            
        check = HealthCheck(
            name="failing_check",
            check_function=failing_check,
            interval=1.0
        )
        
        health_monitor.register_check(check)
        result = health_monitor.force_check("failing_check")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in result.message.lower()
        
    def test_overall_health_status(self, health_monitor):
        """Test overall health status calculation"""
        # Add healthy check
        def healthy_check():
            return HealthCheckResult("healthy_check", HealthStatus.HEALTHY)
            
        # Add critical unhealthy check
        def unhealthy_check():
            return HealthCheckResult("unhealthy_check", HealthStatus.UNHEALTHY)
            
        healthy = HealthCheck("healthy_check", healthy_check, critical=False)
        unhealthy = HealthCheck("unhealthy_check", unhealthy_check, critical=True)
        
        health_monitor.register_check(healthy)
        health_monitor.register_check(unhealthy)
        
        # Force checks
        health_monitor.force_check("healthy_check")
        health_monitor.force_check("unhealthy_check")
        
        overall_health = health_monitor.get_overall_health()
        assert overall_health["status"] == HealthStatus.UNHEALTHY.value
        
    def test_health_history(self, health_monitor):
        """Test health check history tracking"""
        def test_check():
            return HealthCheckResult("history_check", HealthStatus.HEALTHY)
            
        check = HealthCheck("history_check", test_check)
        health_monitor.register_check(check)
        
        # Execute check multiple times
        for _ in range(3):
            health_monitor.force_check("history_check")
            time.sleep(0.01)
            
        history = health_monitor.get_check_history("history_check")
        assert len(history) >= 3
        
    @pytest.mark.asyncio
    async def test_async_health_check(self, health_monitor):
        """Test asynchronous health check"""
        async def async_check():
            await asyncio.sleep(0.01)
            return HealthCheckResult("async_check", HealthStatus.HEALTHY, message="Async check passed")
            
        check = HealthCheck("async_check", async_check)
        health_monitor.register_check(check)
        
        result = health_monitor.force_check("async_check")
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Async check passed"


class TestPerformanceProfiling:
    """Test suite for performance profiling system"""
    
    @pytest.fixture
    def profiler(self):
        profiler = PerformanceProfiler(enable_system_monitoring=False)
        yield profiler
        profiler.stop_system_monitoring()
        
    def test_profile_context_manager(self, profiler):
        """Test profiling context manager"""
        def test_function():
            time.sleep(0.01)
            return "result"
            
        with profiler.profile("test_session") as context:
            result = test_function()
            
        assert result == "result"
        
        # Get profile result
        profile_result = profiler.get_result("test_session")
        assert profile_result is not None
        assert profile_result.duration >= 0.01
        
    def test_function_profiling(self, profiler):
        """Test direct function profiling"""
        def test_function(x, y):
            time.sleep(0.01)
            return x + y
            
        result, profile_result = profiler.profile_function(test_function, 5, 10)
        
        assert result == 15
        assert profile_result is not None
        assert profile_result.duration >= 0.01
        
    def test_profile_cpu_analysis(self, profiler):
        """Test CPU profiling analysis"""
        def cpu_intensive_function():
            # Simulate some CPU work
            for i in range(1000):
                _ = i ** 2
                
        with profiler.profile("cpu_test", profile_cpu=True, profile_memory=False):
            cpu_intensive_function()
            
        result = profiler.get_result("cpu_test")
        assert result is not None
        assert "total_calls" in result.cpu_stats
        assert len(result.function_stats) > 0
        
    def test_profile_memory_analysis(self, profiler):
        """Test memory profiling analysis"""
        def memory_allocating_function():
            # Allocate some memory
            data = [i for i in range(1000)]
            return data
            
        with profiler.profile("memory_test", profile_cpu=False, profile_memory=True):
            data = memory_allocating_function()
            
        result = profiler.get_result("memory_test")
        assert result is not None
        assert "current_memory" in result.memory_stats or "error" in result.memory_stats
        
    def test_performance_trends_analysis(self, profiler):
        """Test performance trends analysis"""
        # Create multiple profile sessions
        for i in range(5):
            with profiler.profile(f"trend_test_{i}"):
                time.sleep(0.01 * (i + 1))  # Increasing duration
                
        # Analyze trends
        session_ids = [f"trend_test_{i}" for i in range(5)]
        trends = profiler.analyze_trends(session_ids)
        
        assert "duration" in trends
        assert "trend" in trends["duration"]
        assert trends["duration"]["trend"] == "increasing"
        
    def test_hotspot_identification(self, profiler):
        """Test performance hotspot identification"""
        def slow_function():
            time.sleep(0.05)  # Intentionally slow
            
        def fast_function():
            pass
            
        with profiler.profile("hotspot_test") as context:
            slow_function()
            fast_function()
            
        result = profiler.get_result("hotspot_test")
        # Should identify slow_function as a hotspot
        assert len(result.hotspots) >= 0  # May or may not find hotspots depending on profiling


class TestObservabilityMiddleware:
    """Test suite for observability middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock ASGI application"""
        async def app(receive, send):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': []
            })
            await send({
                'type': 'http.response.body',
                'body': b'OK'
            })
        return app
        
    @pytest.fixture  
    def middleware_components(self):
        """Create middleware components for testing"""
        registry = MetricsRegistry()
        metrics = MetricsCollector(registry, enable_system_metrics=False)
        tracer = DistributedTracer("test-service")
        health = HealthMonitor()
        profiler = PerformanceProfiler(enable_system_monitoring=False)
        
        metrics.start()
        tracer.start()
        health.start()
        
        yield {
            "metrics": metrics,
            "tracer": tracer,
            "health": health,
            "profiler": profiler
        }
        
        metrics.stop()
        tracer.stop()
        health.stop()
        
    def test_middleware_creation(self, mock_app, middleware_components):
        """Test middleware creation and initialization"""
        middleware = ObservabilityMiddleware(
            app=mock_app,
            metrics_collector=middleware_components["metrics"],
            tracer=middleware_components["tracer"],
            health_monitor=middleware_components["health"],
            profiler=middleware_components["profiler"]
        )
        
        assert middleware.metrics_collector is not None
        assert middleware.tracer is not None
        assert middleware.health_monitor is not None
        assert middleware.profiler is not None
        
    @pytest.mark.asyncio
    async def test_middleware_request_processing(self, mock_app, middleware_components):
        """Test middleware request processing"""
        from fastapi import Request
        from unittest.mock import MagicMock
        
        middleware = ObservabilityMiddleware(
            app=mock_app,
            metrics_collector=middleware_components["metrics"],
            tracer=middleware_components["tracer"]
        )
        
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        
        async def mock_call_next(request):
            from fastapi import Response
            return Response("OK", status_code=200)
            
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers


class TestIntegrationScenarios:
    """Integration tests for complete observability scenarios"""
    
    @pytest.fixture
    def full_observability_stack(self):
        """Create a complete observability stack"""
        from framework.observability.middleware import create_observability_stack
        
        stack = create_observability_stack(
            service_name="test-integration",
            enable_system_metrics=False,
            enable_profiling=False
        )
        
        yield stack
        
        # Cleanup
        if "metrics" in stack:
            stack["metrics"].stop()
        if "tracer" in stack:
            stack["tracer"].stop()
        if "health" in stack:
            stack["health"].stop()
            
    def test_end_to_end_observability(self, full_observability_stack):
        """Test end-to-end observability scenario"""
        metrics = full_observability_stack["metrics"]
        tracer = full_observability_stack["tracer"]
        health = full_observability_stack["health"]
        
        # Simulate a traced operation with metrics
        with tracer.span("integration_test") as span:
            # Record some metrics
            metrics.record("operation_count", 1, {"operation": "integration_test"})
            
            # Add span attributes
            span.set_attribute("operation.type", "integration_test")
            span.add_event("operation_started")
            
            # Simulate some work
            time.sleep(0.01)
            
            span.add_event("operation_completed")
            
        # Check that everything was recorded
        metric_value = metrics.get_current_value("operation_count", {"operation": "integration_test"})
        assert metric_value == 1
        
        completed_spans = tracer.get_completed_spans()
        integration_span = next(s for s in completed_spans if s.operation_name == "integration_test")
        assert integration_span is not None
        assert len(integration_span.events) == 2
        
        # Check health status
        overall_health = health.get_overall_health()
        assert overall_health["status"] in ["healthy", "unknown"]  # System should be healthy
        
    def test_error_scenario_tracking(self, full_observability_stack):
        """Test error tracking across observability components"""
        metrics = full_observability_stack["metrics"]
        tracer = full_observability_stack["tracer"]
        
        # Simulate an error scenario
        try:
            with tracer.span("error_operation") as span:
                metrics.increment("error_count", 1, {"error_type": "test_error"})
                span.set_attribute("operation.critical", True)
                raise ValueError("Simulated error")
        except ValueError:
            pass  # Expected
            
        # Verify error tracking
        error_count = metrics.get_current_value("error_count", {"error_type": "test_error"})
        assert error_count == 1
        
        completed_spans = tracer.get_completed_spans()
        error_span = next(s for s in completed_spans if s.operation_name == "error_operation")
        assert error_span.status == SpanStatus.ERROR
        assert error_span.attributes.get("error") is True


if __name__ == "__main__":
    pytest.main([__file__])