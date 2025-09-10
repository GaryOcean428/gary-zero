"""Comprehensive tests for the AI Management framework."""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from framework.ai_management import (
    ModelManager,
    ABTestManager, ABTestConfig, TestGroup,
    ModelCacheManager, CacheConfig, CacheStrategy, CacheLevel,
    ModelRouter, RoutingStrategy, ModelInstance, RoutingRequest,
    PromptManager, PromptTemplate, PromptType, OptimizationStrategy,
    CostOptimizer, CostBudget, BudgetPeriod,
    ModelVersionManager, ModelVersion, ModelStatus
)
from framework.ai_management.ab_testing import TestMetric


class TestModelVersionManager:
    """Tests for model version management."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.version_manager = ModelVersionManager(self.temp_dir)
    
    def test_create_version(self):
        """Test creating a new model version."""
        config = {"temperature": 0.7, "max_tokens": 1000}
        version = self.version_manager.create_version(
            "gpt-4", "openai", config, tags=["production"]
        )
        
        assert version.version == "1.0.0"
        assert version.model_name == "gpt-4"
        assert version.provider == "openai"
        assert version.status == ModelStatus.DEVELOPMENT
        assert "production" in version.tags
    
    def test_version_increment(self):
        """Test version increment logic."""
        config = {"temperature": 0.7}
        
        # Create first version
        v1 = self.version_manager.create_version("gpt-4", "openai", config)
        assert v1.version == "1.0.0"
        
        # Create patch version
        v2 = self.version_manager.create_version("gpt-4", "openai", config)
        assert v2.version == "1.0.1"
        
        # Create minor version
        from framework.ai_management.version_manager import VersionPolicy
        v3 = self.version_manager.create_version(
            "gpt-4", "openai", config, policy=VersionPolicy.MINOR
        )
        assert v3.version == "1.1.0"
    
    def test_promote_version(self):
        """Test version promotion."""
        config = {"temperature": 0.7}
        version = self.version_manager.create_version("gpt-4", "openai", config)
        
        # Promote to staging
        success = self.version_manager.promote_version(
            "gpt-4", version.version, ModelStatus.STAGING
        )
        assert success
        assert version.status == ModelStatus.STAGING
        
        # Promote to production
        success = self.version_manager.promote_version(
            "gpt-4", version.version, ModelStatus.PRODUCTION
        )
        assert success
        assert version.status == ModelStatus.PRODUCTION
    
    def test_rollback(self):
        """Test version rollback."""
        config = {"temperature": 0.7}
        
        # Create multiple versions
        v1 = self.version_manager.create_version("gpt-4", "openai", config)
        v2 = self.version_manager.create_version("gpt-4", "openai", config)
        
        # Promote v2 to production
        self.version_manager.promote_version("gpt-4", v2.version, ModelStatus.STAGING)
        self.version_manager.promote_version("gpt-4", v2.version, ModelStatus.PRODUCTION)
        
        # Rollback to v1
        success = self.version_manager.rollback_to_version("gpt-4", v1.version)
        assert success
        assert v1.status == ModelStatus.PRODUCTION
        assert v2.status == ModelStatus.DEPRECATED


class TestABTestManager:
    """Tests for A/B testing framework."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.ab_manager = ABTestManager(self.temp_dir)
    
    def test_create_experiment(self):
        """Test creating A/B test experiment."""
        groups = [
            TestGroup("control", "gpt-4", "1.0.0", 50.0),
            TestGroup("treatment", "gpt-4", "1.1.0", 50.0)
        ]
        
        exp_id = self.ab_manager.create_experiment(
            "GPT-4 Version Comparison",
            "Compare v1.0.0 vs v1.1.0",
            groups,
            TestMetric.RESPONSE_TIME
        )
        
        assert exp_id in self.ab_manager.experiments
        experiment = self.ab_manager.experiments[exp_id]
        assert experiment.name == "GPT-4 Version Comparison"
        assert len(experiment.groups) == 2
    
    def test_traffic_allocation(self):
        """Test traffic allocation validation."""
        groups = [
            TestGroup("control", "gpt-4", "1.0.0", 40.0),
            TestGroup("treatment", "gpt-4", "1.1.0", 50.0)  # Total = 90%
        ]
        
        with pytest.raises(ValueError, match="Traffic allocation must sum to 100%"):
            self.ab_manager.create_experiment(
                "Invalid Test", "Invalid traffic", groups, TestMetric.RESPONSE_TIME
            )
    
    def test_group_assignment(self):
        """Test user assignment to groups."""
        groups = [
            TestGroup("control", "gpt-4", "1.0.0", 50.0),
            TestGroup("treatment", "gpt-4", "1.1.0", 50.0)
        ]
        
        exp_id = self.ab_manager.create_experiment(
            "Test", "Test", groups, TestMetric.RESPONSE_TIME
        )
        self.ab_manager.start_experiment(exp_id)
        
        # Test deterministic assignment
        group1 = self.ab_manager.assign_to_group(exp_id, "user123")
        group2 = self.ab_manager.assign_to_group(exp_id, "user123")
        assert group1.name == group2.name  # Same user gets same group
        
        # Test assignment distribution
        assignments = {}
        for i in range(100):
            group = self.ab_manager.assign_to_group(exp_id, f"user{i}")
            assignments[group.name] = assignments.get(group.name, 0) + 1
        
        # Should be roughly 50/50 split
        assert 30 <= assignments.get("control", 0) <= 70
        assert 30 <= assignments.get("treatment", 0) <= 70
    
    def test_record_results(self):
        """Test recording experiment results."""
        groups = [
            TestGroup("control", "gpt-4", "1.0.0", 50.0),
            TestGroup("treatment", "gpt-4", "1.1.0", 50.0)
        ]
        
        exp_id = self.ab_manager.create_experiment(
            "Test", "Test", groups, TestMetric.RESPONSE_TIME
        )
        
        # Record some results
        self.ab_manager.record_result(exp_id, "control", TestMetric.RESPONSE_TIME, 100.0)
        self.ab_manager.record_result(exp_id, "control", TestMetric.RESPONSE_TIME, 120.0)
        self.ab_manager.record_result(exp_id, "treatment", TestMetric.RESPONSE_TIME, 80.0)
        self.ab_manager.record_result(exp_id, "treatment", TestMetric.RESPONSE_TIME, 90.0)
        
        stats = self.ab_manager.get_experiment_stats(exp_id)
        assert stats['total_samples'] == 4
        assert 'control' in stats['groups']
        assert 'treatment' in stats['groups']


