"""AI Management Framework Demo - Phase 5 Showcase

This demo showcases all the advanced AI model management capabilities:
- Model versioning and lifecycle management
- A/B testing framework
- Intelligent caching strategies
- Model routing and load balancing
- Advanced prompt engineering
- Cost optimization and analytics
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from framework.ai_management import (
    ModelManager,
    ModelInstance, RoutingRequest, RoutingStrategy,
    PromptType, OptimizationStrategy,
    CacheConfig, CacheStrategy, CacheLevel,
    BudgetPeriod, TestMetric
)
from framework.ai_management.version_manager import ModelStatus, VersionPolicy


class AIManagementDemo:
    """Comprehensive demo of AI Management Framework."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.model_manager = ModelManager(self.temp_dir)
        print(f"Demo data directory: {self.temp_dir}")
    
    async def run_complete_demo(self):
        """Run complete demonstration of all features."""
        print("=" * 80)
        print("🤖 AI MANAGEMENT FRAMEWORK - PHASE 5 DEMONSTRATION")
        print("=" * 80)
        
        # 1. Model Version Management
        await self.demo_version_management()
        
        # 2. Advanced Caching
        await self.demo_caching_strategies()
        
        # 3. Intelligent Routing
        await self.demo_intelligent_routing()
        
        # 4. A/B Testing
        await self.demo_ab_testing()
        
        # 5. Prompt Engineering
        await self.demo_prompt_engineering()
        
        # 6. Cost Optimization
        await self.demo_cost_optimization()
        
        # 7. Comprehensive Analytics
        await self.demo_analytics()
        
        print("\n" + "=" * 80)
        print("✅ AI MANAGEMENT FRAMEWORK DEMO COMPLETED")
        print("=" * 80)
    
    async def demo_version_management(self):
        """Demonstrate model version management."""
        print("\n📦 1. MODEL VERSION MANAGEMENT")
        print("-" * 40)
        
        # Create model versions
        print("Creating model versions...")
        v1 = self.model_manager.create_model_version(
            "gpt-4", "openai", 
            {"temperature": 0.7, "max_tokens": 1000},
            tags=["stable", "production"],
            metadata={"purpose": "general_use"}
        )
        print(f"✓ Created v{v1.version} (Development)")
        
        v2 = self.model_manager.create_model_version(
            "gpt-4", "openai",
            {"temperature": 0.8, "max_tokens": 1500},
            policy=VersionPolicy.MINOR,
            tags=["experimental", "high_creativity"],
            metadata={"purpose": "creative_tasks"}
        )
        print(f"✓ Created v{v2.version} (Development)")
        
        # Promote versions
        print("\nPromoting versions through lifecycle...")
        self.model_manager.promote_model_version("gpt-4", v1.version, ModelStatus.STAGING)
        print(f"✓ Promoted v{v1.version} to Staging")
        
        self.model_manager.promote_model_version("gpt-4", v1.version, ModelStatus.PRODUCTION)
        print(f"✓ Promoted v{v1.version} to Production")
        
        self.model_manager.promote_model_version("gpt-4", v2.version, ModelStatus.STAGING)
        print(f"✓ Promoted v{v2.version} to Staging")
        
        # Show version status
        print("\nCurrent model versions:")
        prod_version = self.model_manager.get_production_model("gpt-4")
        print(f"  Production: v{prod_version.version} (tags: {prod_version.tags})")
        
        versions = self.model_manager.version_manager.list_versions("gpt-4")
        for v in versions:
            print(f"  v{v.version}: {v.status.value} - {v.metadata.get('purpose', 'N/A')}")
    
    async def demo_caching_strategies(self):
        """Demonstrate advanced caching strategies."""
        print("\n🚀 2. ADVANCED CACHING STRATEGIES")
        print("-" * 40)
        
        # Configure different cache strategies
        cache_config = CacheConfig(
            strategy=CacheStrategy.EXACT_MATCH,
            levels=[CacheLevel.MEMORY, CacheLevel.DISK],
            ttl_seconds=3600,
            max_size_mb=50,
            warm_up_enabled=True
        )
        
        model_name = "gpt-4"
        cache_manager = self.model_manager.get_cache_manager(model_name, cache_config)
        
        print("Testing cache performance...")
        
        # Test cache miss and hit
        prompt = "What is artificial intelligence?"
        params = {"temperature": 0.7}
        
        # Cache miss
        cached = await cache_manager.get_cached_response(model_name, prompt, params)
        print(f"✓ Cache miss (expected): {cached is None}")
        
        # Cache the response
        response = "AI is a field of computer science focused on creating intelligent machines..."
        await cache_manager.cache_response(model_name, prompt, params, response)
        print("✓ Response cached")
        
        # Cache hit
        cached = await cache_manager.get_cached_response(model_name, prompt, params)
        print(f"✓ Cache hit: {cached == response}")
        
        # Cache statistics
        stats = await cache_manager.get_cache_stats()
        print(f"\nCache Statistics:")
        print(f"  Strategy: {stats['config']['strategy']}")
        print(f"  Levels: {', '.join(stats['config']['levels'])}")
        memory_stats = stats['levels']['memory']
        print(f"  Memory cache: {memory_stats['entries']} entries, {memory_stats['hit_rate']:.2%} hit rate")
    
    async def demo_intelligent_routing(self):
        """Demonstrate intelligent model routing."""
        print("\n🎯 3. INTELLIGENT MODEL ROUTING")
        print("-" * 40)
        
        # Register multiple model instances
        print("Registering model instances...")
        
        instances = [
            ModelInstance(
                id="gpt4-east-1",
                model_name="gpt-4",
                model_version="1.0.0",
                provider="openai",
                endpoint_url="https://api-east.openai.com",
                region="us-east-1",
                response_time_ms=120,
                success_rate=0.98,
                cost_per_request=0.02,
                capabilities=["text", "function_calling"]
            ),
            ModelInstance(
                id="gpt4-west-1",
                model_name="gpt-4",
                model_version="1.0.0",
                provider="openai",
                endpoint_url="https://api-west.openai.com",
                region="us-west-1",
                response_time_ms=100,
                success_rate=0.95,
                cost_per_request=0.025,
                capabilities=["text", "function_calling", "vision"]
            ),
            ModelInstance(
                id="gpt4-backup",
                model_name="gpt-4",
                model_version="1.0.0",
                provider="openai",
                endpoint_url="https://backup.openai.com",
                region="us-central-1",
                response_time_ms=200,
                success_rate=0.90,
                cost_per_request=0.015,
                capabilities=["text"]
            )
        ]
        
        for instance in instances:
            self.model_manager.register_model_instance(instance)
            print(f"✓ Registered {instance.id} ({instance.region})")
        
        # Test different routing strategies
        request = RoutingRequest(
            prompt="Analyze this image and provide insights",
            parameters={"temperature": 0.7},
            required_capabilities=["vision"],
            preferred_region="us-west-1",
            max_latency_ms=150
        )
        
        strategies = [
            RoutingStrategy.PERFORMANCE_BASED,
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.GEOGRAPHIC,
            RoutingStrategy.CAPABILITY_BASED
        ]
        
        print(f"\nTesting routing strategies for request requiring 'vision' capability:")
        for strategy in strategies:
            result = await self.model_manager.route_model_request(
                "gpt-4", "1.0.0", request, strategy
            )
            if result:
                instance = result.selected_instance
                print(f"  {strategy.value:20} → {instance.id} (cost: ${instance.cost_per_request:.3f}, latency: {instance.response_time_ms}ms)")
            else:
                print(f"  {strategy.value:20} → No suitable instance")
    
    async def demo_ab_testing(self):
        """Demonstrate A/B testing framework."""
        print("\n🧪 4. A/B TESTING FRAMEWORK")
        print("-" * 40)
        
        # Create A/B test
        print("Creating A/B test experiment...")
        experiment_id = self.model_manager.create_ab_test(
            name="GPT-4 Temperature Comparison",
            description="Compare performance of different temperature settings",
            model_a="gpt-4",
            version_a="1.0.0",
            model_b="gpt-4", 
            version_b="1.1.0",
            traffic_split=60.0,  # 60% control, 40% treatment
            primary_metric=TestMetric.RESPONSE_TIME,
            secondary_metrics=[TestMetric.COST_PER_REQUEST, TestMetric.SUCCESS_RATE],
            minimum_sample_size=20
        )
        print(f"✓ Created experiment: {experiment_id[:8]}...")
        
        # Start experiment
        self.model_manager.start_ab_test(experiment_id)
        print("✓ Started A/B test")
        
        # Simulate test data
        print("\nSimulating A/B test results...")
        import random
        
        for i in range(50):
            user_id = f"user_{i}"
            
            # Record response time results
            if i % 2 == 0:  # Control group
                response_time = random.normalvariate(150, 20)  # Average 150ms
                self.model_manager.ab_test_manager.record_result(
                    experiment_id, "control", TestMetric.RESPONSE_TIME, response_time
                )
            else:  # Treatment group
                response_time = random.normalvariate(130, 25)  # Average 130ms (better)
                self.model_manager.ab_test_manager.record_result(
                    experiment_id, "treatment", TestMetric.RESPONSE_TIME, response_time
                )
        
        print("✓ Recorded 50 test results")
        
        # Analyze results
        results = self.model_manager.get_ab_test_results(experiment_id)
        print(f"\nA/B Test Results:")
        print(f"  Total samples: {results['total_samples']}")
        
        for group_name, group_data in results['groups'].items():
            metrics = group_data['metrics']['response_time']
            print(f"  {group_name:10}: {metrics['count']} samples, avg {metrics['mean']:.1f}ms")
        
        # Check for winner
        winner = self.model_manager.get_ab_test_winner(experiment_id)
        if winner and winner['winner']:
            print(f"🏆 Winner: {winner['winner']} (improvement: {winner['improvement']}, confidence: {winner['confidence']})")
        else:
            print("📊 No statistically significant winner yet")
    
    async def demo_prompt_engineering(self):
        """Demonstrate advanced prompt engineering."""
        print("\n✍️  5. ADVANCED PROMPT ENGINEERING")
        print("-" * 40)
        
        # Create prompt templates
        print("Creating prompt templates...")
        
        templates = [
            {
                "name": "code_review",
                "template": """Please review the following {{language}} code and provide feedback:

Code:
```{{language}}
{{code}}
```

Focus on:
1. Code quality and best practices
2. Performance considerations  
3. Security implications
4. Suggestions for improvement

{% if expertise_level %}
Note: User expertise level is {{expertise_level}}.
{% endif %}""",
                "type": PromptType.SYSTEM,
                "description": "Template for code review tasks"
            },
            {
                "name": "meeting_summary",
                "template": """Summarize the following meeting transcript:

{{transcript}}

Please provide:
- Key decisions made
- Action items with owners
- Important topics discussed
- Next steps

Keep the summary concise and {{tone}} in tone.""",
                "type": PromptType.USER,
                "description": "Template for meeting summaries"
            }
        ]
        
        created_templates = []
        for template_data in templates:
            template = self.model_manager.create_prompt_template(
                name=template_data["name"],
                template=template_data["template"],
                prompt_type=template_data["type"],
                description=template_data["description"]
            )
            created_templates.append(template)
            print(f"✓ Created template: {template.name} v{template.version}")
        
        # Test template rendering
        print("\nTesting template rendering...")
        
        code_context = {
            "language": "Python",
            "code": "def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "expertise_level": "intermediate"
        }
        
        rendered = await self.model_manager.render_prompt(
            "code_review", code_context
        )
        print("✓ Rendered code review template")
        print(f"  Length: {len(rendered)} characters")
        
        # Test prompt optimization
        print("\nTesting prompt optimization...")
        
        original_template = created_templates[1]  # meeting_summary
        optimized = await self.model_manager.prompt_manager.optimize_template(
            original_template.id,
            OptimizationStrategy.LENGTH_REDUCTION
        )
        
        print(f"✓ Optimized prompt:")
        print(f"  Original length: {len(original_template.template)} chars")
        print(f"  Optimized length: {len(optimized)} chars")
        print(f"  Reduction: {((len(original_template.template) - len(optimized)) / len(original_template.template) * 100):.1f}%")
        
        # Simulate template performance metrics
        print("\nSimulating template performance...")
        for template in created_templates:
            for i in range(10):
                self.model_manager.prompt_manager.update_template_metrics(
                    template.id,
                    success=random.choice([True, True, True, False]),  # 75% success rate
                    response_time=random.normalvariate(200, 50),
                    cost=random.normalvariate(0.01, 0.003),
                    input_tokens=random.randint(50, 200),
                    output_tokens=random.randint(100, 400),
                    user_satisfaction=random.uniform(0.7, 1.0)
                )
        
        print("✓ Updated template performance metrics")
        
        # Get best performing template
        best_template = self.model_manager.get_best_prompt_template("code_review", "success_rate")
        if best_template:
            print(f"📈 Best performing 'code_review' template: v{best_template.version}")
            print(f"   Success rate: {best_template.metrics.success_rate:.1%}")
            print(f"   Avg response time: {best_template.metrics.average_response_time:.1f}ms")
    
    async def demo_cost_optimization(self):
        """Demonstrate cost optimization and analytics."""
        print("\n💰 6. COST OPTIMIZATION & ANALYTICS")
        print("-" * 40)
        
        # Create cost budgets
        print("Creating cost budgets...")
        
        budgets = [
            {
                "name": "Daily Development Budget",
                "limit": 50.0,
                "period": BudgetPeriod.DAILY,
                "warning_threshold": 0.8,
                "critical_threshold": 0.95
            },
            {
                "name": "Monthly Production Budget", 
                "limit": 1000.0,
                "period": BudgetPeriod.MONTHLY,
                "warning_threshold": 0.75,
                "critical_threshold": 0.90
            }
        ]
        
        for budget_data in budgets:
            budget_id = self.model_manager.create_cost_budget(**budget_data)
            print(f"✓ Created budget: {budget_data['name']} (${budget_data['limit']})")
        
        # Simulate cost data
        print("\nSimulating model usage and costs...")
        
        models = [
            ("gpt-4", "1.0.0", "openai"),
            ("gpt-4", "1.1.0", "openai"), 
            ("claude-3", "1.0.0", "anthropic")
        ]
        
        for i in range(100):
            model_name, version, provider = random.choice(models)
            
            # Simulate token usage and costs
            input_tokens = random.randint(50, 500)
            output_tokens = random.randint(20, 200)
            
            # Different cost structures per model
            if "gpt-4" in model_name:
                cost_input = input_tokens * 0.00003  # $0.03 per 1k tokens
                cost_output = output_tokens * 0.00006  # $0.06 per 1k tokens
            else:  # claude
                cost_input = input_tokens * 0.000015  # $0.015 per 1k tokens  
                cost_output = output_tokens * 0.000075  # $0.075 per 1k tokens
            
            self.model_manager.record_model_cost(
                model_name=model_name,
                model_version=version,
                provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_input=cost_input,
                cost_output=cost_output,
                request_id=f"req_{i}",
                user_id=f"user_{i % 10}",
                session_id=f"session_{i // 20}"
            )
        
        print("✓ Recorded 100 cost entries")
        
        # Get cost analytics
        analytics = self.model_manager.get_cost_analytics()
        metrics = analytics['metrics']
        
        print(f"\nCost Analytics:")
        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Total cost: ${metrics.total_cost:.4f}")
        print(f"  Avg cost per request: ${metrics.average_cost_per_request:.6f}")
        print(f"  Cost per token: ${metrics.cost_per_token:.8f}")
        print(f"  Most expensive model: {metrics.most_expensive_model}")
        
        # Cost breakdown by model
        breakdown = analytics['breakdown']
        print(f"\nTop models by cost:")
        sorted_models = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
        for model, cost in sorted_models:
            print(f"  {model:20}: ${cost:.4f}")
        
        # Get optimization recommendations
        recommendations = self.model_manager.get_cost_optimization_recommendations()
        print(f"\n💡 Cost Optimization Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec['title']}")
            print(f"     Estimated savings: ${rec['estimated_savings']:.4f} ({rec['confidence']:.0%} confidence)")
            print(f"     Implementation effort: {rec['implementation_effort']}")
        
        # Budget status
        budget_status = analytics['budgets']
        print(f"\nBudget Status:")
        for budget in budget_status:
            status_icon = "⚠️" if budget['is_warning'] else "✅"
            print(f"  {status_icon} {budget['name']}: ${budget['spent']:.2f}/${budget['limit']:.2f} ({budget['usage_percentage']:.1f}%)")
    
    async def demo_analytics(self):
        """Demonstrate comprehensive analytics and reporting."""
        print("\n📊 7. COMPREHENSIVE ANALYTICS")
        print("-" * 40)
        
        # Get comprehensive analytics
        analytics = self.model_manager.get_comprehensive_analytics()
        
        print("System Overview:")
        overview = analytics['overview']
        print(f"  Total requests: {overview['total_requests']}")
        print(f"  Total cost: ${overview['total_cost']:.4f}")
        print(f"  Uptime: {overview['uptime_seconds']:.1f} seconds")
        print(f"  Requests per second: {overview['requests_per_second']:.2f}")
        
        print(f"\nModel Management:")
        versions = analytics['versions']
        print(f"  Total models: {versions['total_models']}")
        print(f"  Production models: {versions['production_models']}")
        
        ab_tests = analytics['ab_tests']
        print(f"  Total experiments: {ab_tests['total_experiments']}")
        print(f"  Running experiments: {ab_tests['running_experiments']}")
        
        prompts = analytics['prompts']
        print(f"  Total prompt templates: {prompts['total_templates']}")
        print(f"  Active templates: {prompts['active_templates']}")
        
        # Routing statistics
        routing = analytics['routing']
        print(f"\nRouting Statistics:")
        print(f"  Total models configured: {routing['total_models']}")
        print(f"  Total instances: {routing['total_instances']}")
        
        # Health status
        health = self.model_manager.get_health_status()
        print(f"\nSystem Health: {health['status'].upper()}")
        print(f"  Components:")
        for component, status in health['components'].items():
            status_icon = "✅" if status == "healthy" else "⚠️"
            print(f"    {status_icon} {component}: {status}")
        
        # Cost analytics summary
        costs = analytics['costs']
        cost_metrics = costs['metrics']
        print(f"\nCost Summary:")
        print(f"  Peak usage hour: {cost_metrics.peak_usage_hour}:00" if cost_metrics.peak_usage_hour else "  Peak usage hour: N/A")
        print(f"  Most used model: {cost_metrics.most_used_model}")
        
        recent_alerts = health['alerts']
        if recent_alerts:
            print(f"\nRecent Alerts ({len(recent_alerts)}):")
            for alert in recent_alerts[:3]:
                print(f"  🚨 {alert['message']} ({alert['severity']})")
        else:
            print(f"\n✅ No recent alerts")


async def main():
    """Run the comprehensive AI Management demo."""
    demo = AIManagementDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    import random
    random.seed(42)  # For reproducible demo results
    asyncio.run(main())