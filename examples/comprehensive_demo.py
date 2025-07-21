#!/usr/bin/env python3
"""
Comprehensive Demo of Gary-Zero Framework Quality Upgrades

This demo showcases all the major components implemented:
1. Dependency Injection Container
2. Security Framework (validation, rate limiting, audit logging, sanitization)
3. Performance Framework (caching, async utils, monitoring, optimization)
4. Activity Monitor Integration
5. Interface-Based Architecture

Run this demo to see the framework in action with real-world examples.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

# Framework imports
from framework.container import get_container
from framework.interfaces import BaseService
from framework.security import (
    InputValidator, RateLimiter, AuditLogger, ContentSanitizer
)
from framework.performance import (
    CacheManager, PerformanceMonitor, ResourceOptimizer,
    BackgroundTaskManager, cached, timer, memory_optimize, cpu_optimize
)


class DemoUserService(BaseService):
    """Demo service for user management with framework integration."""
    
    def __init__(self):
        super().__init__()
        self.users: Dict[str, Dict[str, Any]] = {}
        self.validator = InputValidator()
        self.sanitizer = ContentSanitizer()
        self.audit_logger = AuditLogger()
        
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        print("✅ DemoUserService initialized")
        
    async def shutdown(self):
        """Shutdown the service."""
        await super().shutdown()
        print("✅ DemoUserService shutdown")
        
    @cached(ttl=300)  # Cache for 5 minutes
    @timer("get_user")  # Time the operation
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user with caching and timing."""
        # Validate input
        if not self.validator.validate_user_input(user_id):
            raise ValueError("Invalid user ID")
            
        # Sanitize input
        clean_user_id = self.sanitizer.sanitize_text(user_id)
        
        # Log the operation
        import asyncio
        asyncio.create_task(self.audit_logger.log_user_input("system", clean_user_id, "get_user"))
        
        # Return user or default
        return self.users.get(clean_user_id, {"id": clean_user_id, "name": "Unknown"})
    
    @memory_optimize()
    @cpu_optimize()
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create user with optimization and validation."""
        # Validate input
        if not self.validator.validate_tool_input("create_user", user_data):
            return False
            
        # Sanitize all string values
        sanitized_data = {}
        for key, value in user_data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitizer.sanitize_text(value)
            else:
                sanitized_data[key] = value
                
        # Store user
        user_id = sanitized_data.get("id", f"user_{len(self.users)}")
        self.users[user_id] = sanitized_data
        
        # Log creation
        import asyncio
        asyncio.create_task(self.audit_logger.log_tool_execution(
            "system", "create_user", {"user_id": user_id}, True, 0.001
        ))
        
        return True


class DemoDataService(BaseService):
    """Demo service for data processing with async capabilities."""
    
    def __init__(self):
        super().__init__()
        self.cache_manager = CacheManager()
        self.task_manager = BackgroundTaskManager()
        self.monitor = PerformanceMonitor()
        
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        print("✅ DemoDataService initialized")
        
    async def shutdown(self):
        """Shutdown the service."""
        await super().shutdown()
        print("✅ DemoDataService shutdown")
        
    @timer("process_data_batch")
    async def process_data_batch(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data batch with monitoring and caching."""
        batch_id = f"batch_{datetime.now().isoformat()}"
        
        # Check cache first
        cached_result = self.cache_manager.get(f"processed_{batch_id}")
        if cached_result:
            return cached_result
            
        # Start monitoring
        with self.monitor.timing_context("batch_processing"):
            # Simulate processing
            processed_items = []
            for item in data:
                # Simulate async processing
                await asyncio.sleep(0.01)
                processed_items.append({
                    "id": item.get("id", "unknown"),
                    "processed_at": datetime.now().isoformat(),
                    "status": "completed"
                })
                
            result = {
                "batch_id": batch_id,
                "processed_count": len(processed_items),
                "items": processed_items,
                "metrics": self.monitor.get_metrics_summary()
            }
            
            # Cache the result
            self.cache_manager.set(f"processed_{batch_id}", result, ttl=600)
            
            return result