class TestModelCaching:
    """Tests for model caching system."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = CacheConfig(
            strategy=CacheStrategy.EXACT_MATCH,
            levels=[CacheLevel.MEMORY],
            ttl_seconds=3600,
            max_size_mb=10
        )
        self.cache_manager = ModelCacheManager(self.config, self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_hit(self):
        """Test cache miss followed by cache hit."""
        model_name = "gpt-4"
        prompt = "Hello, world!"
        params = {"temperature": 0.7}
        
        # Cache miss
        result = await self.cache_manager.get_cached_response(model_name, prompt, params)
        assert result is None
        
        # Cache the response
        response = "Hello! How can I help you?"
        success = await self.cache_manager.cache_response(
            model_name, prompt, params, response
        )
        assert success
        
        # Cache hit
        cached = await self.cache_manager.get_cached_response(model_name, prompt, params)
        assert cached == response
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation."""
        model_name = "gpt-4"
        prompt = "Test prompt"
        params = {"temperature": 0.7}
        response = "Test response"
        
        # Cache response
        await self.cache_manager.cache_response(model_name, prompt, params, response)
        
        # Verify cached
        cached = await self.cache_manager.get_cached_response(model_name, prompt, params)
        assert cached == response
        
        # Invalidate cache
        await self.cache_manager.invalidate_model_cache(model_name)
        
        # Verify cache miss
        cached = await self.cache_manager.get_cached_response(model_name, prompt, params)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        model_name = "gpt-4"
        prompt = "Test"
        params = {}
        
        # Initial stats
        stats = await self.cache_manager.get_cache_stats()
        assert 'config' in stats
        assert 'levels' in stats
        
        # Cache something
        await self.cache_manager.cache_response(model_name, prompt, params, "response")
        
        # Get updated stats
        stats = await self.cache_manager.get_cache_stats()
        memory_stats = stats['levels']['memory']
        assert memory_stats['entries'] >= 1


