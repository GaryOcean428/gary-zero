"""
Enterprise Deployment Management Framework.

Provides advanced deployment strategies including canary deployments,
blue-green deployments, and automated rollback capabilities.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategy types."""
    ROLLING = "rolling"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    IMMEDIATE = "immediate"
    PERCENTAGE = "percentage"


class DeploymentStatus(Enum):
    """Deployment status lifecycle."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CANARY_TESTING = "canary_testing"
    PROMOTING = "promoting"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"
    PREVIEW = "preview"


@dataclass
class DeploymentConfig:
    """Configuration for deployment strategies."""
    strategy: DeploymentStrategy
    environment: Environment
    canary_percentage: float = 5.0  # For canary deployments
    rollout_duration: int = 300  # Seconds for gradual rollout
    health_check_interval: int = 30  # Health check frequency
    success_threshold: float = 99.0  # Success rate threshold
    auto_promote: bool = False  # Auto-promote successful canary
    auto_rollback: bool = True  # Auto-rollback on failure
    notification_webhooks: List[str] = None
    
    def __post_init__(self):
        if self.notification_webhooks is None:
            self.notification_webhooks = []


@dataclass
class DeploymentMetrics:
    """Real-time deployment metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 100.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)
    
    def update_metrics(self, request_success: bool, response_time: float):
        """Update metrics with new request data."""
        self.total_requests += 1
        if request_success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update averages
        self.avg_response_time = (
            (self.avg_response_time * (self.total_requests - 1) + response_time) 
            / self.total_requests
        )
        
        self.error_rate = (self.failed_requests / self.total_requests) * 100
        self.success_rate = (self.successful_requests / self.total_requests) * 100
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class Deployment:
    """Deployment instance with full lifecycle tracking."""
    id: str
    version: str
    strategy: DeploymentStrategy
    environment: Environment
    status: DeploymentStatus
    config: DeploymentConfig
    metrics: DeploymentMetrics
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = "system"
    artifacts: Dict[str, Any] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.logs is None:
            self.logs = []
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log entry to the deployment."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        logger.info(f"Deployment {self.id}: {message}")