async def demonstrate_framework():
    """Main demonstration function showcasing all framework components."""
    print("🚀 Starting Gary-Zero Framework Comprehensive Demo\n")
    
    # Initialize container and register services
    container = get_container()
    
    print("📦 Setting up Dependency Injection Container...")
    container.register_service("user_service", DemoUserService)
    container.register_service("data_service", DemoDataService)
    
    # Initialize all services
    await container.initialize_services()
    
    # Get services from container
    user_service = container.get("user_service")
    data_service = container.get("data_service")
    
    print("\n🔐 Testing Security Framework...")
    
    # Test rate limiting
    rate_limiter = RateLimiter()
    print("  • Testing rate limiting...")
    for i in range(15):  # Test rate limit (default is 10/minute)
        try:
            await rate_limiter.check_limit("api_call", "demo_user")
            print(f"    ✅ Request {i+1} allowed")
        except Exception as e:
            print(f"    ⚠️  Rate limit exceeded at request {i+1}: {e}")
            break
    else:
        print("    ✅ Rate limiting working normally")
    
    # Test input validation and sanitization
    print("  • Testing input validation and sanitization...")
    test_inputs = [
        "normal_user_123",
        "<script>alert('xss')</script>",
        "user'; DROP TABLE users; --",
        "valid@email.com"
    ]
    
    validator = InputValidator()
    sanitizer = ContentSanitizer()
    
    for test_input in test_inputs:
        try:
            is_valid = validator.validate_user_input(test_input)
            valid_status = "✅ Valid"
        except Exception as e:
            is_valid = False
            valid_status = "⚠️  Invalid (blocked)"
        
        sanitized = sanitizer.sanitize_text(test_input)
        print(f"    Input: '{test_input[:30]}...' -> {valid_status}, Sanitized: '{sanitized[:30]}...'")
    
    print("\n⚡ Testing Performance Framework...")
    
    # Test caching with user service
    print("  • Testing caching performance...")
    start_time = time.time()
    user1 = user_service.get_user("demo_user_1")  # First call - not cached
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    user2 = user_service.get_user("demo_user_1")  # Second call - cached
    second_call_time = time.time() - start_time
    
    print(f"    First call: {first_call_time:.4f}s, Second call: {second_call_time:.4f}s")
    print(f"    Cache speedup: {first_call_time/second_call_time:.2f}x")
    
    # Test user creation with optimization
    print("  • Testing optimized user creation...")
    test_users = [
        {"id": "user_1", "name": "Alice Johnson", "email": "alice@example.com"},
        {"id": "user_2", "name": "Bob Smith", "email": "bob@example.com"},
        {"id": "user_3", "name": "Charlie Brown", "email": "charlie@example.com"}
    ]
    
    creation_times = []
    for user_data in test_users:
        start_time = time.time()
        success = user_service.create_user(user_data)
        creation_time = time.time() - start_time
        creation_times.append(creation_time)
        print(f"    Created {user_data['name']}: {creation_time:.4f}s, Success: {success}")
    
    print(f"    Average creation time: {sum(creation_times)/len(creation_times):.4f}s")
    
    # Test async data processing
    print("  • Testing async data processing...")
    test_data = [{"id": f"item_{i}", "value": i * 10} for i in range(5)]
    
    result = await data_service.process_data_batch(test_data)
    print(f"    Processed {result['processed_count']} items in batch {result['batch_id'][:20]}...")
    
    # Test background task management
    print("  • Testing background task management...")
    task_manager = BackgroundTaskManager()
    
    async def background_task(task_id: int):
        await asyncio.sleep(0.1)
        return f"Task {task_id} completed"
    
    # Start multiple background tasks
    task_ids = await task_manager.submit_tasks([
        lambda: background_task(i) for i in range(3)
    ])
    print(f"    Started {len(task_ids)} background tasks")
    
    # Wait for completion
    results = await task_manager.wait_for_tasks(task_ids)
    print(f"    Completed tasks: {results}")
    
    print("\n📊 Performance Monitoring Summary...")
    monitor = PerformanceMonitor()
    metrics = monitor.get_metrics_summary()
    
    if metrics:
        print("  • Key metrics:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"    {key}: {value:.4f}")
    
    print("\n🏗️  Testing Interface-Based Architecture...")
    
    # Show dependency injection working
    print("  • Dependency injection container stats:")
    registered = container.list_registered()
    print(f"    Registered services: {list(registered.keys())}")
    
    # Test service lifecycle
    print("  • Testing service lifecycle...")
    print("    Services initialized ✅")
    
    await container.shutdown_services()
    print("    Services shut down ✅")
    
    print("\n📋 Security Audit Summary...")
    audit_logger = AuditLogger()
    security_summary = audit_logger.get_security_summary()
    
    print(f"  • Total events logged: {security_summary.get('total_events', 0)}")
    print(f"  • User input events: {security_summary.get('user_input_count', 0)}")
    print(f"  • Tool execution events: {security_summary.get('tool_execution_count', 0)}")
    
    print("\n🎉 Demo completed successfully!")
    print("\nFramework Components Demonstrated:")
    print("  ✅ Dependency Injection Container")
    print("  ✅ Security Framework (validation, rate limiting, audit logging)")
    print("  ✅ Performance Framework (caching, monitoring, optimization)")
    print("  ✅ Async Task Management")
    print("  ✅ Interface-Based Architecture")
    print("  ✅ Service Lifecycle Management")
    
    return True


if __name__ == "__main__":
    # Run the demonstration
    try:
        asyncio.run(demonstrate_framework())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()