class TestModelRouter:
    """Tests for model routing system."""
    
    def setup_method(self):
        self.router = ModelRouter()
        
        # Register test instances
        self.instance1 = ModelInstance(
            id="instance1",
            model_name="gpt-4",
            model_version="1.0.0",
            provider="openai",
            endpoint_url="https://api.openai.com",
            response_time_ms=100.0,
            success_rate=0.95,
            cost_per_request=0.01
        )
        
        self.instance2 = ModelInstance(
            id="instance2",
            model_name="gpt-4",
            model_version="1.0.0",
            provider="openai",
            endpoint_url="https://api2.openai.com",
            response_time_ms=150.0,
            success_rate=0.90,
            cost_per_request=0.008
        )
        
        self.router.register_instance(self.instance1)
        self.router.register_instance(self.instance2)
    
    @pytest.mark.asyncio
    async def test_performance_based_routing(self):
        """Test performance-based routing."""
        request = RoutingRequest(
            prompt="Test prompt",
            parameters={"temperature": 0.7}
        )
        
        result = await self.router.route_request(
            "gpt-4", "1.0.0", request, RoutingStrategy.PERFORMANCE_BASED
        )
        
        assert result is not None
        # Should select instance1 (better performance)
        assert result.selected_instance.id == "instance1"
    
    @pytest.mark.asyncio
    async def test_cost_optimized_routing(self):
        """Test cost-optimized routing."""
        request = RoutingRequest(
            prompt="Test prompt",
            parameters={"temperature": 0.7}
        )
        
        result = await self.router.route_request(
            "gpt-4", "1.0.0", request, RoutingStrategy.COST_OPTIMIZED
        )
        
        assert result is not None
        # Should select instance2 (lower cost)
        assert result.selected_instance.id == "instance2"
    
    @pytest.mark.asyncio
    async def test_record_request_result(self):
        """Test recording request results."""
        initial_response_time = self.instance1.response_time_ms
        
        # Record a slower request
        await self.router.record_request_result("instance1", True, 200.0, 0.015)
        
        # Response time should be updated (rolling average)
        assert self.instance1.response_time_ms > initial_response_time
        assert self.instance1.response_time_ms < 200.0  # Due to rolling average