class DeploymentBackend(ABC):
    """Abstract backend for deployment storage and orchestration."""
    
    @abstractmethod
    async def store_deployment(self, deployment: Deployment) -> bool:
        """Store deployment information."""
        pass
    
    @abstractmethod
    async def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get deployment by ID."""
        pass
    
    @abstractmethod
    async def list_deployments(
        self, 
        environment: Optional[Environment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[Deployment]:
        """List deployments with optional filtering."""
        pass
    
    @abstractmethod
    async def deploy_version(
        self, 
        version: str, 
        environment: Environment,
        config: DeploymentConfig
    ) -> bool:
        """Execute the actual deployment."""
        pass
    
    @abstractmethod
    async def get_health_status(self, environment: Environment) -> Dict[str, Any]:
        """Get health status for an environment."""
        pass


class InMemoryDeploymentBackend(DeploymentBackend):
    """In-memory deployment backend for development and testing."""
    
    def __init__(self):
        self._deployments: Dict[str, Deployment] = {}
        self._environment_health: Dict[Environment, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def store_deployment(self, deployment: Deployment) -> bool:
        async with self._lock:
            self._deployments[deployment.id] = deployment
            return True
    
    async def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        async with self._lock:
            return self._deployments.get(deployment_id)
    
    async def list_deployments(
        self, 
        environment: Optional[Environment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[Deployment]:
        async with self._lock:
            deployments = list(self._deployments.values())
            
            if environment:
                deployments = [d for d in deployments if d.environment == environment]
            
            if status:
                deployments = [d for d in deployments if d.status == status]
            
            return sorted(deployments, key=lambda d: d.created_at, reverse=True)
    
    async def deploy_version(
        self, 
        version: str, 
        environment: Environment,
        config: DeploymentConfig
    ) -> bool:
        # Simulate deployment process
        await asyncio.sleep(1)
        return True
    
    async def get_health_status(self, environment: Environment) -> Dict[str, Any]:
        return self._environment_health.get(environment, {
            "healthy": True,
            "response_time": 50.0,
            "error_rate": 0.0,
            "last_check": datetime.now(timezone.utc).isoformat()
        })


class CanaryDeployment:
    """
    Canary deployment implementation with automatic monitoring and promotion.
    """
    
    def __init__(
        self,
        deployment_id: str,
        canary_percentage: float,
        promotion_criteria: Dict[str, float],
        monitoring_duration: int = 300
    ):
        self.deployment_id = deployment_id
        self.canary_percentage = canary_percentage
        self.promotion_criteria = promotion_criteria
        self.monitoring_duration = monitoring_duration
        self.start_time = datetime.now(timezone.utc)
        self.metrics = DeploymentMetrics()
        
    async def should_promote(self) -> bool:
        """Determine if canary should be promoted based on criteria."""
        # Check if monitoring duration has passed
        elapsed = (datetime.now(timezone.utc) - self.start_time).seconds
        if elapsed < self.monitoring_duration:
            return False
        
        # Check promotion criteria
        success_rate_threshold = self.promotion_criteria.get("success_rate", 95.0)
        error_rate_threshold = self.promotion_criteria.get("error_rate", 5.0)
        response_time_threshold = self.promotion_criteria.get("response_time", 1000.0)
        
        if self.metrics.success_rate < success_rate_threshold:
            return False
        
        if self.metrics.error_rate > error_rate_threshold:
            return False
        
        if self.metrics.avg_response_time > response_time_threshold:
            return False
        
        return True
    
    async def should_rollback(self) -> bool:
        """Determine if canary should be rolled back due to issues."""
        critical_error_rate = self.promotion_criteria.get("critical_error_rate", 10.0)
        critical_response_time = self.promotion_criteria.get("critical_response_time", 5000.0)
        
        if self.metrics.error_rate > critical_error_rate:
            return True
        
        if self.metrics.avg_response_time > critical_response_time:
            return True
        
        return False


class DeploymentManager:
    """
    Enterprise deployment manager with advanced strategies and monitoring.
    
    Features:
    - Multiple deployment strategies (rolling, canary, blue-green)
    - Automated health monitoring and rollback
    - Real-time metrics and alerting
    - Integration with feature flags for traffic routing
    - Deployment history and audit trails
    """
    
    def __init__(
        self,
        backend: Optional[DeploymentBackend] = None,
        feature_flag_manager: Optional[Any] = None
    ):
        self.backend = backend or InMemoryDeploymentBackend()
        self.feature_flag_manager = feature_flag_manager
        
        # Active deployments tracking
        self._active_deployments: Dict[str, Deployment] = {}
        self._canary_deployments: Dict[str, CanaryDeployment] = {}
        self._deployment_callbacks: List[Callable] = []
        
        # Background monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("DeploymentManager initialized")
    
    async def start_monitoring(self):
        """Start background monitoring for active deployments."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Started deployment monitoring")
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        if self._monitoring_task:
            self._shutdown_event.set()
            await self._monitoring_task
            self._monitoring_task = None
            logger.info("Stopped deployment monitoring")
    
    async def create_deployment(
        self,
        version: str,
        environment: Environment,
        strategy: DeploymentStrategy,
        config: Optional[DeploymentConfig] = None,
        created_by: str = "system"
    ) -> Deployment:
        """Create a new deployment."""
        deployment_id = f"deploy-{version}-{int(time.time())}"
        
        if config is None:
            config = DeploymentConfig(strategy=strategy, environment=environment)
        
        deployment = Deployment(
            id=deployment_id,
            version=version,
            strategy=strategy,
            environment=environment,
            status=DeploymentStatus.PENDING,
            config=config,
            metrics=DeploymentMetrics(),
            created_at=datetime.now(timezone.utc),
            created_by=created_by
        )
        
        await self.backend.store_deployment(deployment)
        deployment.add_log(f"Deployment created for version {version}")
        
        return deployment
    
    async def execute_deployment(self, deployment_id: str) -> bool:
        """Execute a deployment with the configured strategy."""
        deployment = await self.backend.get_deployment(deployment_id)
        if not deployment:
            logger.error(f"Deployment not found: {deployment_id}")
            return False
        
        try:
            deployment.status = DeploymentStatus.IN_PROGRESS
            deployment.started_at = datetime.now(timezone.utc)
            deployment.add_log("Starting deployment execution")
            
            await self.backend.store_deployment(deployment)
            self._active_deployments[deployment_id] = deployment
            
            # Execute strategy-specific deployment
            success = await self._execute_strategy(deployment)
            
            if success:
                if deployment.strategy == DeploymentStrategy.CANARY:
                    deployment.status = DeploymentStatus.CANARY_TESTING
                    deployment.add_log("Canary deployment in progress, monitoring...")
                    await self._setup_canary_monitoring(deployment)
                else:
                    deployment.status = DeploymentStatus.COMPLETED
                    deployment.completed_at = datetime.now(timezone.utc)
                    deployment.add_log("Deployment completed successfully")
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.add_log("Deployment failed")
                
                if deployment.config.auto_rollback:
                    await self._rollback_deployment(deployment)
            
            await self.backend.store_deployment(deployment)
            await self._notify_deployment_status(deployment)
            
            return success
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.add_log(f"Deployment error: {str(e)}")
            await self.backend.store_deployment(deployment)
            logger.error(f"Deployment execution failed: {e}")
            return False
    
    async def _execute_strategy(self, deployment: Deployment) -> bool:
        """Execute deployment based on strategy."""
        if deployment.strategy == DeploymentStrategy.IMMEDIATE:
            return await self._execute_immediate_deployment(deployment)
        
        elif deployment.strategy == DeploymentStrategy.ROLLING:
            return await self._execute_rolling_deployment(deployment)
        
        elif deployment.strategy == DeploymentStrategy.CANARY:
            return await self._execute_canary_deployment(deployment)
        
        elif deployment.strategy == DeploymentStrategy.BLUE_GREEN:
            return await self._execute_blue_green_deployment(deployment)
        
        elif deployment.strategy == DeploymentStrategy.PERCENTAGE:
            return await self._execute_percentage_deployment(deployment)
        
        else:
            deployment.add_log(f"Unknown deployment strategy: {deployment.strategy}")
            return False
    
    async def _execute_immediate_deployment(self, deployment: Deployment) -> bool:
        """Execute immediate deployment to all instances."""
        deployment.add_log("Executing immediate deployment")
        
        success = await self.backend.deploy_version(
            deployment.version,
            deployment.environment,
            deployment.config
        )
        
        if success:
            deployment.add_log("Immediate deployment successful")
        else:
            deployment.add_log("Immediate deployment failed")
        
        return success
    
    async def _execute_rolling_deployment(self, deployment: Deployment) -> bool:
        """Execute rolling deployment with gradual instance updates."""
        deployment.add_log("Starting rolling deployment")
        
        # Simulate rolling deployment phases
        phases = ["25%", "50%", "75%", "100%"]
        
        for phase in phases:
            deployment.add_log(f"Rolling deployment phase: {phase}")
            
            # Simulate deployment to percentage of instances
            await asyncio.sleep(deployment.config.rollout_duration / len(phases))
            
            # Check health after each phase
            health = await self.backend.get_health_status(deployment.environment)
            if not health.get("healthy", False):
                deployment.add_log(f"Health check failed at {phase}")
                return False
            
            deployment.add_log(f"Phase {phase} completed successfully")
        
        deployment.add_log("Rolling deployment completed")
        return True
    
    async def _execute_canary_deployment(self, deployment: Deployment) -> bool:
        """Execute canary deployment with traffic splitting."""
        deployment.add_log(f"Starting canary deployment with {deployment.config.canary_percentage}% traffic")
        
        # Deploy to canary environment
        success = await self.backend.deploy_version(
            deployment.version,
            Environment.CANARY,
            deployment.config
        )
        
        if not success:
            deployment.add_log("Canary deployment failed")
            return False
        
        # Setup traffic routing via feature flags
        if self.feature_flag_manager:
            await self._setup_canary_traffic_routing(deployment)
        
        deployment.add_log("Canary deployment successful, monitoring started")
        return True
    
    async def _execute_blue_green_deployment(self, deployment: Deployment) -> bool:
        """Execute blue-green deployment with environment swapping."""
        deployment.add_log("Starting blue-green deployment")
        
        # Deploy to "green" environment
        green_env = Environment.STAGING if deployment.environment == Environment.PRODUCTION else Environment.PREVIEW
        
        success = await self.backend.deploy_version(
            deployment.version,
            green_env,
            deployment.config
        )
        
        if not success:
            deployment.add_log("Green environment deployment failed")
            return False
        
        # Health check green environment
        await asyncio.sleep(30)  # Allow warmup
        health = await self.backend.get_health_status(green_env)
        
        if not health.get("healthy", False):
            deployment.add_log("Green environment health check failed")
            return False
        
        # Switch traffic (simulated)
        deployment.add_log("Switching traffic to green environment")
        await asyncio.sleep(5)
        
        deployment.add_log("Blue-green deployment completed")
        return True
    
    async def _execute_percentage_deployment(self, deployment: Deployment) -> bool:
        """Execute percentage-based gradual rollout."""
        deployment.add_log("Starting percentage-based deployment")
        
        # Gradual percentage increase
        percentages = [10, 25, 50, 75, 100]
        
        for percentage in percentages:
            deployment.add_log(f"Rolling out to {percentage}% of traffic")
            
            # Update feature flag for traffic routing
            if self.feature_flag_manager:
                flag_key = f"deployment_{deployment.version}_traffic"
                await self.feature_flag_manager.update_flag(
                    flag_key,
                    percentage_rollout=percentage
                )
            
            # Monitor for issues
            await asyncio.sleep(deployment.config.rollout_duration / len(percentages))
            
            health = await self.backend.get_health_status(deployment.environment)
            if not health.get("healthy", False):
                deployment.add_log(f"Health check failed at {percentage}%")
                return False
        
        deployment.add_log("Percentage deployment completed")
        return True
    
    async def _setup_canary_monitoring(self, deployment: Deployment):
        """Setup monitoring for canary deployment."""
        promotion_criteria = {
            "success_rate": deployment.config.success_threshold,
            "error_rate": 100.0 - deployment.config.success_threshold,
            "response_time": 1000.0,
            "critical_error_rate": 10.0,
            "critical_response_time": 5000.0
        }
        
        canary = CanaryDeployment(
            deployment.id,
            deployment.config.canary_percentage,
            promotion_criteria,
            monitoring_duration=300
        )
        
        self._canary_deployments[deployment.id] = canary
    
    async def _setup_canary_traffic_routing(self, deployment: Deployment):
        """Setup feature flag for canary traffic routing."""
        if not self.feature_flag_manager:
            return
        
        flag_key = f"canary_{deployment.version}"
        
        await self.feature_flag_manager.register_flag(
            key=flag_key,
            name=f"Canary Traffic for {deployment.version}",
            description=f"Routes traffic to canary deployment of version {deployment.version}",
            default_value=False,
            percentage_rollout=deployment.config.canary_percentage
        )
        
        deployment.add_log(f"Created feature flag for canary traffic routing: {flag_key}")
    
    async def _monitoring_loop(self):
        """Background loop for monitoring active deployments."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_canary_deployments()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    async def _check_canary_deployments(self):
        """Check canary deployments for promotion or rollback."""
        for deployment_id, canary in list(self._canary_deployments.items()):
            deployment = await self.backend.get_deployment(deployment_id)
            if not deployment:
                continue
            
            # Update metrics (simulated)
            await self._update_canary_metrics(canary, deployment)
            
            # Check for promotion
            if await canary.should_promote():
                await self._promote_canary(deployment, canary)
                del self._canary_deployments[deployment_id]
            
            # Check for rollback
            elif await canary.should_rollback():
                await self._rollback_deployment(deployment)
                del self._canary_deployments[deployment_id]
    
    async def _update_canary_metrics(self, canary: CanaryDeployment, deployment: Deployment):
        """Update metrics for canary deployment (simulated)."""
        # Simulate metrics update
        import random
        
        # Simulate request
        success = random.random() > 0.02  # 98% success rate
        response_time = random.uniform(50, 200)  # 50-200ms response time
        
        canary.metrics.update_metrics(success, response_time)
        deployment.metrics = canary.metrics
        
        await self.backend.store_deployment(deployment)
    
    async def _promote_canary(self, deployment: Deployment, canary: CanaryDeployment):
        """Promote canary deployment to full production."""
        deployment.status = DeploymentStatus.PROMOTING
        deployment.add_log("Promoting canary deployment to production")
        
        # Execute full deployment
        success = await self.backend.deploy_version(
            deployment.version,
            deployment.environment,
            deployment.config
        )
        
        if success:
            deployment.status = DeploymentStatus.COMPLETED
            deployment.completed_at = datetime.now(timezone.utc)
            deployment.add_log("Canary promotion completed successfully")
        else:
            deployment.status = DeploymentStatus.FAILED
            deployment.add_log("Canary promotion failed")
        
        await self.backend.store_deployment(deployment)
        await self._notify_deployment_status(deployment)
    
    async def _rollback_deployment(self, deployment: Deployment):
        """Rollback a failed deployment."""
        deployment.status = DeploymentStatus.ROLLING_BACK
        deployment.add_log("Starting deployment rollback")
        
        # Get previous successful deployment
        deployments = await self.backend.list_deployments(
            environment=deployment.environment,
            status=DeploymentStatus.COMPLETED
        )
        
        if deployments:
            previous_deployment = deployments[0]  # Most recent successful
            
            # Rollback to previous version
            success = await self.backend.deploy_version(
                previous_deployment.version,
                deployment.environment,
                deployment.config
            )
            
            if success:
                deployment.status = DeploymentStatus.ROLLED_BACK
                deployment.add_log(f"Rollback to version {previous_deployment.version} completed")
            else:
                deployment.add_log("Rollback failed")
        else:
            deployment.add_log("No previous deployment found for rollback")
        
        await self.backend.store_deployment(deployment)
        await self._notify_deployment_status(deployment)
    
    async def _notify_deployment_status(self, deployment: Deployment):
        """Send notifications about deployment status."""
        for webhook in deployment.config.notification_webhooks:
            try:
                # Simulate webhook notification
                notification_data = {
                    "deployment_id": deployment.id,
                    "version": deployment.version,
                    "environment": deployment.environment.value,
                    "status": deployment.status.value,
                    "metrics": asdict(deployment.metrics)
                }
                
                deployment.add_log(f"Sent notification to {webhook}")
                
            except Exception as e:
                deployment.add_log(f"Failed to send notification to {webhook}: {e}")
        
        # Execute callbacks
        for callback in self._deployment_callbacks:
            try:
                await callback(deployment)
            except Exception as e:
                logger.warning(f"Deployment callback error: {e}")
    
    def add_deployment_callback(self, callback: Callable):
        """Add callback for deployment events."""
        self._deployment_callbacks.append(callback)
    
    def remove_deployment_callback(self, callback: Callable):
        """Remove deployment callback."""
        if callback in self._deployment_callbacks:
            self._deployment_callbacks.remove(callback)
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed deployment status."""
        deployment = await self.backend.get_deployment(deployment_id)
        if not deployment:
            return None
        
        status = asdict(deployment)
        
        # Add canary-specific information
        if deployment_id in self._canary_deployments:
            canary = self._canary_deployments[deployment_id]
            status["canary_metrics"] = asdict(canary.metrics)
            status["monitoring_duration"] = canary.monitoring_duration
            status["promotion_criteria"] = canary.promotion_criteria
        
        return status
    
    async def list_deployments(
        self,
        environment: Optional[Environment] = None,
        status: Optional[DeploymentStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List deployments with optional filtering."""
        deployments = await self.backend.list_deployments(environment, status)
        return [asdict(d) for d in deployments[:limit]]
    
    async def abort_deployment(self, deployment_id: str) -> bool:
        """Abort an active deployment."""
        deployment = await self.backend.get_deployment(deployment_id)
        if not deployment:
            return False
        
        if deployment.status not in [DeploymentStatus.IN_PROGRESS, DeploymentStatus.CANARY_TESTING]:
            return False
        
        deployment.add_log("Deployment aborted by user")
        
        if deployment.config.auto_rollback:
            await self._rollback_deployment(deployment)
        else:
            deployment.status = DeploymentStatus.FAILED
            await self.backend.store_deployment(deployment)
        
        # Cleanup
        if deployment_id in self._canary_deployments:
            del self._canary_deployments[deployment_id]
        
        if deployment_id in self._active_deployments:
            del self._active_deployments[deployment_id]
        
        return True


# Convenience functions
async def quick_deploy(
    manager: DeploymentManager,
    version: str,
    environment: Environment,
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
) -> str:
    """Quick deployment with default configuration."""
    deployment = await manager.create_deployment(version, environment, strategy)
    await manager.execute_deployment(deployment.id)
    return deployment.id


async def canary_deploy(
    manager: DeploymentManager,
    version: str,
    environment: Environment,
    percentage: float = 5.0,
    auto_promote: bool = True
) -> str:
    """Create and execute a canary deployment."""
    config = DeploymentConfig(
        strategy=DeploymentStrategy.CANARY,
        environment=environment,
        canary_percentage=percentage,
        auto_promote=auto_promote
    )
    
    deployment = await manager.create_deployment(version, environment, DeploymentStrategy.CANARY, config)
    await manager.execute_deployment(deployment.id)
    return deployment.id