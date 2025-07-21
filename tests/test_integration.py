"""
Integration tests for Gary-Zero Framework Quality Upgrades

These tests verify that all framework components work together correctly:
- Container + Security integration
- Container + Performance integration  
- Security + Performance integration
- Full end-to-end workflows
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from framework.container import get_container, Container
from framework.interfaces import BaseService
from framework.security import InputValidator, RateLimiter, AuditLogger, ContentSanitizer
from framework.performance import CacheManager, PerformanceMonitor, cached, timer


class MockSecureService(BaseService):
    """Mock service with security integration for testing."""
    
    def __init__(self):
        super().__init__()
        self.validator = InputValidator()
        self.sanitizer = ContentSanitizer()
        self.audit_logger = AuditLogger()
        
    async def initialize(self):
        await super().initialize()
        
    async def shutdown(self):
        await super().shutdown()
        
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input with security validation."""
        # Validate input
        if not self.validator.validate_user_input(user_input):
            self.audit_logger.log_security_violation(
                "invalid_input", {"input": user_input[:50]}
            )
            return {"success": False, "error": "Invalid input"}
            
        # Sanitize input
        clean_input = self.sanitizer.sanitize_text(user_input)
        
        # Log the operation
        self.audit_logger.log_user_input(clean_input, "process_user_input")
        
        return {"success": True, "processed_input": clean_input}


class MockPerformantService(BaseService):
    """Mock service with performance optimizations for testing."""
    
    def __init__(self):
        super().__init__()
        self.cache_manager = CacheManager()
        self.monitor = PerformanceMonitor()
        
    async def initialize(self):
        await super().initialize()
        
    async def shutdown(self):
        await super().shutdown()
        
    @cached(ttl=60)
    @timer("expensive_operation")
    def expensive_operation(self, data: str) -> Dict[str, Any]:
        """Simulate expensive operation with caching and timing."""
        # Simulate processing time
        import time
        time.sleep(0.01)
        
        return {
            "result": f"processed_{data}",
            "timestamp": time.time()
        }
        
    async def async_batch_process(self, items: list) -> Dict[str, Any]:
        """Async batch processing with monitoring."""
        with self.monitor.timing_context("batch_process"):
            results = []
            for item in items:
                await asyncio.sleep(0.001)  # Simulate async work
                results.append(f"processed_{item}")
                
            return {
                "results": results,
                "count": len(results),
                "metrics": self.monitor.get_metrics_summary()
            }


