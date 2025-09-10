"""Model versioning and lifecycle management system.

This module provides comprehensive model versioning capabilities including:
- Semantic versioning for AI models
- Model deployment and rollback
- Version comparison and analytics
- Lifecycle management with automated policies
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model deployment status."""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class VersionPolicy(str, Enum):
    """Model versioning policies."""
    
    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes, optimizations


@dataclass
class ModelVersion:
    """Model version metadata."""
    
    version: str
    model_name: str
    provider: str
    status: ModelStatus
    created_at: datetime
    config_hash: str
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @property
    def semantic_version(self) -> tuple[int, int, int]:
        """Parse semantic version."""
        parts = self.version.split('.')
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    
    def is_compatible_with(self, other: 'ModelVersion') -> bool:
        """Check version compatibility."""
        self_major, self_minor, _ = self.semantic_version
        other_major, other_minor, _ = other.semantic_version
        
        # Same major version and at least same minor version
        return self_major == other_major and self_minor >= other_minor


class ModelDeployment(BaseModel):
    """Model deployment configuration."""
    
    version: str
    replicas: int = 1
    resources: Dict[str, str] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    health_check: Dict[str, Any] = Field(default_factory=dict)
    rollout_strategy: str = "rolling"
    traffic_split: Dict[str, float] = Field(default_factory=dict)


