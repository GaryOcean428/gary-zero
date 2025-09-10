"""Main AI Model Manager that orchestrates all model management components.

This module provides the central interface for all AI model management
capabilities including versioning, A/B testing, caching, routing,
prompt management, and cost optimization.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .ab_testing import ABTestManager, ABTestConfig, TestGroup, ExperimentStatus
from .caching import ModelCacheManager, CacheConfig, CacheStrategy, CacheLevel
from .cost_optimizer import CostOptimizer, CostBudget, BudgetPeriod
from .prompt_manager import PromptManager, PromptTemplate, PromptType, OptimizationStrategy
from .routing import ModelRouter, RoutingStrategy, ModelInstance, RoutingRequest
from .version_manager import ModelVersionManager, ModelVersion, ModelStatus

logger = logging.getLogger(__name__)


class ModelManager:
    """Central manager for all AI model management capabilities."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path("ai_management")
        self.base_path.mkdir(exist_ok=True)
        
        # Initialize all management components
        self.version_manager = ModelVersionManager(self.base_path / "versions")
        self.ab_test_manager = ABTestManager(self.base_path / "ab_tests")
        self.prompt_manager = PromptManager(self.base_path / "prompts")
        self.cost_optimizer = CostOptimizer(self.base_path / "costs")
        self.model_router = ModelRouter()
        
        # Initialize cache managers for different models
        self.cache_managers: Dict[str, ModelCacheManager] = {}
        
        # Statistics tracking
        self.request_count = 0
        self.total_cost = 0.0
        self.start_time = datetime.now()
        
        logger.info("AI Model Manager initialized")
    
    def get_cache_manager(
        self,
        model_name: str,
        cache_config: Optional[CacheConfig] = None
    ) -> ModelCacheManager:
        """Get or create cache manager for a model."""
        if model_name not in self.cache_managers:
            config = cache_config or CacheConfig(
                strategy=CacheStrategy.EXACT_MATCH,
                levels=[CacheLevel.MEMORY, CacheLevel.DISK],
                ttl_seconds=3600,
                max_size_mb=100
            )
            
            cache_dir = self.base_path / "cache" / model_name.replace(":", "_")
            self.cache_managers[model_name] = ModelCacheManager(config, cache_dir)
        
        return self.cache_managers[model_name]
    
    # Version Management
    def create_model_version(
        self,
        model_name: str,
        provider: str,
        config: Dict[str, Any],
        **kwargs
    ) -> ModelVersion:
        """Create a new model version."""
        return self.version_manager.create_version(
            model_name, provider, config, **kwargs
        )
    
    def get_model_version(self, model_name: str, version: str) -> Optional[ModelVersion]:
        """Get specific model version."""
        return self.version_manager.get_version(model_name, version)
    
    def get_production_model(self, model_name: str) -> Optional[ModelVersion]:
        """Get current production version of a model."""
        return self.version_manager.get_production_version(model_name)
    
    def promote_model_version(
        self,
        model_name: str,
        version: str,
        target_status: ModelStatus
    ) -> bool:
        """Promote model version to target status."""
        return self.version_manager.promote_version(model_name, version, target_status)
    
    def rollback_model(self, model_name: str, version: str) -> bool:
        """Rollback model to specific version."""
        return self.version_manager.rollback_to_version(model_name, version)
    
    # A/B Testing
    def create_ab_test(
        self,
        name: str,
        description: str,
        model_a: str,
        version_a: str,
        model_b: str,
        version_b: str,
        traffic_split: float = 50.0,
        **kwargs
    ) -> str:
        """Create A/B test between two model versions."""
        groups = [
            TestGroup(
                name="control",
                model_name=model_a,
                model_version=version_a,
                traffic_percentage=traffic_split
            ),
            TestGroup(
                name="treatment",
                model_name=model_b,
                model_version=version_b,
                traffic_percentage=100.0 - traffic_split
            )
        ]
        
        return self.ab_test_manager.create_experiment(
            name, description, groups, **kwargs
        )
    
    def start_ab_test(self, experiment_id: str) -> bool:
        """Start an A/B test experiment."""
        return self.ab_test_manager.start_experiment(experiment_id)
    
    def stop_ab_test(self, experiment_id: str) -> bool:
        """Stop an A/B test experiment."""
        return self.ab_test_manager.stop_experiment(experiment_id)
    
    def get_ab_test_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get A/B test results and analysis."""
        return self.ab_test_manager.get_experiment_stats(experiment_id)
    
    def get_ab_test_winner(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get winning variant from A/B test."""
        return self.ab_test_manager.get_winning_variant(experiment_id)
    
    # Prompt Management
    def create_prompt_template(
        self,
        name: str,
        template: str,
        prompt_type: PromptType,
        **kwargs
    ) -> PromptTemplate:
        """Create a new prompt template."""
        return self.prompt_manager.create_template(
            name, template, prompt_type, **kwargs
        )
    
    def get_prompt_template(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """Get prompt template by name and version."""
        return self.prompt_manager.get_template_by_name(name, version)
    
    async def render_prompt(
        self,
        template_name: str,
        context: Dict[str, Any],
        optimize: bool = False,
        optimization_strategy: Optional[OptimizationStrategy] = None
    ) -> Optional[str]:
        """Render prompt template with context."""
        template = self.get_prompt_template(template_name)
        if not template:
            return None
        
        return await self.prompt_manager.render_template(
            template.id, context, optimize, optimization_strategy
        )
    
    def get_best_prompt_template(
        self,
        name: str,
        metric: str = "success_rate"
    ) -> Optional[PromptTemplate]:
        """Get best performing prompt template version."""
        return self.prompt_manager.get_best_performing_template(name, metric)
    
    # Model Routing
    def register_model_instance(self, instance: ModelInstance):
        """Register a model instance for routing."""
        self.model_router.register_instance(instance)
    
    async def route_model_request(
        self,
        model_name: str,
        model_version: str,
        request: RoutingRequest,
        strategy: RoutingStrategy = RoutingStrategy.PERFORMANCE_BASED
    ):
        """Route request to best available model instance."""
        return await self.model_router.route_request(
            model_name, model_version, request, strategy
        )
    
    async def record_request_result(
        self,
        instance_id: str,
        success: bool,
        response_time_ms: float,
        cost: float = 0.0
    ):
        """Record request result for routing optimization."""
        await self.model_router.record_request_result(
            instance_id, success, response_time_ms, cost
        )
    
    # Cost Management
    def record_model_cost(
        self,
        model_name: str,
        model_version: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost_input: float,
        cost_output: float,
        request_id: str,
        **kwargs
    ) -> bool:
        """Record cost for model usage."""
        self.total_cost += cost_input + cost_output
        return self.cost_optimizer.record_cost(
            model_name, model_version, provider,
            input_tokens, output_tokens, cost_input, cost_output,
            request_id, **kwargs
        )
    
    def create_cost_budget(
        self,
        name: str,
        limit: float,
        period: BudgetPeriod,
        **kwargs
    ) -> str:
        """Create a cost budget."""
        return self.cost_optimizer.create_budget(name, limit, period, **kwargs)
    
    def get_cost_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cost analytics and metrics."""
        metrics = self.cost_optimizer.get_usage_metrics(start_date, end_date)
        breakdown = self.cost_optimizer.get_cost_breakdown(start_date, end_date)
        budgets = self.cost_optimizer.get_budget_status()
        recommendations = self.cost_optimizer.generate_optimization_recommendations()
        
        return {
            'metrics': metrics,
            'breakdown': breakdown,
            'budgets': budgets,
            'recommendations': recommendations[:5]  # Top 5
        }
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations."""
        recommendations = self.cost_optimizer.generate_optimization_recommendations()
        return [
            {
                'type': r.type.value,
                'title': r.title,
                'description': r.description,
                'estimated_savings': r.estimated_savings,
                'confidence': r.confidence,
                'implementation_effort': r.implementation_effort
            }
            for r in recommendations
        ]
    
    # Caching
    async def get_cached_response(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached model response."""
        cache_manager = self.get_cache_manager(model_name)
        return await cache_manager.get_cached_response(model_name, prompt, parameters)
    
    async def cache_model_response(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any],
        response: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Cache a model response."""
        cache_manager = self.get_cache_manager(model_name)
        return await cache_manager.cache_response(
            model_name, prompt, parameters, response, ttl_seconds
        )
    
    async def invalidate_model_cache(self, model_name: str) -> bool:
        """Invalidate cache for a specific model."""
        if model_name in self.cache_managers:
            return await self.cache_managers[model_name].invalidate_model_cache(model_name)
        return True
    
    # Comprehensive Model Execution
    async def execute_model_request(
        self,
        model_name: str,
        prompt: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_cache: bool = True,
        use_ab_testing: bool = False,
        experiment_id: Optional[str] = None,
        routing_strategy: RoutingStrategy = RoutingStrategy.PERFORMANCE_BASED
    ) -> Dict[str, Any]:
        """Execute a comprehensive model request with all features."""
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        # Increment request counter
        self.request_count += 1
        
        try:
            # 1. Check cache first
            cached_response = None
            if use_cache:
                cached_response = await self.get_cached_response(
                    model_name, prompt, parameters
                )
                if cached_response:
                    return {
                        'response': cached_response,
                        'cached': True,
                        'request_id': request_id,
                        'response_time_ms': 0,
                        'cost': 0.0,
                        'model_used': model_name
                    }
            
            # 2. A/B testing assignment
            selected_model = model_name
            selected_version = "latest"
            ab_group = None
            
            if use_ab_testing and experiment_id:
                ab_group = self.ab_test_manager.assign_to_group(experiment_id, user_id)
                if ab_group:
                    selected_model = ab_group.model_name
                    selected_version = ab_group.model_version
            
            # 3. Get model version
            if selected_version == "latest":
                model_version = self.get_production_model(selected_model)
            else:
                model_version = self.get_model_version(selected_model, selected_version)
            
            if not model_version:
                raise ValueError(f"Model version not found: {selected_model}:{selected_version}")
            
            # 4. Route to model instance
            routing_request = RoutingRequest(
                prompt=prompt,
                parameters=parameters,
                user_id=user_id,
                session_id=session_id,
                metadata={'request_id': request_id}
            )
            
            routing_result = await self.route_model_request(
                selected_model, model_version.version, routing_request, routing_strategy
            )
            
            if not routing_result:
                raise ValueError(f"No available instances for {selected_model}:{model_version.version}")
            
            # 5. Execute the actual model call (simulated)
            # In a real implementation, this would call the actual model API
            response = await self._simulate_model_execution(
                routing_result.selected_instance,
                prompt,
                parameters
            )
            
            # Calculate response time and cost
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Estimate cost (would be actual cost in real implementation)
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimation
            output_tokens = len(str(response).split()) * 1.3
            cost_input = input_tokens * 0.001  # Simplified cost calculation
            cost_output = output_tokens * 0.002
            total_cost = cost_input + cost_output
            
            # 6. Record metrics and costs
            success = response is not None
            
            await self.record_request_result(
                routing_result.selected_instance.id,
                success,
                response_time_ms,
                total_cost
            )
            
            self.record_model_cost(
                selected_model,
                model_version.version,
                routing_result.selected_instance.provider,
                int(input_tokens),
                int(output_tokens),
                cost_input,
                cost_output,
                request_id,
                user_id=user_id,
                session_id=session_id
            )
            
            # 7. Record A/B test result
            if ab_group and experiment_id:
                # Record primary metric (response time in this example)
                from .ab_testing import TestMetric
                self.ab_test_manager.record_result(
                    experiment_id,
                    ab_group.name,
                    TestMetric.RESPONSE_TIME,
                    response_time_ms
                )
            
            # 8. Cache the response
            if use_cache and success:
                await self.cache_model_response(
                    selected_model, prompt, parameters, response
                )
            
            # 9. Update version metrics
            self.version_manager.update_performance_metrics(
                selected_model,
                model_version.version,
                {
                    'response_time': response_time_ms,
                    'cost': total_cost,
                    'success_rate': 1.0 if success else 0.0
                }
            )
            
            return {
                'response': response,
                'cached': False,
                'request_id': request_id,
                'response_time_ms': response_time_ms,
                'cost': total_cost,
                'model_used': f"{selected_model}:{model_version.version}",
                'instance_id': routing_result.selected_instance.id,
                'routing_strategy': routing_strategy.value,
                'ab_group': ab_group.name if ab_group else None,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens)
            }
        
        except Exception as e:
            logger.error(f"Model execution failed: {e}")
            
            # Record failure
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                'response': None,
                'error': str(e),
                'cached': False,
                'request_id': request_id,
                'response_time_ms': response_time_ms,
                'cost': 0.0,
                'model_used': model_name,
                'success': False
            }
    
    async def _simulate_model_execution(
        self,
        instance: ModelInstance,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Simulate model execution (replace with actual API calls)."""
        # Simulate processing time based on instance performance
        import random
        await asyncio.sleep(instance.response_time_ms / 1000 + random.uniform(0, 0.1))
        
        # Simulate response based on prompt
        return f"Response to: {prompt[:50]}..."
    
    # Analytics and Reporting
    def get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics across all components."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        analytics = {
            'overview': {
                'total_requests': self.request_count,
                'total_cost': self.total_cost,
                'uptime_seconds': uptime,
                'requests_per_second': self.request_count / uptime if uptime > 0 else 0,
                'average_cost_per_request': self.total_cost / self.request_count if self.request_count > 0 else 0
            },
            'versions': {
                'total_models': len(self.version_manager.versions),
                'production_models': sum(
                    1 for versions in self.version_manager.versions.values()
                    if any(v.status == ModelStatus.PRODUCTION for v in versions)
                )
            },
            'ab_tests': {
                'total_experiments': len(self.ab_test_manager.experiments),
                'running_experiments': len([
                    exp_id for exp_id, status in self.ab_test_manager.experiment_status.items()
                    if status == ExperimentStatus.RUNNING
                ])
            },
            'prompts': {
                'total_templates': len(self.prompt_manager.templates),
                'active_templates': len([
                    t for t in self.prompt_manager.templates.values()
                    if t.is_active
                ])
            },
            'routing': self.model_router.get_routing_stats(),
            'costs': self.get_cost_analytics(),
            'cache': {}
        }
        
        # Cache statistics
        for model_name, cache_manager in self.cache_managers.items():
            analytics['cache'][model_name] = asyncio.create_task(
                cache_manager.get_cache_stats()
            )
        
        return analytics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components."""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'version_manager': 'healthy',
                'ab_test_manager': 'healthy',
                'prompt_manager': 'healthy',
                'cost_optimizer': 'healthy',
                'model_router': 'healthy'
            },
            'models': self.model_router.get_instance_health(),
            'budgets': self.cost_optimizer.get_budget_status(),
            'alerts': self.cost_optimizer.get_recent_alerts(5)
        }
        
        # Check for any critical budget alerts
        budgets = self.cost_optimizer.get_budget_status()
        if any(b['is_exceeded'] for b in budgets):
            health['status'] = 'degraded'
            health['components']['cost_optimizer'] = 'degraded'
        
        return health
    
    async def warm_up(self, model_names: Optional[List[str]] = None):
        """Warm up caches and model instances."""
        logger.info("Starting AI Model Manager warm-up...")
        
        # Warm up caches
        if model_names:
            for model_name in model_names:
                cache_manager = self.get_cache_manager(model_name)
                await cache_manager.warm_up_models([model_name])
        
        logger.info("AI Model Manager warm-up completed")
    
    async def shutdown(self):
        """Gracefully shutdown the model manager."""
        logger.info("Shutting down AI Model Manager...")
        
        # Save all data
        self.version_manager._save_versions()
        self.ab_test_manager._save_experiments()
        self.prompt_manager._save_templates()
        self.cost_optimizer._save_data()
        
        # Clear caches
        for cache_manager in self.cache_managers.values():
            await cache_manager.clear_all_caches()
        
        logger.info("AI Model Manager shutdown completed")