class TestFrameworkIntegration:
    """Integration tests for framework components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.container = Container()
        
    def teardown_method(self):
        """Clean up test environment."""
        self.container.clear()
        
    def test_container_security_integration(self):
        """Test container with security-enabled services."""
        # Register security-enabled service
        self.container.register_service("secure_service", MockSecureService)
        
        # Get and initialize service
        service = self.container.get("secure_service")
        assert isinstance(service, MockSecureService)
        assert hasattr(service, 'validator')
        assert hasattr(service, 'sanitizer')
        assert hasattr(service, 'audit_logger')
        
        # Test valid input processing
        result = service.process_user_input("valid_input_123")
        assert result["success"] is True
        assert "processed_input" in result
        
        # Test invalid input processing
        result = service.process_user_input("<script>alert('xss')</script>")
        assert result["success"] is False
        assert "error" in result
        
        # Verify audit logging
        summary = service.audit_logger.get_security_summary()
        assert summary["total_events"] > 0
        
    def test_container_performance_integration(self):
        """Test container with performance-optimized services."""
        # Register performance-optimized service
        self.container.register_service("performant_service", MockPerformantService)
        
        # Get service
        service = self.container.get("performant_service")
        assert isinstance(service, MockPerformantService)
        assert hasattr(service, 'cache_manager')
        assert hasattr(service, 'monitor')
        
        # Test cached operation
        result1 = service.expensive_operation("test_data")
        result2 = service.expensive_operation("test_data")  # Should be cached
        
        assert result1["result"] == result2["result"]
        # Second call should be from cache (same timestamp for this test)
        
    @pytest.mark.asyncio
    async def test_async_integration(self):
        """Test async integration between components."""
        # Register and initialize async service
        self.container.register_service("async_service", MockPerformantService)
        await self.container.initialize_services()
        
        service = self.container.get("async_service")
        
        # Test async batch processing
        test_items = ["item1", "item2", "item3"]
        result = await service.async_batch_process(test_items)
        
        assert result["count"] == 3
        assert len(result["results"]) == 3
        assert all(r.startswith("processed_") for r in result["results"])
        
        # Clean up
        await self.container.shutdown_services()
        
    def test_security_performance_integration(self):
        """Test security and performance working together."""
        # Create service with both security and performance
        class IntegratedService(BaseService):
            def __init__(self):
                super().__init__()
                self.validator = InputValidator()
                self.sanitizer = ContentSanitizer()
                self.cache_manager = CacheManager()
                
            @cached(ttl=30)
            def secure_cached_operation(self, user_input: str):
                if not self.validator.validate_user_input(user_input):
                    return {"error": "Invalid input"}
                    
                clean_input = self.sanitizer.sanitize_basic_text(user_input)
                return {"processed": clean_input, "cached": True}
        
        # Register and test
        self.container.register_service("integrated_service", IntegratedService)
        service = self.container.get("integrated_service")
        
        # Test valid input
        result1 = service.secure_cached_operation("valid_input")
        result2 = service.secure_cached_operation("valid_input")  # Cached
        
        assert result1["processed"] == result2["processed"]
        assert "error" not in result1
        
        # Test invalid input (should not be cached)
        result3 = service.secure_cached_operation("<script>")
        assert "error" in result3
        
    def test_rate_limiting_with_services(self):
        """Test rate limiting integration with container services."""
        class RateLimitedService(BaseService):
            def __init__(self):
                super().__init__()
                self.rate_limiter = RateLimiter()
                
            def limited_operation(self, user_id: str):
                if not self.rate_limiter.check_rate_limit(user_id, "operation"):
                    return {"error": "Rate limit exceeded"}
                return {"success": True, "user_id": user_id}
        
        self.container.register_service("rate_limited_service", RateLimitedService)
        service = self.container.get("rate_limited_service")
        
        # Test normal operation
        result = service.limited_operation("test_user")
        assert result["success"] is True
        
        # Test rate limiting (make many requests)
        rate_limited = False
        for i in range(20):  # Exceed default limit
            result = service.limited_operation("test_user")
            if "error" in result:
                rate_limited = True
                break
                
        assert rate_limited, "Rate limiting should have been triggered"
        
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow with all components."""
        # Register both services
        self.container.register_service("secure_service", MockSecureService)
        self.container.register_service("performant_service", MockPerformantService)
        
        # Initialize services
        await self.container.initialize_services()
        
        secure_service = self.container.get("secure_service")
        performant_service = self.container.get("performant_service")
        
        # Workflow: Secure input -> Performance processing -> Result
        user_inputs = ["valid_input_1", "valid_input_2", "<script>bad</script>"]
        
        processed_inputs = []
        for user_input in user_inputs:
            # Step 1: Security validation and sanitization
            security_result = secure_service.process_user_input(user_input)
            
            if security_result["success"]:
                # Step 2: Performance-optimized processing
                perf_result = performant_service.expensive_operation(
                    security_result["processed_input"]
                )
                processed_inputs.append(perf_result["result"])
                
        # Should have processed 2 valid inputs, rejected 1 invalid
        assert len(processed_inputs) == 2
        assert all("processed_valid_input" in result for result in processed_inputs)
        
        # Step 3: Async batch processing of validated results
        batch_result = await performant_service.async_batch_process(processed_inputs)
        assert batch_result["count"] == 2
        
        # Verify audit trail
        security_summary = secure_service.audit_logger.get_security_summary()
        assert security_summary["total_events"] >= 3  # All inputs logged
        assert security_summary.get("security_violations", 0) >= 1  # Invalid input
        
        # Clean up
        await self.container.shutdown_services()
        
    def test_dependency_injection_with_framework_components(self):
        """Test dependency injection with framework security and performance components."""
        class ServiceWithDependencies(BaseService):
            def __init__(self, validator: InputValidator, cache_manager: CacheManager):
                super().__init__()
                self.validator = validator
                self.cache_manager = cache_manager
                
            def validate_and_cache(self, key: str, value: str):
                if not self.validator.validate_user_input(value):
                    return {"error": "Invalid input"}
                    
                self.cache_manager.set(key, value, ttl=60)
                return {"success": True, "cached": True}
        
        # Register dependencies
        self.container.register_singleton("validator", InputValidator())
        self.container.register_singleton("cache_manager", CacheManager())
        
        # Register service with dependencies
        self.container.register_service("dependent_service", ServiceWithDependencies)
        
        # Get service (dependencies should be injected)
        service = self.container.get("dependent_service")
        
        # Test that dependencies were injected correctly
        assert isinstance(service.validator, InputValidator)
        assert isinstance(service.cache_manager, CacheManager)
        
        # Test functionality
        result = service.validate_and_cache("test_key", "valid_value")
        assert result["success"] is True
        
        # Verify cache
        cached_value = service.cache_manager.get("test_key")
        assert cached_value == "valid_value"
        
    def test_error_handling_integration(self):
        """Test error handling across framework components."""
        class ErrorProneService(BaseService):
            def __init__(self):
                super().__init__()
                self.audit_logger = AuditLogger()
                
            @timer("risky_operation")
            def risky_operation(self, should_fail: bool = False):
                if should_fail:
                    self.audit_logger.log_security_violation(
                        "operation_failed", {"reason": "intentional_test_failure"}
                    )
                    raise ValueError("Intentional test failure")
                return {"success": True}
        
        self.container.register_service("error_service", ErrorProneService)
        service = self.container.get("error_service")
        
        # Test successful operation
        result = service.risky_operation(should_fail=False)
        assert result["success"] is True
        
        # Test error handling
        with pytest.raises(ValueError, match="Intentional test failure"):
            service.risky_operation(should_fail=True)
            
        # Verify error was logged
        summary = service.audit_logger.get_security_summary()
        assert summary.get("security_violations", 0) >= 1


class TestPerformanceUnderLoad:
    """Test framework performance under load conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_service_access(self):
        """Test concurrent access to container services."""
        container = Container()
        container.register_service("perf_service", MockPerformantService)
        
        await container.initialize_services()
        service = container.get("perf_service")
        
        # Create multiple concurrent tasks
        async def concurrent_task(task_id: int):
            return await service.async_batch_process([f"item_{task_id}_{i}" for i in range(3)])
        
        # Run tasks concurrently
        tasks = [concurrent_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all tasks completed
        assert len(results) == 5
        assert all(result["count"] == 3 for result in results)
        
        await container.shutdown_services()
        
    def test_cache_performance_under_load(self):
        """Test cache performance with many operations."""
        cache_manager = CacheManager()
        
        # Perform many cache operations
        start_time = time.time()
        
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}", ttl=60)
            
        set_time = time.time() - start_time
        
        start_time = time.time()
        
        for i in range(1000):
            value = cache_manager.get(f"key_{i}")
            assert value == f"value_{i}"
            
        get_time = time.time() - start_time
        
        # Performance should be reasonable
        assert set_time < 1.0, f"Cache set operations too slow: {set_time}s"
        assert get_time < 0.5, f"Cache get operations too slow: {get_time}s"


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])