class ModelVersionManager:
    """Manages model versions and deployments."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("model_versions")
        self.storage_path.mkdir(exist_ok=True)
        self.versions: Dict[str, List[ModelVersion]] = {}
        self.deployments: Dict[str, ModelDeployment] = {}
        self._load_versions()
    
    def _load_versions(self) -> None:
        """Load versions from storage."""
        versions_file = self.storage_path / "versions.json"
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                    for model_name, version_list in data.items():
                        self.versions[model_name] = [
                            ModelVersion(
                                version=v['version'],
                                model_name=v['model_name'],
                                provider=v['provider'],
                                status=ModelStatus(v['status']),
                                created_at=datetime.fromisoformat(v['created_at']),
                                config_hash=v['config_hash'],
                                performance_metrics=v.get('performance_metrics', {}),
                                deployment_config=v.get('deployment_config', {}),
                                metadata=v.get('metadata', {}),
                                tags=v.get('tags', [])
                            )
                            for v in version_list
                        ]
            except Exception as e:
                logger.error(f"Failed to load versions: {e}")
    
    def _save_versions(self) -> None:
        """Save versions to storage."""
        versions_file = self.storage_path / "versions.json"
        try:
            data = {}
            for model_name, version_list in self.versions.items():
                data[model_name] = [
                    {
                        'version': v.version,
                        'model_name': v.model_name,
                        'provider': v.provider,
                        'status': v.status.value,
                        'created_at': v.created_at.isoformat(),
                        'config_hash': v.config_hash,
                        'performance_metrics': v.performance_metrics,
                        'deployment_config': v.deployment_config,
                        'metadata': v.metadata,
                        'tags': v.tags
                    }
                    for v in version_list
                ]
            
            with open(versions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save versions: {e}")
    
    def create_version(
        self,
        model_name: str,
        provider: str,
        config: Dict[str, Any],
        policy: VersionPolicy = VersionPolicy.PATCH,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelVersion:
        """Create a new model version."""
        # Calculate config hash
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
        # Determine version number
        current_versions = self.versions.get(model_name, [])
        if not current_versions:
            version = "1.0.0"
        else:
            latest = max(current_versions, key=lambda v: v.semantic_version)
            major, minor, patch = latest.semantic_version
            
            if policy == VersionPolicy.MAJOR:
                version = f"{major + 1}.0.0"
            elif policy == VersionPolicy.MINOR:
                version = f"{major}.{minor + 1}.0"
            else:  # PATCH
                version = f"{major}.{minor}.{patch + 1}"
        
        # Create version
        model_version = ModelVersion(
            version=version,
            model_name=model_name,
            provider=provider,
            status=ModelStatus.DEVELOPMENT,
            created_at=datetime.now(),
            config_hash=config_hash,
            deployment_config=config,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Store version
        if model_name not in self.versions:
            self.versions[model_name] = []
        self.versions[model_name].append(model_version)
        self._save_versions()
        
        logger.info(f"Created version {version} for model {model_name}")
        return model_version
    
    def get_version(self, model_name: str, version: str) -> Optional[ModelVersion]:
        """Get specific model version."""
        versions = self.versions.get(model_name, [])
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def get_latest_version(
        self,
        model_name: str,
        status: Optional[ModelStatus] = None
    ) -> Optional[ModelVersion]:
        """Get latest version of a model."""
        versions = self.versions.get(model_name, [])
        if status:
            versions = [v for v in versions if v.status == status]
        
        if not versions:
            return None
        
        return max(versions, key=lambda v: v.semantic_version)
    
    def get_production_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get current production version."""
        return self.get_latest_version(model_name, ModelStatus.PRODUCTION)
    
    def list_versions(
        self,
        model_name: str,
        status: Optional[ModelStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModelVersion]:
        """List model versions with optional filtering."""
        versions = self.versions.get(model_name, [])
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        if tags:
            versions = [
                v for v in versions
                if any(tag in v.tags for tag in tags)
            ]
        
        # Sort by semantic version (newest first)
        return sorted(versions, key=lambda v: v.semantic_version, reverse=True)
    
    def promote_version(
        self,
        model_name: str,
        version: str,
        target_status: ModelStatus
    ) -> bool:
        """Promote version to target status."""
        model_version = self.get_version(model_name, version)
        if not model_version:
            logger.error(f"Version {version} not found for model {model_name}")
            return False
        
        # Validation rules
        if target_status == ModelStatus.PRODUCTION:
            if model_version.status != ModelStatus.STAGING:
                logger.error("Can only promote staging versions to production")
                return False
        
        # Demote current production if promoting new production
        if target_status == ModelStatus.PRODUCTION:
            current_prod = self.get_production_version(model_name)
            if current_prod and current_prod.version != version:
                current_prod.status = ModelStatus.DEPRECATED
        
        model_version.status = target_status
        self._save_versions()
        
        logger.info(f"Promoted {model_name} v{version} to {target_status.value}")
        return True
    
    def rollback_to_version(self, model_name: str, version: str) -> bool:
        """Rollback to a specific version."""
        target_version = self.get_version(model_name, version)
        if not target_version:
            logger.error(f"Version {version} not found for model {model_name}")
            return False
        
        if target_version.status == ModelStatus.ARCHIVED:
            logger.error("Cannot rollback to archived version")
            return False
        
        # Demote current production
        current_prod = self.get_production_version(model_name)
        if current_prod:
            current_prod.status = ModelStatus.DEPRECATED
        
        # Promote target to production
        target_version.status = ModelStatus.PRODUCTION
        self._save_versions()
        
        logger.info(f"Rolled back {model_name} to version {version}")
        return True
    
    def archive_old_versions(
        self,
        model_name: str,
        keep_count: int = 5,
        min_age_days: int = 30
    ) -> List[str]:
        """Archive old versions based on policies."""
        versions = self.list_versions(model_name)
        cutoff_date = datetime.now() - timedelta(days=min_age_days)
        archived = []
        
        # Keep latest versions and recent versions
        for i, version in enumerate(versions):
            if (
                i >= keep_count and
                version.created_at < cutoff_date and
                version.status not in [ModelStatus.PRODUCTION, ModelStatus.STAGING]
            ):
                version.status = ModelStatus.ARCHIVED
                archived.append(version.version)
        
        if archived:
            self._save_versions()
            logger.info(f"Archived versions for {model_name}: {archived}")
        
        return archived
    
    def get_version_comparison(
        self,
        model_name: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two versions."""
        v1 = self.get_version(model_name, version1)
        v2 = self.get_version(model_name, version2)
        
        if not v1 or not v2:
            return {}
        
        comparison = {
            'versions': {
                'v1': version1,
                'v2': version2
            },
            'compatibility': v1.is_compatible_with(v2),
            'config_changes': v1.config_hash != v2.config_hash,
            'performance_diff': {},
            'metadata_diff': {}
        }
        
        # Compare performance metrics
        for metric in set(v1.performance_metrics.keys()) | set(v2.performance_metrics.keys()):
            val1 = v1.performance_metrics.get(metric, 0)
            val2 = v2.performance_metrics.get(metric, 0)
            if val1 != 0:
                comparison['performance_diff'][metric] = {
                    'v1': val1,
                    'v2': val2,
                    'change_percent': ((val2 - val1) / val1) * 100 if val1 != 0 else 0
                }
        
        return comparison
    
    def update_performance_metrics(
        self,
        model_name: str,
        version: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Update performance metrics for a version."""
        model_version = self.get_version(model_name, version)
        if not model_version:
            return False
        
        model_version.performance_metrics.update(metrics)
        self._save_versions()
        return True
    
    async def deploy_version(
        self,
        model_name: str,
        version: str,
        deployment_config: ModelDeployment
    ) -> bool:
        """Deploy a specific version."""
        model_version = self.get_version(model_name, version)
        if not model_version:
            logger.error(f"Version {version} not found for model {model_name}")
            return False
        
        deployment_key = f"{model_name}:{version}"
        self.deployments[deployment_key] = deployment_config
        
        # Simulate deployment process
        logger.info(f"Deploying {deployment_key} with strategy {deployment_config.rollout_strategy}")
        
        # Update version status if successful
        if model_version.status == ModelStatus.DEVELOPMENT:
            model_version.status = ModelStatus.STAGING
            self._save_versions()
        
        return True
    
    def get_deployment_status(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get deployment status for a version."""
        deployment_key = f"{model_name}:{version}"
        deployment = self.deployments.get(deployment_key)
        
        if not deployment:
            return None
        
        return {
            'version': version,
            'replicas': deployment.replicas,
            'health': "healthy",  # Would integrate with actual health checks
            'traffic_split': deployment.traffic_split,
            'uptime': "99.9%"  # Would integrate with monitoring
        }