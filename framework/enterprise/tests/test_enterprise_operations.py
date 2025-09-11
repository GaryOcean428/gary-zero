"""
Tests for Enterprise Operations Framework.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from framework.enterprise.feature_flags import (
    FeatureFlagManager, FeatureFlag, TargetingRule, FeatureFlagStatus, TargetingStrategy
)
from framework.enterprise.deployments import (
    DeploymentManager, Deployment, DeploymentStrategy, DeploymentStatus, Environment, DeploymentConfig
)
from framework.enterprise.config_manager import (
    EnterpriseConfigManager, ConfigEntry, ConfigScope, ConfigValidationRule, ConfigSchema
)
from framework.enterprise.monitoring import (
    EnterpriseMonitor, AlertManager, MetricDefinition, MetricType, AlertRule, AlertSeverity
)


class TestFeatureFlags:
    """Test suite for feature flag functionality."""
    
    @pytest.fixture
    async def flag_manager(self):
        """Create feature flag manager for testing."""
        manager = FeatureFlagManager()
        yield manager
    
    @pytest.mark.asyncio
    async def test_register_flag(self, flag_manager):
        """Test registering a new feature flag."""
        flag = await flag_manager.register_flag(
            key="test_feature",
            name="Test Feature",
            description="A test feature flag",
            default_value=False
        )
        
        assert flag.key == "test_feature"
        assert flag.name == "Test Feature"
        assert flag.status == FeatureFlagStatus.ACTIVE
        assert flag.default_value is False
    
    @pytest.mark.asyncio
    async def test_is_enabled_default(self, flag_manager):
        """Test feature flag evaluation with default value."""
        await flag_manager.register_flag(
            key="test_feature",
            name="Test Feature",
            description="A test feature flag",
            default_value=False
        )
        
        # Should return default value
        result = await flag_manager.is_enabled("test_feature")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_percentage_rollout(self, flag_manager):
        """Test percentage-based rollout."""
        await flag_manager.register_flag(
            key="test_percentage",
            name="Test Percentage",
            description="Percentage rollout test",
            default_value=False,
            percentage_rollout=50.0
        )
        
        # Test multiple users to verify percentage logic
        enabled_count = 0
        total_tests = 100
        
        for i in range(total_tests):
            result = await flag_manager.is_enabled(
                "test_percentage",
                user_id=f"user_{i}"
            )
            if result:
                enabled_count += 1
        
        # Should be approximately 50% (allow some variance)
        assert 30 <= enabled_count <= 70
    
    @pytest.mark.asyncio
    async def test_user_targeting(self, flag_manager):
        """Test user ID targeting."""
        rule = TargetingRule(
            strategy=TargetingStrategy.USER_ID,
            condition=json.dumps({"user_ids": ["user1", "user2"]}),
            priority=1
        )
        
        await flag_manager.register_flag(
            key="test_targeting",
            name="Test Targeting",
            description="User targeting test",
            default_value=False,
            targeting_rules=[rule]
        )
        
        # Targeted users should be enabled
        assert await flag_manager.is_enabled("test_targeting", user_id="user1") is True
        assert await flag_manager.is_enabled("test_targeting", user_id="user2") is True
        
        # Non-targeted users should use default
        assert await flag_manager.is_enabled("test_targeting", user_id="user3") is False
    
    @pytest.mark.asyncio
    async def test_flag_update(self, flag_manager):
        """Test updating feature flag configuration."""
        await flag_manager.register_flag(
            key="test_update",
            name="Test Update",
            description="Update test",
            default_value=False
        )
        
        # Update the flag
        updated_flag = await flag_manager.update_flag(
            "test_update",
            percentage_rollout=25.0,
            description="Updated description"
        )
        
        assert updated_flag is not None
        assert updated_flag.percentage_rollout == 25.0
        assert updated_flag.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_export_import_configuration(self, flag_manager):
        """Test configuration export and import."""
        # Create test flags
        await flag_manager.register_flag(
            key="flag1",
            name="Flag 1",
            description="First flag",
            default_value=True
        )
        
        await flag_manager.register_flag(
            key="flag2",
            name="Flag 2", 
            description="Second flag",
            default_value=False,
            percentage_rollout=30.0
        )
        
        # Export configuration
        config = await flag_manager.export_configuration()
        
        assert "flags" in config
        assert len(config["flags"]) == 2
        assert "version" in config
        
        # Clear and import
        new_manager = FeatureFlagManager()
        success = await new_manager.import_configuration(config)
        assert success is True
        
        # Verify imported flags
        flags = await new_manager.list_flags()
        assert len(flags) == 2
        
        flag_keys = {f.key for f in flags}
        assert "flag1" in flag_keys
        assert "flag2" in flag_keys


class TestDeployments:
    """Test suite for deployment management."""
    
    @pytest.fixture
    async def deployment_manager(self):
        """Create deployment manager for testing."""
        manager = DeploymentManager()
        await manager.start_monitoring()
        yield manager
        await manager.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_create_deployment(self, deployment_manager):
        """Test creating a deployment."""
        deployment = await deployment_manager.create_deployment(
            version="v1.0.0",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.ROLLING,
            created_by="test_user"
        )
        
        assert deployment.version == "v1.0.0"
        assert deployment.environment == Environment.STAGING
        assert deployment.strategy == DeploymentStrategy.ROLLING
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.created_by == "test_user"
    
    @pytest.mark.asyncio
    async def test_execute_immediate_deployment(self, deployment_manager):
        """Test immediate deployment execution."""
        deployment = await deployment_manager.create_deployment(
            version="v1.0.0",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.IMMEDIATE
        )
        
        success = await deployment_manager.execute_deployment(deployment.id)
        assert success is True
        
        # Check deployment status
        updated_deployment = await deployment_manager.backend.get_deployment(deployment.id)
        assert updated_deployment.status == DeploymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_canary_deployment(self, deployment_manager):
        """Test canary deployment with monitoring."""
        config = DeploymentConfig(
            strategy=DeploymentStrategy.CANARY,
            environment=Environment.PRODUCTION,
            canary_percentage=10.0,
            auto_promote=False
        )
        
        deployment = await deployment_manager.create_deployment(
            version="v1.1.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY,
            config=config
        )
        
        success = await deployment_manager.execute_deployment(deployment.id)
        assert success is True
        
        # Should be in canary testing phase
        updated_deployment = await deployment_manager.backend.get_deployment(deployment.id)
        assert updated_deployment.status == DeploymentStatus.CANARY_TESTING
    
    @pytest.mark.asyncio
    async def test_deployment_rollback(self, deployment_manager):
        """Test deployment rollback functionality."""
        # Create successful deployment first
        successful_deployment = await deployment_manager.create_deployment(
            version="v1.0.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.IMMEDIATE
        )
        await deployment_manager.execute_deployment(successful_deployment.id)
        
        # Create failed deployment
        config = DeploymentConfig(
            strategy=DeploymentStrategy.IMMEDIATE,
            environment=Environment.PRODUCTION,
            auto_rollback=True
        )
        
        failed_deployment = await deployment_manager.create_deployment(
            version="v1.1.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.IMMEDIATE,
            config=config
        )
        
        # Mock failure
        deployment_manager.backend.deploy_version = AsyncMock(return_value=False)
        
        success = await deployment_manager.execute_deployment(failed_deployment.id)
        assert success is False
        
        # Should trigger rollback
        updated_deployment = await deployment_manager.backend.get_deployment(failed_deployment.id)
        assert updated_deployment.status in [DeploymentStatus.ROLLING_BACK, DeploymentStatus.ROLLED_BACK]
    
    @pytest.mark.asyncio
    async def test_list_deployments(self, deployment_manager):
        """Test listing deployments with filtering."""
        # Create test deployments
        await deployment_manager.create_deployment(
            version="v1.0.0",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.ROLLING
        )
        
        await deployment_manager.create_deployment(
            version="v1.1.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY
        )
        
        # List all deployments
        all_deployments = await deployment_manager.list_deployments()
        assert len(all_deployments) == 2
        
        # Filter by environment
        staging_deployments = await deployment_manager.list_deployments(
            environment=Environment.STAGING
        )
        assert len(staging_deployments) == 1
        assert staging_deployments[0]["environment"] == Environment.STAGING.value


class TestConfigManager:
    """Test suite for enterprise configuration management."""
    
    @pytest.fixture
    async def config_manager(self):
        """Create config manager for testing."""
        manager = EnterpriseConfigManager()
        yield manager
        await manager.stop_hot_reload()
    
    @pytest.mark.asyncio
    async def test_set_get_config(self, config_manager):
        """Test basic configuration set and get operations."""
        # Set configuration
        success = await config_manager.set_config(
            key="database_url",
            value="postgresql://localhost:5432/test",
            scope=ConfigScope.GLOBAL,
            description="Test database URL"
        )
        assert success is True
        
        # Get configuration
        value = await config_manager.get_config(
            key="database_url",
            scope=ConfigScope.GLOBAL
        )
        assert value == "postgresql://localhost:5432/test"
    
    @pytest.mark.asyncio
    async def test_config_scoping(self, config_manager):
        """Test configuration scope hierarchy."""
        # Set global config
        await config_manager.set_config(
            key="feature_enabled",
            value=False,
            scope=ConfigScope.GLOBAL
        )
        
        # Set environment-specific config
        await config_manager.set_config(
            key="feature_enabled",
            value=True,
            scope=ConfigScope.ENVIRONMENT,
            environment="staging"
        )
        
        # Global scope should return global value
        global_value = await config_manager.get_config(
            key="feature_enabled",
            scope=ConfigScope.GLOBAL
        )
        assert global_value is False
        
        # Environment scope should return environment-specific value
        env_value = await config_manager.get_config(
            key="feature_enabled",
            scope=ConfigScope.ENVIRONMENT,
            environment="staging"
        )
        assert env_value is True
        
        # Different environment should fall back to global
        other_env_value = await config_manager.get_config(
            key="feature_enabled",
            scope=ConfigScope.ENVIRONMENT,
            environment="production"
        )
        assert other_env_value is False
    
    @pytest.mark.asyncio
    async def test_config_encryption(self, config_manager):
        """Test configuration encryption."""
        secret_value = {"api_key": "secret123", "password": "super_secret"}
        
        # Set encrypted config
        success = await config_manager.set_config(
            key="api_credentials",
            value=secret_value,
            scope=ConfigScope.GLOBAL,
            encrypt=True
        )
        assert success is True
        
        # Get and verify decrypted value
        decrypted_value = await config_manager.get_config(
            key="api_credentials",
            scope=ConfigScope.GLOBAL
        )
        assert decrypted_value == secret_value
    
    @pytest.mark.asyncio
    async def test_config_validation(self, config_manager):
        """Test configuration validation with schema."""
        # Register validation schema
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
        
        schema = ConfigSchema(
            name="server_config",
            version="1.0",
            validation_rules=validation_rules,
            required_fields=["host", "port"],
            field_types={"port": "int", "host": "string"}
        )
        
        await config_manager.register_schema(schema)
        
        # Valid config should succeed
        success = await config_manager.set_config(
            key="port",
            value=8080,
            scope=ConfigScope.GLOBAL,
            schema_name="server_config"
        )
        assert success is True
        
        # Invalid config should fail
        success = await config_manager.set_config(
            key="port",
            value=70000,  # Out of range
            scope=ConfigScope.GLOBAL,
            schema_name="server_config"
        )
        assert success is False
    
    @pytest.mark.asyncio
    async def test_config_history_rollback(self, config_manager):
        """Test configuration history and rollback."""
        # Set initial value
        await config_manager.set_config(
            key="version",
            value="1.0.0",
            scope=ConfigScope.GLOBAL
        )
        
        # Update value multiple times
        await config_manager.set_config(
            key="version",
            value="1.1.0",
            scope=ConfigScope.GLOBAL
        )
        
        await config_manager.set_config(
            key="version",
            value="1.2.0",
            scope=ConfigScope.GLOBAL
        )
        
        # Check current value
        current_value = await config_manager.get_config("version", ConfigScope.GLOBAL)
        assert current_value == "1.2.0"
        
        # Get history
        history = await config_manager.get_config_history("version", ConfigScope.GLOBAL)
        assert len(history) >= 2  # Previous versions
        
        # Rollback to previous version
        success = await config_manager.rollback_config("version", ConfigScope.GLOBAL)
        assert success is True
        
        # Verify rollback
        rolled_back_value = await config_manager.get_config("version", ConfigScope.GLOBAL)
        assert rolled_back_value == "1.1.0"
    
    @pytest.mark.asyncio
    async def test_config_promotion(self, config_manager):
        """Test configuration promotion between environments."""
        # Set config in staging
        await config_manager.set_config(
            key="feature_toggle",
            value=True,
            scope=ConfigScope.ENVIRONMENT,
            environment="staging"
        )
        
        # Promote to production
        success = await config_manager.promote_config(
            key="feature_toggle",
            from_environment="staging",
            to_environment="production"
        )
        assert success is True
        
        # Verify promotion
        prod_value = await config_manager.get_config(
            key="feature_toggle",
            scope=ConfigScope.ENVIRONMENT,
            environment="production"
        )
        assert prod_value is True
    
    @pytest.mark.asyncio
    async def test_bulk_import_export(self, config_manager):
        """Test bulk configuration import and export."""
        # Set up test configuration
        test_configs = {
            "app_name": "Gary-Zero",
            "debug_mode": True,
            "max_connections": 100
        }
        
        # Bulk import
        successful, failed, errors = await config_manager.bulk_import(
            test_configs,
            scope=ConfigScope.GLOBAL
        )
        
        assert successful == 3
        assert failed == 0
        assert len(errors) == 0
        
        # Bulk export
        exported_data = await config_manager.bulk_export(
            scope=ConfigScope.GLOBAL,
            include_metadata=False
        )
        
        assert isinstance(exported_data, dict)
        assert "app_name" in exported_data
        assert exported_data["app_name"] == "Gary-Zero"


class TestMonitoring:
    """Test suite for enterprise monitoring."""
    
    @pytest.fixture
    async def monitor(self):
        """Create enterprise monitor for testing."""
        monitor = EnterpriseMonitor()
        await monitor.start()
        yield monitor
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_record_metric(self, monitor):
        """Test recording metrics."""
        # Record a metric
        success = await monitor.record_metric(
            metric_name="http_requests_total",
            value=1,
            labels={"method": "GET", "status": "200", "endpoint": "/api/test"}
        )
        assert success is True
        
        # Query the metric
        samples = await monitor.query_metrics(
            metric_name="http_requests_total",
            duration_hours=1
        )
        assert len(samples) == 1
        assert samples[0].value == 1
        assert samples[0].labels["method"] == "GET"
    
    @pytest.mark.asyncio
    async def test_metric_aggregation(self, monitor):
        """Test metric aggregation."""
        # Record multiple samples
        for i in range(5):
            await monitor.record_metric(
                metric_name="response_time",
                value=i * 100,  # 0, 100, 200, 300, 400
                labels={"endpoint": "/test"}
            )
        
        # Query with aggregation
        samples = await monitor.query_metrics(
            metric_name="response_time",
            aggregation="avg",
            duration_hours=1
        )
        
        assert len(samples) == 1
        assert samples[0].value == 200.0  # Average of 0,100,200,300,400
    
    @pytest.mark.asyncio
    async def test_alert_rules(self, monitor):
        """Test alert rule evaluation."""
        # Add alert rule
        alert_rule = AlertRule(
            name="high_response_time",
            description="Response time too high",
            metric_name="response_time",
            condition=">",
            threshold_value=150.0,
            severity=AlertSeverity.HIGH
        )
        
        await monitor.alert_manager.add_rule(alert_rule)
        
        # Record metric that should trigger alert
        await monitor.record_metric("response_time", 200.0)
        
        # Manually trigger evaluation (in real scenario this happens in background)
        await monitor.alert_manager._evaluate_rules()
        
        # Check active alerts
        active_alerts = await monitor.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].severity == AlertSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_dashboard_creation(self, monitor):
        """Test dashboard creation and management."""
        # Create dashboard
        dashboard = await monitor.create_dashboard(
            name="Test Dashboard",
            description="A test dashboard",
            tags=["test", "monitoring"]
        )
        
        assert dashboard.name == "Test Dashboard"
        assert "test" in dashboard.tags
        
        # Add widget
        success = await monitor.add_widget_to_dashboard(
            dashboard.id,
            "CPU Usage",
            "gauge",
            ["system_cpu_usage"],
            {"threshold": 80},
            {"x": 0, "y": 0, "width": 6, "height": 4}
        )
        assert success is True
        
        # Get dashboard with data
        dashboard_data = await monitor.render_dashboard_data(dashboard.id)
        assert "widgets" in dashboard_data
        assert len(dashboard_data["widgets"]) == 1
    
    @pytest.mark.asyncio
    async def test_operational_dashboard(self, monitor):
        """Test pre-configured operational dashboard."""
        # Create operational dashboard
        dashboard = await monitor.create_operational_dashboard()
        
        assert dashboard.name == "Operational Dashboard"
        assert len(dashboard.widgets) == 4  # Pre-configured widgets
        
        # Verify widget types
        widget_titles = {w.title for w in dashboard.widgets}
        assert "System CPU Usage" in widget_titles
        assert "System Memory Usage" in widget_titles
        assert "HTTP Request Rate" in widget_titles
        assert "AI Model Performance" in widget_titles
    
    @pytest.mark.asyncio
    async def test_monitoring_health(self, monitor):
        """Test monitoring system health check."""
        # Setup default alerts
        await monitor.setup_default_alerts()
        
        # Get health status
        health = await monitor.get_monitoring_health()
        
        assert "status" in health
        assert "active_alerts" in health
        assert "registered_metrics" in health
        assert "dashboards" in health
        assert health["registered_metrics"] > 0  # Should have built-in metrics


@pytest.mark.asyncio
async def test_integrated_enterprise_operations():
    """Test integrated enterprise operations workflow."""
    # Initialize all components
    feature_flag_manager = FeatureFlagManager()
    deployment_manager = DeploymentManager(feature_flag_manager=feature_flag_manager)
    config_manager = EnterpriseConfigManager()
    monitor = EnterpriseMonitor()
    
    await deployment_manager.start_monitoring()
    await monitor.start()
    
    try:
        # 1. Setup configuration
        await config_manager.set_config(
            key="new_feature_enabled",
            value=False,
            scope=ConfigScope.GLOBAL
        )
        
        # 2. Create feature flag for gradual rollout
        await feature_flag_manager.register_flag(
            key="new_feature_rollout",
            name="New Feature Rollout",
            description="Gradual rollout of new feature",
            default_value=False,
            percentage_rollout=10.0
        )
        
        # 3. Create canary deployment
        deployment = await deployment_manager.create_deployment(
            version="v2.0.0",
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY,
            created_by="ops_team"
        )
        
        # 4. Record deployment metrics
        await monitor.record_metric(
            "deployment_status",
            1.0,  # Success
            {"environment": "production", "version": "v2.0.0"}
        )
        
        # 5. Test feature flag evaluation
        user_enabled = await feature_flag_manager.is_enabled(
            "new_feature_rollout",
            user_id="test_user_123"
        )
        
        # 6. Record feature flag metrics
        await monitor.record_metric(
            "feature_flag_evaluations",
            1,
            {"flag": "new_feature_rollout", "variation": str(user_enabled)}
        )
        
        # 7. Verify everything works together
        assert deployment.status == DeploymentStatus.PENDING
        
        # Configuration should be accessible
        config_value = await config_manager.get_config(
            "new_feature_enabled",
            ConfigScope.GLOBAL
        )
        assert config_value is False
        
        # Metrics should be recorded
        flag_metrics = await monitor.query_metrics(
            "feature_flag_evaluations",
            duration_hours=1
        )
        assert len(flag_metrics) >= 1
        
        deployment_metrics = await monitor.query_metrics(
            "deployment_status",
            duration_hours=1
        )
        assert len(deployment_metrics) >= 1
        
    finally:
        await deployment_manager.stop_monitoring()
        await monitor.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])