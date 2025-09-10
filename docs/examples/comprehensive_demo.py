"""
Complete example demonstrating the Gary-Zero framework capabilities.

This example shows:
1. Setting up the framework with dependency injection
2. Creating and managing agents
3. Processing messages with security
4. Using the event system
5. Performance monitoring and caching
6. Error handling and validation
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Framework imports
from framework.container.enhanced_container import get_enhanced_container, ServiceLifetime
from framework.domain.services import (
    AgentOrchestrationService,
    MessageProcessingService,
    ToolExecutionService
)
from framework.domain.entities import Agent, Message, Tool
from framework.domain.events import get_event_bus, AgentCreatedEvent, MessageProcessedEvent
from framework.domain.value_objects import ModelConfiguration, SecurityContext, ToolParameters
from framework.security.enhanced_rate_limiter import create_rate_limiter
from framework.security.enhanced_sanitizer import sanitize_and_validate_input
from framework.performance.caching.multi_level_cache import create_cache_hierarchy, cached

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveExample:
    """Comprehensive example of Gary-Zero framework usage."""
    
    def __init__(self):
        self.container = get_enhanced_container()
        self.event_bus = get_event_bus()
        self.cache = None
        self.rate_limiter = None
        
    async def setup_framework(self):
        """Initialize the framework components."""
        logger.info("🚀 Setting up Gary-Zero framework...")
        
        # Create cache hierarchy
        self.cache = create_cache_hierarchy()
        
        # Create rate limiter
        self.rate_limiter = create_rate_limiter(
            requests_per_minute=30,
            requests_per_hour=500,
            burst_limit=5
        )
        
        # Register services with dependency injection
        self.container.register_singleton("event_bus", self.event_bus)
        self.container.register_singleton("cache", self.cache)
        self.container.register_singleton("rate_limiter", self.rate_limiter)
        
        # Register domain services
        self.container.register_transient(
            "agent_orchestrator", 
            AgentOrchestrationService,
            AgentOrchestrationService
        )
        self.container.register_transient(
            "message_processor", 
            MessageProcessingService,
            MessageProcessingService
        )
        self.container.register_transient(
            "tool_executor", 
            ToolExecutionService,
            ToolExecutionService
        )
        
        # Initialize all services
        await self.container.initialize_services()
        
        logger.info("✅ Framework setup complete")
    
    def setup_event_handlers(self):
        """Set up event handlers for demonstration."""
        logger.info("📡 Setting up event handlers...")
        
        # Handler for agent creation events
        async def on_agent_created(event: AgentCreatedEvent):
            logger.info(f"🤖 Agent created: {event.agent_id} (type: {event.agent_type})")
            await self.cache.set(f"agent:{event.agent_id}", {
                "id": event.agent_id,
                "type": event.agent_type,
                "created_at": event.timestamp.isoformat()
            }, ttl=3600)
        
        # Handler for message processing events
        async def on_message_processed(event: MessageProcessedEvent):
            logger.info(f"💬 Message processed: {event.message_id} in {event.processing_time_ms:.2f}ms")
            
            # Store processing metrics
            metrics_key = f"metrics:processing_time"
            cached_metrics = await self.cache.get(metrics_key) or []
            cached_metrics.append({
                "message_id": event.message_id,
                "processing_time_ms": event.processing_time_ms,
                "timestamp": event.timestamp.isoformat()
            })
            
            # Keep only last 100 entries
            if len(cached_metrics) > 100:
                cached_metrics = cached_metrics[-100:]
            
            await self.cache.set(metrics_key, cached_metrics, ttl=1800)
        
        # Register event handlers
        self.event_bus.register_handler("agent.created", on_agent_created)
        self.event_bus.register_handler("message.processed", on_message_processed)
        
        logger.info("✅ Event handlers registered")
    
    async def create_sample_agents(self) -> Dict[str, Agent]:
        """Create sample agents for demonstration."""
        logger.info("🤖 Creating sample agents...")
        
        # Get orchestration service
        orchestrator = await self.container.get("agent_orchestrator")
        
        # Create security context (in real app, this would come from authentication)
        security_context = SecurityContext(
            user_id="demo_user",
            session_id="demo_session",
            permissions=["agent.create", "agent.pause", "agent.stop", "message.process"],
            ip_address="127.0.0.1",
            user_agent="Demo Client"
        )
        
        agents = {}
        
        # Create different types of agents
        agent_configs = [
            {
                "name": "Chat Assistant",
                "type": "conversational",
                "config": ModelConfiguration(
                    model_name="gpt-4",
                    temperature=0.7,
                    max_tokens=4096
                )
            },
            {
                "name": "Code Analyzer",
                "type": "analysis",
                "config": ModelConfiguration(
                    model_name="claude-3-sonnet",
                    temperature=0.3,
                    max_tokens=8192
                )
            },
            {
                "name": "Creative Writer",
                "type": "creative",
                "config": ModelConfiguration(
                    model_name="gpt-4",
                    temperature=1.2,
                    max_tokens=4096
                )
            }
        ]
        
        for agent_config in agent_configs:
            agent = await orchestrator.create_agent(
                name=agent_config["name"],
                agent_type=agent_config["type"],
                config=agent_config["config"],
                security_context=security_context
            )
            agents[agent_config["type"]] = agent
            
            # Small delay to see events in sequence
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Created {len(agents)} agents")
        return agents
    
    async def demonstrate_message_processing(self, agents: Dict[str, Agent]):
        """Demonstrate message processing with different agents."""
        logger.info("💬 Demonstrating message processing...")
        
        # Get message processing service
        processor = await self.container.get("message_processor")
        
        # Create security context
        security_context = SecurityContext(
            user_id="demo_user",
            session_id="demo_session",
            permissions=["message.process"],
            ip_address="127.0.0.1"
        )
        
        # Sample messages for different agent types
        test_messages = [
            {
                "agent_type": "conversational",
                "content": "Hello! Can you help me understand quantum computing?",
                "expected_tone": "friendly and educational"
            },
            {
                "agent_type": "analysis", 
                "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "expected_tone": "technical and precise"
            },
            {
                "agent_type": "creative",
                "content": "Write a short poem about artificial intelligence",
                "expected_tone": "creative and imaginative"
            }
        ]
        
        for msg_data in test_messages:
            agent = agents.get(msg_data["agent_type"])
            if not agent:
                continue
            
            # Validate and sanitize input
            validation_rules = {
                "content": {
                    "required": True,
                    "type": str,
                    "max_length": 1000
                }
            }
            
            try:
                clean_data = sanitize_and_validate_input(
                    {"content": msg_data["content"]}, 
                    validation_rules
                )
                
                # Check rate limit
                rate_result = await self.rate_limiter.check_rate_limit(
                    security_context.user_id, 
                    "api.chat"
                )
                
                if not rate_result.allowed:
                    logger.warning(f"⚠️ Rate limited for user {security_context.user_id}")
                    continue
                
                # Create message
                message = Message(
                    content=clean_data["content"],
                    sender_id=security_context.user_id,
                    recipient_id=agent.id,
                    message_type="text"
                )
                
                # Process message
                result = await processor.process_message(
                    message, 
                    agent.id, 
                    security_context
                )
                
                logger.info(f"📨 {agent.name} processed message: '{message.content[:50]}...'")
                logger.info(f"   Response: {result['response']}")
                
                # Small delay between messages
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
    
    async def demonstrate_tool_execution(self):
        """Demonstrate tool execution with security validation."""
        logger.info("🔧 Demonstrating tool execution...")
        
        # Get tool execution service
        tool_executor = await self.container.get("tool_executor")
        
        # Create sample tools
        tools = [
            Tool(
                name="file_reader",
                description="Read and analyze files",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "format": {"type": "string", "enum": ["text", "json", "csv"]}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="calculator",
                description="Perform mathematical calculations",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                        "precision": {"type": "integer", "minimum": 1, "maximum": 10}
                    },
                    "required": ["expression"]
                }
            )
        ]
        
        # Register tools
        for tool in tools:
            tool_executor.register_tool(tool)
        
        # Create security context
        security_context = SecurityContext(
            user_id="demo_user",
            session_id="demo_session",
            permissions=["tool.execute"],
            ip_address="127.0.0.1"
        )
        
        # Execute sample tools
        tool_executions = [
            {
                "tool_name": "calculator",
                "parameters": {"expression": "2 + 2 * 3", "precision": 2}
            },
            {
                "tool_name": "file_reader",
                "parameters": {"path": "data/sample.txt", "format": "text"}
            }
        ]
        
        for execution in tool_executions:
            try:
                # Create tool parameters value object
                tool_params = ToolParameters(
                    tool_name=execution["tool_name"],
                    parameters=execution["parameters"]
                )
                
                # Execute tool
                result = await tool_executor.execute_tool(
                    tool_params,
                    "demo_agent",
                    security_context
                )
                
                logger.info(f"🔧 Executed {execution['tool_name']}: {result['output']}")
                
            except Exception as e:
                logger.error(f"❌ Tool execution failed: {e}")
    
    @cached(None, ttl=300)  # Cache for 5 minutes
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics (cached for performance)."""
        logger.info("📊 Collecting system metrics...")
        
        # Simulate expensive metrics collection
        await asyncio.sleep(0.1)
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_agents": len(await self.cache.get("agents") or []),
            "processed_messages": len(await self.cache.get("metrics:processing_time") or []),
            "cache_size": self.cache.l1_cache.get_size() if hasattr(self.cache, 'l1_cache') else 0,
            "memory_usage": "45.2 MB",  # Mock data
            "cpu_usage": "12.5%",       # Mock data
        }
        
        return metrics
    
    async def demonstrate_performance_features(self):
        """Demonstrate caching and performance monitoring."""
        logger.info("⚡ Demonstrating performance features...")
        
        # Set cache for demonstration
        if not self.cache:
            self.cache = create_cache_hierarchy()
            
        # First call - should be slow (cache miss)
        start_time = asyncio.get_event_loop().time()
        metrics1 = await self.get_system_metrics()
        first_call_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Second call - should be fast (cache hit)
        start_time = asyncio.get_event_loop().time()
        metrics2 = await self.get_system_metrics()
        second_call_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.info(f"📊 First call (cache miss): {first_call_time:.2f}ms")
        logger.info(f"📊 Second call (cache hit): {second_call_time:.2f}ms")
        logger.info(f"🚀 Cache speedup: {first_call_time / second_call_time:.1f}x")
        
        # Demonstrate cache operations
        await self.cache.set("demo_key", {"message": "Hello, Cache!"}, ttl=60)
        cached_value = await self.cache.get("demo_key")
        logger.info(f"💾 Cache test: {cached_value}")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up resources...")
        
        # Clear caches
        if self.cache:
            await self.cache.clear()
        
        # Clear rate limiter state
        if self.rate_limiter:
            self.rate_limiter.clear_user_limits("demo_user")
        
        # Shutdown services
        await self.container.shutdown_services()
        
        logger.info("✅ Cleanup complete")
    
    async def run_complete_demo(self):
        """Run the complete demonstration."""
        try:
            logger.info("🎬 Starting Gary-Zero Framework Demonstration")
            logger.info("=" * 60)
            
            # Setup
            await self.setup_framework()
            self.setup_event_handlers()
            
            # Create agents
            agents = await self.create_sample_agents()
            
            # Wait for events to propagate
            await asyncio.sleep(0.5)
            
            # Demonstrate core features
            await self.demonstrate_message_processing(agents)
            await self.demonstrate_tool_execution()
            await self.demonstrate_performance_features()
            
            # Show final metrics
            logger.info("📊 Final System State:")
            if self.cache:
                stats = self.cache.get_combined_stats() if hasattr(self.cache, 'get_combined_stats') else {}
                for cache_name, cache_stats in stats.items():
                    if hasattr(cache_stats, 'hit_rate'):
                        logger.info(f"   {cache_name} cache hit rate: {cache_stats.hit_rate:.2%}")
            
            logger.info("🎉 Demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the example."""
    demo = ComprehensiveExample()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())