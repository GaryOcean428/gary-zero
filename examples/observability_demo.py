"""
Advanced Observability Integration Example

Demonstrates how to integrate and use the complete observability framework
in a Gary-Zero application with:
- Comprehensive metrics collection
- Distributed tracing
- Health monitoring
- Performance profiling
- FastAPI middleware integration
"""

import asyncio
import time
from fastapi import FastAPI, HTTPException
from framework.observability import (
    MetricsCollector, MetricsRegistry, CustomMetric, MetricType,
    DistributedTracer, HealthMonitor, PerformanceProfiler,
    create_observability_stack
)
from framework.observability.middleware import ObservabilityMiddleware, HealthCheckEndpoints
from framework.observability.health import create_database_check, create_redis_check, create_http_check


class GaryZeroObservabilityExample:
    """Example integration of observability components"""
    
    def __init__(self):
        self.app = FastAPI(title="Gary-Zero Observability Example")
        self.observability_stack = None
        
    async def setup_observability(self):
        """Setup comprehensive observability stack"""
        print("🔧 Setting up observability stack...")
        
        # Create complete observability stack
        self.observability_stack = create_observability_stack(
            service_name="gary-zero-example",
            enable_system_metrics=True,
            enable_tracing=True,
            enable_health_monitoring=True,
            enable_profiling=True
        )
        
        # Register custom metrics
        await self._register_custom_metrics()
        
        # Setup health checks
        await self._setup_health_checks()
        
        # Add middleware
        self.app.add_middleware(
            ObservabilityMiddleware,
            metrics_collector=self.observability_stack["metrics"],
            tracer=self.observability_stack["tracer"],
            health_monitor=self.observability_stack["health"],
            profiler=self.observability_stack["profiler"],
            enable_detailed_profiling=True
        )
        
        # Add health endpoints
        self._setup_health_endpoints()
        
        print("✅ Observability stack ready!")
        
    async def _register_custom_metrics(self):
        """Register application-specific metrics"""
        registry = self.observability_stack["metrics_registry"]
        
        # Agent-specific metrics
        custom_metrics = [
            CustomMetric(
                name="agent_conversations_total",
                metric_type=MetricType.COUNTER,
                description="Total number of agent conversations",
                labels=["agent_type", "outcome"]
            ),
            CustomMetric(
                name="agent_response_quality",
                metric_type=MetricType.HISTOGRAM,
                description="Agent response quality score",
                labels=["agent_type"],
                buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
            ),
            CustomMetric(
                name="tool_execution_duration",
                metric_type=MetricType.TIMER,
                description="Time taken to execute tools",
                labels=["tool_name", "status"]
            ),
            CustomMetric(
                name="model_inference_tokens",
                metric_type=MetricType.COUNTER,
                description="Number of tokens processed",
                labels=["model", "provider", "direction"]
            )
        ]
        
        for metric in custom_metrics:
            try:
                registry.register(metric)
                print(f"📊 Registered metric: {metric.name}")
            except ValueError as e:
                print(f"⚠️ Metric registration warning: {e}")
                
    async def _setup_health_checks(self):
        """Setup comprehensive health checks"""
        health_monitor = self.observability_stack["health"]
        
        # Database health check (if using database)
        try:
            db_check = create_database_check(
                name="database_connectivity",
                connection_string="sqlite:///./example.db"  # Example SQLite
            )
            health_monitor.register_check(db_check)
            print("💾 Database health check registered")
        except Exception as e:
            print(f"⚠️ Database health check setup failed: {e}")
            
        # Redis health check (if using Redis)
        try:
            redis_check = create_redis_check(
                name="redis_connectivity",
                redis_url="redis://localhost:6379"
            )
            health_monitor.register_check(redis_check)
            print("🔴 Redis health check registered")
        except Exception as e:
            print(f"⚠️ Redis health check setup failed: {e}")
            
        # External API health check
        api_check = create_http_check(
            name="openai_api",
            url="https://api.openai.com/v1/models",
            timeout=5.0
        )
        health_monitor.register_check(api_check)
        print("🌐 OpenAI API health check registered")
        
    def _setup_health_endpoints(self):
        """Setup health check endpoints"""
        health_endpoints = HealthCheckEndpoints(
            health_monitor=self.observability_stack["health"],
            metrics_collector=self.observability_stack["metrics"]
        )
        
        # Add health endpoints
        self.app.get("/health")(health_endpoints.health_check)
        self.app.get("/health/ready")(health_endpoints.readiness_check)
        self.app.get("/health/live")(health_endpoints.liveness_check)
        self.app.get("/metrics")(health_endpoints.metrics_endpoint)
        
        print("🏥 Health endpoints registered")
        
    async def simulate_agent_conversation(self, agent_type: str = "chat"):
        """Simulate an agent conversation with full observability"""
        tracer = self.observability_stack["tracer"]
        metrics = self.observability_stack["metrics"]
        profiler = self.observability_stack["profiler"]
        
        # Start distributed trace
        with tracer.span("agent_conversation", attributes={
            "agent.type": agent_type,
            "conversation.id": f"conv_{int(time.time())}"
        }) as conversation_span:
            
            # Simulate user input processing
            with tracer.span("process_user_input") as input_span:
                await self._simulate_input_processing(input_span, metrics)
                
            # Simulate model inference
            with tracer.span("model_inference") as inference_span:
                with profiler.profile(f"inference_{agent_type}"):
                    response_quality = await self._simulate_model_inference(
                        inference_span, metrics, agent_type
                    )
                    
            # Simulate tool execution
            with tracer.span("tool_execution") as tool_span:
                await self._simulate_tool_execution(tool_span, metrics)
                
            # Record conversation metrics
            metrics.increment("agent_conversations_total", 1, {
                "agent_type": agent_type,
                "outcome": "success"
            })
            
            metrics.record("agent_response_quality", response_quality, {
                "agent_type": agent_type
            })
            
            conversation_span.set_attribute("conversation.quality", response_quality)
            conversation_span.set_attribute("conversation.outcome", "success")
            
        return {
            "status": "success",
            "agent_type": agent_type,
            "quality_score": response_quality,
            "trace_id": conversation_span.trace_id
        }
        
    async def _simulate_input_processing(self, span, metrics):
        """Simulate input processing with observability"""
        span.add_event("input_received")
        
        # Simulate validation and sanitization
        await asyncio.sleep(0.01)  # Simulate processing time
        
        span.add_event("input_validated")
        span.set_attribute("input.length", 150)  # Simulated input length
        
        # Record input metrics
        metrics.increment("request_count", 1, {
            "method": "POST",
            "endpoint": "/chat",
            "status": "200"
        })
        
    async def _simulate_model_inference(self, span, metrics, agent_type):
        """Simulate model inference with detailed observability"""
        model_name = "gpt-4" if agent_type == "advanced" else "gpt-3.5-turbo"
        provider = "openai"
        
        span.set_attribute("model.name", model_name)
        span.set_attribute("model.provider", provider)
        span.add_event("inference_started")
        
        # Simulate inference time (different for different models)
        inference_time = 0.5 if model_name == "gpt-4" else 0.2
        await asyncio.sleep(inference_time)
        
        # Simulate token usage
        input_tokens = 150
        output_tokens = 200
        
        # Record model metrics
        metrics.increment("model_inference_count", 1, {
            "model": model_name,
            "provider": provider
        })
        
        metrics.record("model_inference_duration", inference_time, {
            "model": model_name,
            "provider": provider
        })
        
        metrics.increment("model_inference_tokens", input_tokens, {
            "model": model_name,
            "provider": provider,
            "direction": "input"
        })
        
        metrics.increment("model_inference_tokens", output_tokens, {
            "model": model_name,
            "provider": provider,
            "direction": "output"
        })
        
        span.set_attribute("tokens.input", input_tokens)
        span.set_attribute("tokens.output", output_tokens)
        span.set_attribute("tokens.total", input_tokens + output_tokens)
        span.add_event("inference_completed")
        
        # Simulate response quality (random but realistic)
        import random
        quality_score = random.uniform(0.7, 0.95)
        return quality_score
        
    async def _simulate_tool_execution(self, span, metrics):
        """Simulate tool execution with observability"""
        tools = ["web_search", "file_read", "calculation"]
        
        for tool_name in tools:
            with span.tracer.span(f"execute_{tool_name}") as tool_span:
                tool_span.set_attribute("tool.name", tool_name)
                tool_span.add_event("tool_started")
                
                # Simulate tool execution time
                execution_time = random.uniform(0.1, 0.3)
                await asyncio.sleep(execution_time)
                
                # Record tool metrics
                metrics.record("tool_execution_duration", execution_time, {
                    "tool_name": tool_name,
                    "status": "success"
                })
                
                tool_span.set_attribute("tool.duration", execution_time)
                tool_span.add_event("tool_completed")
                
    async def run_demonstration(self):
        """Run a comprehensive observability demonstration"""
        print("🚀 Starting Gary-Zero Observability Demonstration")
        print("=" * 60)
        
        # Setup observability
        await self.setup_observability()
        
        print("\n📈 Running simulated agent conversations...")
        
        # Simulate multiple conversations with different agent types
        conversation_results = []
        
        for i in range(5):
            agent_type = "advanced" if i % 2 == 0 else "chat"
            
            print(f"🤖 Simulating conversation {i+1} with {agent_type} agent...")
            
            try:
                result = await self.simulate_agent_conversation(agent_type)
                conversation_results.append(result)
                print(f"   ✅ Success - Quality: {result['quality_score']:.3f}, Trace: {result['trace_id'][:8]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
            # Brief pause between conversations
            await asyncio.sleep(0.1)
            
        print(f"\n📊 Demonstration completed - {len(conversation_results)} conversations processed")
        
        # Display metrics summary
        await self._display_metrics_summary()
        
        # Display tracing summary
        await self._display_tracing_summary()
        
        # Display health summary
        await self._display_health_summary()
        
        return conversation_results
        
    async def _display_metrics_summary(self):
        """Display metrics summary"""
        print("\n📊 METRICS SUMMARY")
        print("-" * 30)
        
        metrics = self.observability_stack["metrics"]
        all_metrics = metrics.get_all_metrics()
        
        # Group metrics by name
        metric_groups = {}
        for metric in all_metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
            
        for name, metric_list in metric_groups.items():
            if "agent" in name or "model" in name:  # Focus on our custom metrics
                total_value = sum(m.value for m in metric_list)
                print(f"  {name}: {total_value}")
                
    async def _display_tracing_summary(self):
        """Display tracing summary"""
        print("\n🔍 TRACING SUMMARY")
        print("-" * 30)
        
        tracer = self.observability_stack["tracer"]
        completed_spans = tracer.get_completed_spans()
        
        # Count spans by operation
        span_counts = {}
        total_duration = 0
        
        for span in completed_spans:
            operation = span.operation_name
            span_counts[operation] = span_counts.get(operation, 0) + 1
            if span.duration:
                total_duration += span.duration
                
        print(f"  Total spans: {len(completed_spans)}")
        print(f"  Total duration: {total_duration:.3f}s")
        print("  Top operations:")
        for op, count in sorted(span_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {op}: {count} spans")
            
    async def _display_health_summary(self):
        """Display health summary"""
        print("\n🏥 HEALTH SUMMARY")
        print("-" * 30)
        
        health = self.observability_stack["health"]
        overall_health = health.get_overall_health()
        
        print(f"  Overall status: {overall_health['status']}")
        print(f"  Total checks: {overall_health['checks']['total']}")
        print(f"  Healthy checks: {overall_health['checks']['healthy']}")
        
        if overall_health['checks']['unhealthy'] > 0:
            print(f"  Unhealthy checks: {overall_health['checks']['unhealthy']}")
            
    async def cleanup(self):
        """Cleanup observability components"""
        print("\n🧹 Cleaning up observability stack...")
        
        if self.observability_stack:
            if "metrics" in self.observability_stack:
                self.observability_stack["metrics"].stop()
            if "tracer" in self.observability_stack:
                self.observability_stack["tracer"].stop()
            if "health" in self.observability_stack:
                self.observability_stack["health"].stop()
            if "profiler" in self.observability_stack:
                self.observability_stack["profiler"].stop_system_monitoring()
                
        print("✅ Cleanup completed")


# FastAPI endpoints for manual testing
async def create_demo_app():
    """Create demo FastAPI app with observability"""
    demo = GaryZeroObservabilityExample()
    await demo.setup_observability()
    
    @demo.app.post("/chat")
    async def chat_endpoint(message: dict):
        """Chat endpoint with observability"""
        agent_type = message.get("agent_type", "chat")
        result = await demo.simulate_agent_conversation(agent_type)
        return result
        
    @demo.app.get("/demo")
    async def run_demo():
        """Run the full demonstration"""
        results = await demo.run_demonstration()
        return {"status": "completed", "conversations": len(results)}
        
    @demo.app.get("/")
    async def root():
        return {
            "message": "Gary-Zero Observability Demo",
            "endpoints": [
                "/health", "/health/ready", "/health/live", 
                "/metrics", "/chat", "/demo"
            ]
        }
        
    return demo.app


# CLI demonstration
async def main():
    """Main demonstration function"""
    import random
    random.seed(42)  # For reproducible demo
    
    demo = GaryZeroObservabilityExample()
    
    try:
        results = await demo.run_demonstration()
        
        print(f"\n🎉 Demonstration completed successfully!")
        print(f"   Processed {len(results)} conversations")
        print(f"   Average quality: {sum(r['quality_score'] for r in results) / len(results):.3f}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("🔬 Gary-Zero Advanced Observability Framework")
    print("Demonstrating enterprise-grade monitoring and tracing")
    print("=" * 60)
    
    asyncio.run(main())