class TestPromptManager:
    """Tests for prompt management system."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.prompt_manager = PromptManager(self.temp_dir)
    
    def test_create_template(self):
        """Test creating prompt templates."""
        template = self.prompt_manager.create_template(
            name="greeting",
            template="Hello {{name}}, how are you?",
            prompt_type=PromptType.USER,
            description="A simple greeting template"
        )
        
        assert template.name == "greeting"
        assert template.version == "1.0"
        assert "name" in template.variables
        assert template.prompt_type == PromptType.USER
    
    def test_template_rendering(self):
        """Test template rendering."""
        template = self.prompt_manager.create_template(
            name="greeting",
            template="Hello {{name}}, you are {{age}} years old.",
            prompt_type=PromptType.USER
        )
        
        rendered = template.render({"name": "Alice", "age": 25})
        assert rendered == "Hello Alice, you are 25 years old."
    
    @pytest.mark.asyncio
    async def test_prompt_optimization(self):
        """Test prompt optimization."""
        template = self.prompt_manager.create_template(
            name="verbose",
            template="Please kindly help me with this task if you would be so kind.",
            prompt_type=PromptType.USER
        )
        
        optimized = await self.prompt_manager.optimize_template(
            template.id, OptimizationStrategy.LENGTH_REDUCTION
        )
        
        # Should be shorter
        assert len(optimized) < len(template.template)
    
    def test_template_versioning(self):
        """Test template versioning."""
        # Create initial template
        t1 = self.prompt_manager.create_template(
            name="test", template="Version 1", prompt_type=PromptType.USER
        )
        assert t1.version == "1.0"
        
        # Create new version
        t2 = self.prompt_manager.create_template(
            name="test", template="Version 2", prompt_type=PromptType.USER
        )
        assert t2.version == "1.1"
        
        # Get latest version
        latest = self.prompt_manager.get_template_by_name("test")
        assert latest.id == t2.id
    
    def test_template_metrics(self):
        """Test template metrics tracking."""
        template = self.prompt_manager.create_template(
            name="test", template="Test", prompt_type=PromptType.USER
        )
        
        # Update metrics
        success = self.prompt_manager.update_template_metrics(
            template.id,
            success=True,
            response_time=100.0,
            cost=0.01,
            input_tokens=10,
            output_tokens=20,
            user_satisfaction=0.9
        )
        
        assert success
        assert template.metrics.success_rate == 1.0
        assert template.metrics.average_response_time == 100.0
        assert template.metrics.token_efficiency == 2.0  # 20/10


class TestCostOptimizer:
    """Tests for cost optimization system."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cost_optimizer = CostOptimizer(self.temp_dir)
    
    def test_record_cost(self):
        """Test recording cost entries."""
        success = self.cost_optimizer.record_cost(
            model_name="gpt-4",
            model_version="1.0.0",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost_input=0.001,
            cost_output=0.002,
            request_id="req123"
        )
        
        assert success
        assert len(self.cost_optimizer.cost_entries) == 1
        
        entry = self.cost_optimizer.cost_entries[0]
        assert entry.total_cost == 0.003
        assert entry.model_name == "gpt-4"
    
    def test_budget_creation(self):
        """Test budget creation and tracking."""
        budget_id = self.cost_optimizer.create_budget(
            name="Daily Budget",
            limit=10.0,
            period=BudgetPeriod.DAILY
        )
        
        assert budget_id in self.cost_optimizer.budgets
        budget = self.cost_optimizer.budgets[budget_id]
        assert budget.name == "Daily Budget"
        assert budget.limit == 10.0
        assert budget.spent == 0.0
    
    def test_budget_alerts(self):
        """Test budget alert generation."""
        # Create a small budget
        budget_id = self.cost_optimizer.create_budget(
            name="Test Budget",
            limit=1.0,
            period=BudgetPeriod.DAILY,
            warning_threshold=0.5,
            critical_threshold=0.8
        )
        
        initial_alerts = len(self.cost_optimizer.alerts)
        
        # Record cost that exceeds budget
        self.cost_optimizer.record_cost(
            "gpt-4", "1.0.0", "openai", 100, 50, 0.5, 0.6, "req1"
        )
        
        # Should generate alerts
        assert len(self.cost_optimizer.alerts) > initial_alerts
    
    def test_usage_metrics(self):
        """Test usage metrics calculation."""
        # Record multiple costs
        for i in range(5):
            self.cost_optimizer.record_cost(
                "gpt-4", "1.0.0", "openai", 100, 50, 0.01, 0.02, f"req{i}"
            )
        
        metrics = self.cost_optimizer.get_usage_metrics()
        assert metrics.total_requests == 5
        assert metrics.total_cost == 0.15  # 5 * 0.03
        assert metrics.average_cost_per_request == 0.03
    
    def test_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        # Add some expensive model usage
        for i in range(10):
            self.cost_optimizer.record_cost(
                "gpt-4", "1.0.0", "openai", 1000, 500, 0.1, 0.2, f"req{i}"
            )
        
        recommendations = self.cost_optimizer.generate_optimization_recommendations()
        assert len(recommendations) > 0
        
        # Should include model switching recommendation
        model_switch_recs = [
            r for r in recommendations 
            if r.type.value == "model_switch"
        ]
        assert len(model_switch_recs) > 0


