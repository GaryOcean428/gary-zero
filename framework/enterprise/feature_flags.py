"""
Enterprise Feature Flag Framework.

Provides advanced feature flag capabilities with percentage rollouts,
user targeting, A/B testing integration, and real-time configuration updates.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TargetingStrategy(Enum):
    """Feature flag targeting strategies."""
    PERCENTAGE = "percentage"
    USER_ID = "user_id"
    ATTRIBUTE = "attribute"
    SEGMENT = "segment"
    TIME_WINDOW = "time_window"
    GEOGRAPHIC = "geographic"


class FeatureFlagStatus(Enum):
    """Feature flag lifecycle status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


@dataclass
class TargetingRule:
    """Feature flag targeting rule configuration."""
    strategy: TargetingStrategy
    condition: str  # JSON condition for complex rules
    enabled: bool = True
    priority: int = 100
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FeatureFlag:
    """Feature flag configuration with advanced targeting."""
    key: str
    name: str
    description: str
    default_value: Any
    status: FeatureFlagStatus = FeatureFlagStatus.ACTIVE
    targeting_rules: List[TargetingRule] = None
    percentage_rollout: float = 0.0  # 0-100
    variations: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = "system"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.targeting_rules is None:
            self.targeting_rules = []
        if self.variations is None:
            self.variations = {"default": self.default_value}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.tags is None:
            self.tags = []


class FeatureFlagBackend(ABC):
    """Abstract backend for feature flag storage."""
    
    @abstractmethod
    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get feature flag by key."""
        pass
    
    @abstractmethod
    async def set_flag(self, flag: FeatureFlag) -> bool:
        """Store or update feature flag."""
        pass
    
    @abstractmethod
    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag."""
        pass
    
    @abstractmethod
    async def list_flags(self, status: Optional[FeatureFlagStatus] = None) -> List[FeatureFlag]:
        """List all feature flags with optional status filter."""
        pass


class InMemoryFeatureFlagBackend(FeatureFlagBackend):
    """In-memory feature flag backend for development and testing."""
    
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = asyncio.Lock()
    
    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        async with self._lock:
            return self._flags.get(key)
    
    async def set_flag(self, flag: FeatureFlag) -> bool:
        async with self._lock:
            flag.updated_at = datetime.now(timezone.utc)
            self._flags[flag.key] = flag
            return True
    
    async def delete_flag(self, key: str) -> bool:
        async with self._lock:
            if key in self._flags:
                del self._flags[key]
                return True
            return False
    
    async def list_flags(self, status: Optional[FeatureFlagStatus] = None) -> List[FeatureFlag]:
        async with self._lock:
            flags = list(self._flags.values())
            if status:
                flags = [f for f in flags if f.status == status]
            return flags


