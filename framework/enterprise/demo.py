"""
Enterprise Operations Framework Demo.

This demo showcases the complete enterprise operations framework including:
- Feature flags with advanced targeting
- Deployment strategies (canary, blue-green, rolling)
- Configuration management with encryption and validation
- Real-time monitoring and alerting
- Dashboard creation and management
"""

import asyncio
import json
import random
from datetime import datetime, timezone, timedelta

from framework.enterprise import (
    FeatureFlagManager, FeatureFlag, TargetingRule, TargetingStrategy,
    DeploymentManager, DeploymentStrategy, Environment, DeploymentConfig,
    EnterpriseConfigManager, ConfigScope, ConfigValidationRule, ConfigSchema,
    EnterpriseMonitor, AlertRule, AlertSeverity, DashboardType
)


class EnterpriseOperationsDemo:
    """Complete enterprise operations demo."""
    
    def __init__(self):
        # Initialize all components
        self.feature_flag_manager = FeatureFlagManager(enable_analytics=True)
        self.deployment_manager = DeploymentManager(
            feature_flag_manager=self.feature_flag_manager
        )
        self.config_manager = EnterpriseConfigManager(
            enable_encryption=True,
            enable_hot_reload=True
        )
        self.monitor = EnterpriseMonitor()
        
        # Demo state
        self.demo_users = [f"user_{i}" for i in range(1, 101)]
        self.demo_environments = [
            Environment.DEVELOPMENT,
            Environment.STAGING,
            Environment.PRODUCTION
        ]
        
        print("🚀 Enterprise Operations Framework Demo Initialized")
    
    async def start(self):
        """Start all enterprise operations services."""
        print("\n📡 Starting Enterprise Operations Services...")
        
        await self.deployment_manager.start_monitoring()
        await self.config_manager.start_hot_reload()
        await self.monitor.start()
        
        print("✅ All services started successfully")
    
    async def stop(self):
        """Stop all enterprise operations services."""
        print("\n🛑 Stopping Enterprise Operations Services...")
        
        await self.deployment_manager.stop_monitoring()
        await self.config_manager.stop_hot_reload()
        await self.monitor.stop()
        
        print("✅ All services stopped successfully")
    
    async def demo_feature_flags(self):
        """Demonstrate feature flag capabilities."""
        print("\n🎯 === FEATURE FLAGS DEMO ===")
        
        # 1. Basic feature flag
        print("\n1. Creating basic feature flag...")
        await self.feature_flag_manager.register_flag(
            key="dark_mode",
            name="Dark Mode UI",
            description="Enable dark mode for the user interface",
            default_value=False,
            percentage_rollout=25.0,
            tags=["ui", "theme"]
        )
        
        # Test with different users
        enabled_users = []
        for user in self.demo_users[:10]:
            enabled = await self.feature_flag_manager.is_enabled("dark_mode", user_id=user)
            if enabled:
                enabled_users.append(user)
        
        print(f"   Dark mode enabled for {len(enabled_users)}/10 test users: {enabled_users}")
        
        # 2. Advanced targeting with user segments
        print("\n2. Creating advanced targeting rule...")
        vip_targeting = TargetingRule(
            strategy=TargetingStrategy.USER_ID,
            condition=json.dumps({"user_ids": ["user_1", "user_2", "user_5"]}),
            priority=1
        )
        
        await self.feature_flag_manager.register_flag(
            key="premium_features",
            name="Premium Features",
            description="Enable premium features for VIP users",
            default_value=False,
            targeting_rules=[vip_targeting],
            tags=["premium", "vip"]
        )
        
        # Test VIP targeting
        vip_users = ["user_1", "user_2", "user_5"]
        regular_users = ["user_10", "user_20", "user_30"]
        
        for user in vip_users:
            enabled = await self.feature_flag_manager.is_enabled("premium_features", user_id=user)
            print(f"   VIP user {user}: Premium features = {enabled}")
        
        for user in regular_users:
            enabled = await self.feature_flag_manager.is_enabled("premium_features", user_id=user)
            print(f"   Regular user {user}: Premium features = {enabled}")
        
        # 3. A/B testing flag
        print("\n3. Creating A/B testing flag...")
        await self.feature_flag_manager.register_flag(
            key="checkout_flow_v2",
            name="Checkout Flow V2",
            description="A/B test for new checkout flow",
            default_value="control",
            variations={"control": "original", "treatment": "new_flow"},
            percentage_rollout=50.0,
            tags=["ab_test", "checkout"]
        )
        
        # Test A/B variations
        variations = {"control": 0, "treatment": 0}
        for user in self.demo_users[:20]:
            variation = await self.feature_flag_manager.get_variation("checkout_flow_v2", user_id=user)
            if variation in variations:
                variations[variation] += 1
        
        print(f"   A/B test distribution: {variations}")
        
        # 4. Show flag analytics
        print("\n4. Feature flag analytics...")
        flags = await self.feature_flag_manager.list_flags()
        for flag in flags:
            stats = await self.feature_flag_manager.get_flag_stats(flag.key)
            print(f"   {flag.name}: {len(stats)} evaluation events")
    
    async def demo_deployments(self):
        """Demonstrate deployment strategies."""
        print("\n🚀 === DEPLOYMENT STRATEGIES DEMO ===")
        
        # 1. Immediate deployment
        print("\n1. Immediate deployment to staging...")
        staging_deployment = await self.deployment_manager.create_deployment(
            version="v1.5.0",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.IMMEDIATE,
            created_by="demo_user"
        )
        
        success = await self.deployment_manager.execute_deployment(staging_deployment.id)
        print(f"   Deployment {staging_deployment.id}: {'✅ Success' if success else '❌ Failed'}")
        
        # 2. Rolling deployment
        print("\n2. Rolling deployment to production...")
        rolling_config = DeploymentConfig(
            strategy=DeploymentStrategy.ROLLING,
            environment=Environment.PRODUCTION,
            rollout_duration=60,  # Faster for demo
            auto_rollback=True
        )
        
        rolling_deployment = await self.deployment_manager.create_deployment(
            version="v1.5.1",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.ROLLING,
            config=rolling_config,
            created_by="demo_user"
        )
        
        success = await self.deployment_manager.execute_deployment(rolling_deployment.id)
        print(f"   Rolling deployment {rolling_deployment.id}: {'✅ Success' if success else '❌ Failed'}")
        
        # 3. Canary deployment with feature flag integration
        print("\n3. Canary deployment with traffic splitting...")
        canary_config = DeploymentConfig(
            strategy=DeploymentStrategy.CANARY,
            environment=Environment.PRODUCTION,
            canary_percentage=10.0,
            auto_promote=True,
            success_threshold=95.0
        )
        
        canary_deployment = await self.deployment_manager.create_deployment(
            version="v1.6.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY,
            config=canary_config,
            created_by="demo_user"
        )
        
        success = await self.deployment_manager.execute_deployment(canary_deployment.id)
        print(f"   Canary deployment {canary_deployment.id}: {'✅ Success' if success else '❌ Failed'}")
        
        # 4. Show deployment history
        print("\n4. Deployment history...")
        deployments = await self.deployment_manager.list_deployments(limit=5)
        for deployment in deployments:
            print(f"   {deployment['version']} -> {deployment['environment']} "
                  f"({deployment['strategy']}) - {deployment['status']}")
        
        # 5. Monitor canary deployment
        if success and canary_deployment:
            print("\n5. Monitoring canary deployment...")
            status = await self.deployment_manager.get_deployment_status(canary_deployment.id)
            if status:
                print(f"   Status: {status['status']}")
                print(f"   Metrics: Success rate = {status['metrics']['success_rate']:.1f}%")
    
    async def demo_configuration_management(self):
        """Demonstrate configuration management."""
        print("\n⚙️ === CONFIGURATION MANAGEMENT DEMO ===")
        
        # 1. Basic configuration
        print("\n1. Setting basic configuration...")
        await self.config_manager.set_config(
            key="app_name",
            value="Gary-Zero Enterprise",
            scope=ConfigScope.GLOBAL,
            description="Application name"
        )
        
        await self.config_manager.set_config(
            key="max_connections",
            value=100,
            scope=ConfigScope.GLOBAL,
            description="Maximum database connections"
        )
        
        app_name = await self.config_manager.get_config("app_name", ConfigScope.GLOBAL)
        print(f"   App name: {app_name}")
        
        # 2. Environment-specific configuration
        print("\n2. Environment-specific configuration...")
        environments = ["development", "staging", "production"]
        db_configs = {
            "development": "postgresql://localhost:5432/gary_zero_dev",
            "staging": "postgresql://staging.db:5432/gary_zero_staging",
            "production": "postgresql://prod.db:5432/gary_zero_prod"
        }
        
        for env, db_url in db_configs.items():
            await self.config_manager.set_config(
                key="database_url",
                value=db_url,
                scope=ConfigScope.ENVIRONMENT,
                environment=env,
                description=f"Database URL for {env}"
            )
        
        for env in environments:
            db_url = await self.config_manager.get_config(
                key="database_url",
                scope=ConfigScope.ENVIRONMENT,
                environment=env
            )
            print(f"   {env}: {db_url}")
        
        # 3. Encrypted secrets
        print("\n3. Encrypted secret management...")
        secret_data = {
            "api_key": "sk-1234567890abcdef",
            "client_secret": "super_secret_key_123",
            "encryption_key": "aes256-key-here"
        }
        
        await self.config_manager.set_config(
            key="api_credentials",
            value=secret_data,
            scope=ConfigScope.GLOBAL,
            encrypt=True,
            description="Encrypted API credentials"
        )
        
        # Retrieve and verify
        retrieved_secret = await self.config_manager.get_config(
            key="api_credentials",
            scope=ConfigScope.GLOBAL
        )
        print(f"   Retrieved encrypted secret: {retrieved_secret['api_key'][:8]}...")
        
        # 4. Configuration validation
        print("\n4. Configuration validation with schema...")
        validation_rules = [
            ConfigValidationRule(
                field_path="port",
                rule_type="range",
                rule_config={"min": 1, "max": 65535},
                error_message="Port must be between 1 and 65535"
            ),
            ConfigValidationRule(
                field_path="host",
                rule_type="required",
                rule_config={},
                error_message="Host is required"
            )
        ]
        
        server_schema = ConfigSchema(
            name="server_config",
            version="1.0",
            validation_rules=validation_rules,
            required_fields=["host", "port"],
            field_types={"port": "int", "host": "string"}
        )
        
        await self.config_manager.register_schema(server_schema)
        
        # Valid configuration
        success = await self.config_manager.set_config(
            key="port",
            value=8080,
            scope=ConfigScope.GLOBAL,
            schema_name="server_config"
        )
        print(f"   Valid port (8080): {'✅ Accepted' if success else '❌ Rejected'}")
        
        # Invalid configuration
        success = await self.config_manager.set_config(
            key="port",
            value=70000,  # Out of range
            scope=ConfigScope.GLOBAL,
            schema_name="server_config"
        )
        print(f"   Invalid port (70000): {'✅ Accepted' if success else '❌ Rejected'}")
        
        # 5. Configuration promotion
        print("\n5. Configuration promotion workflow...")
        await self.config_manager.set_config(
            key="new_feature_config",
            value={"enabled": True, "threshold": 0.8},
            scope=ConfigScope.ENVIRONMENT,
            environment="staging",
            description="New feature configuration tested in staging"
        )
        
        # Promote to production
        success = await self.config_manager.promote_config(
            key="new_feature_config",
            from_environment="staging",
            to_environment="production"
        )
        print(f"   Configuration promotion: {'✅ Success' if success else '❌ Failed'}")
        
        # 6. Configuration history and rollback
        print("\n6. Configuration versioning and rollback...")
        original_value = "1.0.0"
        await self.config_manager.set_config("version", original_value, ConfigScope.GLOBAL)
        
        for version in ["1.1.0", "1.2.0", "1.3.0"]:
            await self.config_manager.set_config("version", version, ConfigScope.GLOBAL)
        
        current_version = await self.config_manager.get_config("version", ConfigScope.GLOBAL)
        print(f"   Current version: {current_version}")
        
        # Rollback
        success = await self.config_manager.rollback_config("version", ConfigScope.GLOBAL)
        rolled_back_version = await self.config_manager.get_config("version", ConfigScope.GLOBAL)
        print(f"   After rollback: {rolled_back_version}")
    
    async def demo_monitoring_and_alerting(self):
        """Demonstrate monitoring and alerting capabilities."""
        print("\n📊 === MONITORING & ALERTING DEMO ===")
        
        # 1. Record various metrics
        print("\n1. Recording operational metrics...")
        
        # System metrics
        for i in range(10):
            cpu_usage = random.uniform(20, 95)
            memory_usage = random.uniform(30, 85)
            
            await self.monitor.record_metric("system_cpu_usage", cpu_usage)
            await self.monitor.record_metric("system_memory_usage", memory_usage)
        
        # HTTP request metrics
        endpoints = ["/api/chat", "/api/models", "/api/health", "/api/config"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        status_codes = [200, 201, 400, 404, 500]
        
        for i in range(50):
            endpoint = random.choice(endpoints)
            method = random.choice(methods)
            status = random.choice(status_codes)
            duration = random.uniform(0.05, 2.0)
            
            await self.monitor.record_metric(
                "http_requests_total",
                1,
                {"method": method, "status": str(status), "endpoint": endpoint}
            )
            
            await self.monitor.record_metric(
                "http_request_duration",
                duration,
                {"method": method, "endpoint": endpoint}
            )
        
        # AI inference metrics
        models = ["gpt-4", "claude-3", "llama-2"]
        for i in range(20):
            model = random.choice(models)
            inference_time = random.uniform(0.5, 3.0)
            
            await self.monitor.record_metric(
                "ai_model_inference_time",
                inference_time,
                {"model": model, "version": "latest"}
            )
        
        print("   ✅ Recorded system, HTTP, and AI metrics")
        
        # 2. Query and analyze metrics
        print("\n2. Analyzing metric data...")
        
        # CPU usage summary
        cpu_summary = await self.monitor.get_metric_summary("system_cpu_usage")
        print(f"   CPU Usage - Min: {cpu_summary['min']:.1f}%, "
              f"Max: {cpu_summary['max']:.1f}%, "
              f"Avg: {cpu_summary['avg']:.1f}%")
        
        # HTTP request analysis
        http_samples = await self.monitor.query_metrics("http_requests_total", duration_hours=1)
        total_requests = sum(s.value for s in http_samples)
        print(f"   Total HTTP requests: {int(total_requests)}")
        
        # AI inference performance
        ai_samples = await self.monitor.query_metrics(
            "ai_model_inference_time",
            aggregation="avg",
            duration_hours=1
        )
        if ai_samples:
            avg_inference_time = ai_samples[0].value
            print(f"   Average AI inference time: {avg_inference_time:.2f}s")
        
        # 3. Setup alert rules
        print("\n3. Configuring alert rules...")
        await self.monitor.setup_default_alerts()
        
        # Add custom alert
        custom_alert = AlertRule(
            name="slow_api_response",
            description="API response time is too slow",
            metric_name="http_request_duration",
            condition=">",
            threshold_value=1.5,
            severity=AlertSeverity.MEDIUM,
            duration=60
        )
        await self.monitor.alert_manager.add_rule(custom_alert)
        
        print("   ✅ Configured default + custom alert rules")
        
        # 4. Trigger alerts (simulate high values)
        print("\n4. Simulating alert conditions...")
        
        # Trigger high CPU alert
        await self.monitor.record_metric("system_cpu_usage", 95.0)
        
        # Trigger slow response alert
        await self.monitor.record_metric(
            "http_request_duration",
            2.0,
            {"method": "GET", "endpoint": "/api/slow"}
        )
        
        # Evaluate alerts
        await self.monitor.alert_manager._evaluate_rules()
        
        # Check active alerts
        active_alerts = await self.monitor.alert_manager.get_active_alerts()
        print(f"   Active alerts: {len(active_alerts)}")
        
        for alert in active_alerts:
            print(f"   🚨 {alert.severity.value.upper()}: {alert.message}")
        
        # 5. Create dashboard
        print("\n5. Creating monitoring dashboard...")
        
        # Create operational dashboard
        dashboard = await self.monitor.create_operational_dashboard()
        print(f"   Created dashboard: {dashboard.name}")
        print(f"   Widgets: {len(dashboard.widgets)}")
        
        # Add custom business dashboard
        business_dashboard = await self.monitor.create_dashboard(
            name="Business Metrics",
            description="Key business and performance metrics",
            dashboard_type=DashboardType.BUSINESS,
            tags=["business", "kpi"]
        )
        
        # Add business-specific widgets
        await self.monitor.add_widget_to_dashboard(
            business_dashboard.id,
            "AI Model Usage",
            "pie_chart",
            ["ai_model_inference_time"],
            {"group_by": "model"},
            {"x": 0, "y": 0, "width": 6, "height": 6}
        )
        
        await self.monitor.add_widget_to_dashboard(
            business_dashboard.id,
            "API Endpoint Performance",
            "bar_chart",
            ["http_request_duration"],
            {"group_by": "endpoint", "aggregation": "avg"},
            {"x": 6, "y": 0, "width": 6, "height": 6}
        )
        
        print(f"   Created business dashboard: {business_dashboard.name}")
        
        # 6. Render dashboard data
        print("\n6. Rendering dashboard data...")
        dashboard_data = await self.monitor.render_dashboard_data(dashboard.id)
        
        for widget in dashboard_data["widgets"]:
            sample_count = sum(len(data["samples"]) for data in widget["data"])
            print(f"   Widget '{widget['title']}': {sample_count} data points")
        
        # 7. System health check
        print("\n7. Overall system health...")
        health = await self.monitor.get_monitoring_health()
        
        print(f"   System status: {health['status']}")
        print(f"   Active alerts: {health['active_alerts']}")
        print(f"   Critical alerts: {health['critical_alerts']}")
        print(f"   Registered metrics: {health['registered_metrics']}")
        print(f"   Dashboards: {health['dashboards']}")
    
    async def demo_integrated_workflow(self):
        """Demonstrate integrated enterprise operations workflow."""
        print("\n🔄 === INTEGRATED ENTERPRISE WORKFLOW DEMO ===")
        
        print("\n📋 Scenario: Rolling out a new AI model with enterprise controls")
        
        # 1. Configuration setup
        print("\n1. Setting up configuration for new AI model...")
        await self.config_manager.set_config(
            key="new_model_config",
            value={
                "model_name": "gary-zero-v3",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30
            },
            scope=ConfigScope.ENVIRONMENT,
            environment="staging",
            description="Configuration for new AI model v3"
        )
        
        # 2. Feature flag for gradual rollout
        print("\n2. Creating feature flag for gradual rollout...")
        await self.feature_flag_manager.register_flag(
            key="ai_model_v3_rollout",
            name="AI Model V3 Rollout",
            description="Gradual rollout of new AI model v3",
            default_value=False,
            percentage_rollout=0,  # Start with 0%
            tags=["ai", "model", "rollout"]
        )
        
        # 3. Canary deployment
        print("\n3. Starting canary deployment...")
        canary_config = DeploymentConfig(
            strategy=DeploymentStrategy.CANARY,
            environment=Environment.PRODUCTION,
            canary_percentage=5.0,
            auto_promote=False,  # Manual promotion for demo
            success_threshold=95.0
        )
        
        deployment = await self.deployment_manager.create_deployment(
            version="v3.0.0-canary",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY,
            config=canary_config,
            created_by="ai_team"
        )
        
        success = await self.deployment_manager.execute_deployment(deployment.id)
        print(f"   Canary deployment: {'✅ Started' if success else '❌ Failed'}")
        
        # 4. Enable feature flag for canary traffic
        print("\n4. Enabling feature flag for canary traffic...")
        await self.feature_flag_manager.update_flag(
            "ai_model_v3_rollout",
            percentage_rollout=5.0
        )
        
        # 5. Monitor canary performance
        print("\n5. Monitoring canary performance...")
        
        # Simulate canary traffic and metrics
        for i in range(20):
            # Simulate AI inference requests
            model = "gary-zero-v3" if random.random() < 0.05 else "gary-zero-v2"
            inference_time = random.uniform(0.8, 1.5) if model == "gary-zero-v3" else random.uniform(1.0, 2.0)
            
            await self.monitor.record_metric(
                "ai_model_inference_time",
                inference_time,
                {"model": model, "version": "latest"}
            )
            
            # Record feature flag evaluations
            user_id = f"user_{random.randint(1, 100)}"
            enabled = await self.feature_flag_manager.is_enabled(
                "ai_model_v3_rollout",
                user_id=user_id
            )
            
            await self.monitor.record_metric(
                "feature_flag_evaluations",
                1,
                {"flag": "ai_model_v3_rollout", "variation": str(enabled)}
            )
        
        # 6. Analyze performance
        print("\n6. Analyzing canary performance...")
        
        # Get metrics for both models
        v2_metrics = await self.monitor.query_metrics(
            "ai_model_inference_time",
            labels={"model": "gary-zero-v2"},
            duration_hours=1
        )
        
        v3_metrics = await self.monitor.query_metrics(
            "ai_model_inference_time", 
            labels={"model": "gary-zero-v3"},
            duration_hours=1
        )
        
        if v2_metrics and v3_metrics:
            v2_avg = sum(s.value for s in v2_metrics) / len(v2_metrics)
            v3_avg = sum(s.value for s in v3_metrics) / len(v3_metrics)
            
            print(f"   V2 average inference time: {v2_avg:.2f}s")
            print(f"   V3 average inference time: {v3_avg:.2f}s")
            
            improvement = ((v2_avg - v3_avg) / v2_avg) * 100
            print(f"   Performance improvement: {improvement:.1f}%")
            
            # 7. Decision: promote or rollback
            if improvement > 10:  # 10% improvement threshold
                print("\n7. ✅ Performance improved! Proceeding with gradual rollout...")
                
                # Increase rollout percentage
                await self.feature_flag_manager.update_flag(
                    "ai_model_v3_rollout",
                    percentage_rollout=25.0
                )
                
                # Promote configuration to production
                await self.config_manager.promote_config(
                    key="new_model_config",
                    from_environment="staging",
                    to_environment="production"
                )
                
                print("   🚀 Increased rollout to 25% and promoted config to production")
                
            else:
                print("\n7. ⚠️ Performance not improved enough. Rolling back...")
                
                # Disable feature flag
                await self.feature_flag_manager.update_flag(
                    "ai_model_v3_rollout",
                    percentage_rollout=0
                )
                
                # Abort deployment
                await self.deployment_manager.abort_deployment(deployment.id)
                
                print("   🔄 Rollback completed")
        
        # 8. Generate final report
        print("\n8. 📊 Generating rollout report...")
        
        # Feature flag stats
        flag_stats = await self.feature_flag_manager.get_flag_stats("ai_model_v3_rollout")
        print(f"   Feature flag evaluations: {sum(flag_stats.values())}")
        
        # Deployment status
        deployment_status = await self.deployment_manager.get_deployment_status(deployment.id)
        if deployment_status:
            print(f"   Deployment status: {deployment_status['status']}")
            print(f"   Success rate: {deployment_status['metrics']['success_rate']:.1f}%")
        
        # System health
        health = await self.monitor.get_monitoring_health()
        print(f"   System health: {health['status']}")
        print(f"   Active monitoring alerts: {health['active_alerts']}")
        
        print("\n✅ Integrated enterprise workflow completed successfully!")
    
    async def run_demo(self):
        """Run the complete enterprise operations demo."""
        try:
            await self.start()
            
            print("\n" + "="*80)
            print("🏢 GARY-ZERO ENTERPRISE OPERATIONS FRAMEWORK DEMO")
            print("="*80)
            
            await self.demo_feature_flags()
            await asyncio.sleep(1)
            
            await self.demo_deployments()
            await asyncio.sleep(1)
            
            await self.demo_configuration_management()
            await asyncio.sleep(1)
            
            await self.demo_monitoring_and_alerting()
            await asyncio.sleep(1)
            
            await self.demo_integrated_workflow()
            
            print("\n" + "="*80)
            print("🎉 ENTERPRISE OPERATIONS DEMO COMPLETED SUCCESSFULLY!")
            print("="*80)
            
            print("\n📈 Demo Summary:")
            print("✅ Feature Flags: Advanced targeting, A/B testing, analytics")
            print("✅ Deployments: Canary, rolling, blue-green strategies")
            print("✅ Configuration: Multi-scope, encrypted, validated config management")
            print("✅ Monitoring: Real-time metrics, alerting, custom dashboards")
            print("✅ Integration: End-to-end enterprise workflow automation")
            
            print("\n🚀 Gary-Zero is now enterprise-ready with production-grade operations!")
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.stop()


async def main():
    """Run the enterprise operations demo."""
    demo = EnterpriseOperationsDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())