class TestModelManager:
    """Tests for the main model manager."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.model_manager = ModelManager(self.temp_dir)
    
    def test_initialization(self):
        """Test model manager initialization."""
        assert self.model_manager.version_manager is not None
        assert self.model_manager.ab_test_manager is not None
        assert self.model_manager.prompt_manager is not None
        assert self.model_manager.cost_optimizer is not None
        assert self.model_manager.model_router is not None
    
    @pytest.mark.asyncio
    async def test_comprehensive_request_execution(self):
        """Test comprehensive model request execution."""
        # Create a model version
        version = self.model_manager.create_model_version(
            "gpt-4", "openai", {"temperature": 0.7}
        )
        self.model_manager.promote_model_version(
            "gpt-4", version.version, ModelStatus.PRODUCTION
        )
        
        # Register model instance
        instance = ModelInstance(
            id="test-instance",
            model_name="gpt-4",
            model_version=version.version,
            provider="openai",
            endpoint_url="https://api.openai.com"
        )
        self.model_manager.register_model_instance(instance)
        
        # Execute request
        result = await self.model_manager.execute_model_request(
            model_name="gpt-4",
            prompt="Hello, world!",
            parameters={"temperature": 0.7},
            user_id="test-user"
        )
        
        assert 'response' in result
        assert 'request_id' in result
        assert 'cost' in result
        assert result['model_used'].startswith("gpt-4:")
    
    def test_analytics(self):
        """Test comprehensive analytics."""
        analytics = self.model_manager.get_comprehensive_analytics()
        
        assert 'overview' in analytics
        assert 'versions' in analytics
        assert 'ab_tests' in analytics
        assert 'prompts' in analytics
        assert 'routing' in analytics
        assert 'costs' in analytics
    
    def test_health_status(self):
        """Test health status reporting."""
        health = self.model_manager.get_health_status()
        
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        assert 'components' in health
        assert 'timestamp' in health
        assert all(
            comp in health['components'] 
            for comp in ['version_manager', 'ab_test_manager', 'prompt_manager', 'cost_optimizer', 'model_router']
        )


# Integration tests
class TestAIManagementIntegration:
    """Integration tests for the AI management framework."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.model_manager = ModelManager(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete AI management workflow."""
        # 1. Create model versions
        v1 = self.model_manager.create_model_version(
            "gpt-4", "openai", {"temperature": 0.7}, tags=["stable"]
        )
        v2 = self.model_manager.create_model_version(
            "gpt-4", "openai", {"temperature": 0.8}, tags=["experimental"]
        )
        
        # 2. Promote versions
        self.model_manager.promote_model_version("gpt-4", v1.version, ModelStatus.PRODUCTION)
        self.model_manager.promote_model_version("gpt-4", v2.version, ModelStatus.STAGING)
        
        # 3. Create prompt template
        template = self.model_manager.create_prompt_template(
            "greeting", "Hello {{name}}!", PromptType.USER
        )
        
        # 4. Set up A/B test
        ab_test_id = self.model_manager.create_ab_test(
            "Version Comparison", "Compare v1 vs v2", 
            "gpt-4", v1.version, "gpt-4", v2.version
        )
        self.model_manager.start_ab_test(ab_test_id)
        
        # 5. Create budget
        budget_id = self.model_manager.create_cost_budget(
            "Test Budget", 100.0, BudgetPeriod.DAILY
        )
        
        # 6. Register model instances
        for i in range(2):
            instance = ModelInstance(
                id=f"instance-{i}",
                model_name="gpt-4",
                model_version=v1.version,
                provider="openai",
                endpoint_url=f"https://api{i}.openai.com"
            )
            self.model_manager.register_model_instance(instance)
        
        # 7. Execute requests
        results = []
        for i in range(10):
            result = await self.model_manager.execute_model_request(
                model_name="gpt-4",
                prompt=f"Hello user {i}!",
                parameters={"temperature": 0.7},
                user_id=f"user-{i}",
                use_ab_testing=True,
                experiment_id=ab_test_id
            )
            results.append(result)
        
        # 8. Verify results
        assert len(results) == 10
        assert all('response' in result for result in results)
        assert sum(result['cost'] for result in results) > 0
        
        # 9. Check analytics
        analytics = self.model_manager.get_comprehensive_analytics()
        assert analytics['overview']['total_requests'] >= 10
        
        # 10. Check A/B test results
        ab_results = self.model_manager.get_ab_test_results(ab_test_id)
        assert ab_results['total_samples'] > 0
        
        # 11. Get recommendations
        recommendations = self.model_manager.get_cost_optimization_recommendations()
        assert isinstance(recommendations, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])