class FeatureFlagManager:
    """
    Enterprise feature flag manager with advanced targeting and rollout capabilities.
    
    Features:
    - Percentage-based rollouts with deterministic hashing
    - Complex user targeting with multiple strategies
    - A/B testing integration
    - Real-time flag updates
    - Performance monitoring and analytics
    """
    
    def __init__(
        self,
        backend: Optional[FeatureFlagBackend] = None,
        cache_ttl: int = 300,  # 5 minutes
        enable_analytics: bool = True
    ):
        self.backend = backend or InMemoryFeatureFlagBackend()
        self.cache_ttl = cache_ttl
        self.enable_analytics = enable_analytics
        
        # Local cache for performance
        self._cache: Dict[str, FeatureFlag] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        
        # Analytics and callbacks
        self._evaluation_callbacks: List[Callable] = []
        self._flag_usage_stats: Dict[str, Dict[str, int]] = {}
        
        logger.info("FeatureFlagManager initialized with caching and analytics")
    
    async def register_flag(
        self,
        key: str,
        name: str,
        description: str,
        default_value: Any,
        **kwargs
    ) -> FeatureFlag:
        """Register a new feature flag."""
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            default_value=default_value,
            **kwargs
        )
        
        await self.backend.set_flag(flag)
        await self._invalidate_cache(key)
        
        logger.info(f"Registered feature flag: {key}")
        return flag
    
    async def update_flag(
        self,
        key: str,
        **updates
    ) -> Optional[FeatureFlag]:
        """Update an existing feature flag."""
        flag = await self._get_flag_with_cache(key)
        if not flag:
            return None
        
        # Update flag attributes
        for attr, value in updates.items():
            if hasattr(flag, attr):
                setattr(flag, attr, value)
        
        flag.updated_at = datetime.now(timezone.utc)
        await self.backend.set_flag(flag)
        await self._invalidate_cache(key)
        
        logger.info(f"Updated feature flag: {key}")
        return flag
    
    async def is_enabled(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a feature flag is enabled for the given context."""
        result = await self.get_variation(key, user_id, user_attributes, context)
        return bool(result)
    
    async def get_variation(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get the variation value for a feature flag."""
        flag = await self._get_flag_with_cache(key)
        if not flag or flag.status != FeatureFlagStatus.ACTIVE:
            self._record_flag_usage(key, "default", "flag_inactive")
            return flag.default_value if flag else False
        
        # Evaluate targeting rules
        variation = await self._evaluate_targeting(flag, user_id, user_attributes, context)
        
        # Record analytics
        self._record_flag_usage(key, str(variation), "evaluated")
        
        # Execute callbacks
        for callback in self._evaluation_callbacks:
            try:
                await callback(key, variation, user_id, user_attributes, context)
            except Exception as e:
                logger.warning(f"Feature flag callback error: {e}")
        
        return variation
    
    async def _evaluate_targeting(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        user_attributes: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Evaluate targeting rules and determine variation."""
        user_attributes = user_attributes or {}
        context = context or {}
        
        # Sort rules by priority (lower number = higher priority)
        rules = sorted(flag.targeting_rules, key=lambda r: r.priority)
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if await self._evaluate_rule(rule, user_id, user_attributes, context):
                # Rule matched, determine variation
                return await self._get_rule_variation(flag, rule, user_id)
        
        # No rules matched, check percentage rollout
        if flag.percentage_rollout > 0 and user_id:
            if self._is_in_percentage_rollout(flag.key, user_id, flag.percentage_rollout):
                return flag.variations.get("enabled", True)
        
        return flag.default_value
    
    async def _evaluate_rule(
        self,
        rule: TargetingRule,
        user_id: Optional[str],
        user_attributes: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single targeting rule."""
        try:
            if rule.strategy == TargetingStrategy.PERCENTAGE:
                percentage = json.loads(rule.condition).get("percentage", 0)
                return user_id and self._is_in_percentage(user_id, percentage)
            
            elif rule.strategy == TargetingStrategy.USER_ID:
                user_ids = json.loads(rule.condition).get("user_ids", [])
                return user_id in user_ids
            
            elif rule.strategy == TargetingStrategy.ATTRIBUTE:
                condition = json.loads(rule.condition)
                return self._evaluate_attribute_condition(condition, user_attributes)
            
            elif rule.strategy == TargetingStrategy.TIME_WINDOW:
                return self._evaluate_time_window(json.loads(rule.condition))
            
            elif rule.strategy == TargetingStrategy.GEOGRAPHIC:
                return self._evaluate_geographic_condition(
                    json.loads(rule.condition), 
                    context.get("location", {})
                )
            
            return False
            
        except Exception as e:
            logger.warning(f"Error evaluating targeting rule: {e}")
            return False
    
    def _is_in_percentage_rollout(self, flag_key: str, user_id: str, percentage: float) -> bool:
        """Determine if user is in percentage rollout using consistent hashing."""
        return self._is_in_percentage(f"{flag_key}:{user_id}", percentage)
    
    def _is_in_percentage(self, key: str, percentage: float) -> bool:
        """Consistent percentage-based inclusion using hash."""
        hash_value = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
        return (hash_value % 100) < percentage
    
    def _evaluate_attribute_condition(
        self, 
        condition: Dict[str, Any], 
        attributes: Dict[str, Any]
    ) -> bool:
        """Evaluate attribute-based condition."""
        attr_name = condition.get("attribute")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")
        
        if attr_name not in attributes:
            return False
        
        actual_value = attributes[attr_name]
        
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "in":
            return actual_value in expected_value
        elif operator == "not_in":
            return actual_value not in expected_value
        elif operator == "greater_than":
            return actual_value > expected_value
        elif operator == "less_than":
            return actual_value < expected_value
        
        return False
    
    def _evaluate_time_window(self, condition: Dict[str, Any]) -> bool:
        """Evaluate time window condition."""
        now = datetime.now(timezone.utc)
        start_time = datetime.fromisoformat(condition.get("start", ""))
        end_time = datetime.fromisoformat(condition.get("end", ""))
        
        return start_time <= now <= end_time
    
    def _evaluate_geographic_condition(
        self, 
        condition: Dict[str, Any], 
        location: Dict[str, Any]
    ) -> bool:
        """Evaluate geographic condition."""
        allowed_countries = condition.get("countries", [])
        allowed_regions = condition.get("regions", [])
        
        user_country = location.get("country")
        user_region = location.get("region")
        
        if allowed_countries and user_country:
            return user_country in allowed_countries
        
        if allowed_regions and user_region:
            return user_region in allowed_regions
        
        return not allowed_countries and not allowed_regions
    
    async def _get_rule_variation(
        self, 
        flag: FeatureFlag, 
        rule: TargetingRule, 
        user_id: Optional[str]
    ) -> Any:
        """Get variation value for a matched rule."""
        variation_key = rule.metadata.get("variation", "default")
        return flag.variations.get(variation_key, flag.default_value)
    
    async def _get_flag_with_cache(self, key: str) -> Optional[FeatureFlag]:
        """Get flag with caching for performance."""
        async with self._lock:
            # Check cache validity
            if key in self._cache:
                cache_time = self._cache_timestamps.get(key)
                if cache_time and (datetime.now(timezone.utc) - cache_time).seconds < self.cache_ttl:
                    return self._cache[key]
            
            # Fetch from backend
            flag = await self.backend.get_flag(key)
            if flag:
                self._cache[key] = flag
                self._cache_timestamps[key] = datetime.now(timezone.utc)
            
            return flag
    
    async def _invalidate_cache(self, key: str):
        """Invalidate cache entry for a flag."""
        async with self._lock:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    def _record_flag_usage(self, key: str, variation: str, event: str):
        """Record flag usage for analytics."""
        if not self.enable_analytics:
            return
        
        if key not in self._flag_usage_stats:
            self._flag_usage_stats[key] = {}
        
        stat_key = f"{event}:{variation}"
        self._flag_usage_stats[key][stat_key] = (
            self._flag_usage_stats[key].get(stat_key, 0) + 1
        )
    
    def add_evaluation_callback(self, callback: Callable):
        """Add callback for flag evaluation events."""
        self._evaluation_callbacks.append(callback)
    
    def remove_evaluation_callback(self, callback: Callable):
        """Remove evaluation callback."""
        if callback in self._evaluation_callbacks:
            self._evaluation_callbacks.remove(callback)
    
    async def get_flag_stats(self, key: str) -> Dict[str, Any]:
        """Get usage statistics for a flag."""
        return self._flag_usage_stats.get(key, {})
    
    async def list_flags(
        self, 
        status: Optional[FeatureFlagStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[FeatureFlag]:
        """List feature flags with optional filtering."""
        flags = await self.backend.list_flags(status)
        
        if tags:
            flags = [f for f in flags if any(tag in f.tags for tag in tags)]
        
        return flags
    
    async def export_configuration(self) -> Dict[str, Any]:
        """Export complete feature flag configuration."""
        flags = await self.list_flags()
        return {
            "flags": [asdict(flag) for flag in flags],
            "export_time": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }
    
    async def import_configuration(self, config: Dict[str, Any]) -> bool:
        """Import feature flag configuration."""
        try:
            for flag_data in config.get("flags", []):
                # Convert datetime strings back to datetime objects
                if "created_at" in flag_data:
                    flag_data["created_at"] = datetime.fromisoformat(flag_data["created_at"])
                if "updated_at" in flag_data:
                    flag_data["updated_at"] = datetime.fromisoformat(flag_data["updated_at"])
                
                # Convert enum strings back to enums
                if "status" in flag_data:
                    flag_data["status"] = FeatureFlagStatus(flag_data["status"])
                
                # Convert targeting rules
                if "targeting_rules" in flag_data:
                    rules = []
                    for rule_data in flag_data["targeting_rules"]:
                        if "strategy" in rule_data:
                            rule_data["strategy"] = TargetingStrategy(rule_data["strategy"])
                        rules.append(TargetingRule(**rule_data))
                    flag_data["targeting_rules"] = rules
                
                flag = FeatureFlag(**flag_data)
                await self.backend.set_flag(flag)
                await self._invalidate_cache(flag.key)
            
            logger.info(f"Imported {len(config.get('flags', []))} feature flags")
            return True
            
        except Exception as e:
            logger.error(f"Error importing feature flag configuration: {e}")
            return False


# Convenience functions for common operations
async def create_percentage_flag(
    manager: FeatureFlagManager,
    key: str,
    name: str,
    description: str,
    percentage: float,
    default_value: Any = False
) -> FeatureFlag:
    """Create a percentage-based rollout flag."""
    return await manager.register_flag(
        key=key,
        name=name,
        description=description,
        default_value=default_value,
        percentage_rollout=percentage
    )


async def create_user_targeting_flag(
    manager: FeatureFlagManager,
    key: str,
    name: str,
    description: str,
    user_ids: List[str],
    default_value: Any = False
) -> FeatureFlag:
    """Create a user ID targeting flag."""
    rule = TargetingRule(
        strategy=TargetingStrategy.USER_ID,
        condition=json.dumps({"user_ids": user_ids}),
        priority=1
    )
    
    return await manager.register_flag(
        key=key,
        name=name,
        description=description,
        default_value=default_value,
        targeting_rules=[rule]
    )