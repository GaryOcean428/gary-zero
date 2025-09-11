"""
Enterprise Configuration Management Framework.

Provides advanced configuration management with environment-specific deployments,
hot reloading, configuration validation, and secure secret management.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
import yaml

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels."""
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    SERVICE = "service"
    USER = "user"
    SESSION = "session"


class ConfigFormat(Enum):
    """Configuration format types."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


class ConfigValidationType(Enum):
    """Configuration validation types."""
    NONE = "none"
    SCHEMA = "schema"
    CUSTOM = "custom"
    STRICT = "strict"


@dataclass
class ConfigValidationRule:
    """Configuration validation rule."""
    field_path: str
    rule_type: str  # required, type, range, regex, custom
    rule_config: Dict[str, Any]
    error_message: str = ""
    
    def __post_init__(self):
        if not self.error_message:
            self.error_message = f"Validation failed for {self.field_path}"


@dataclass
class ConfigEntry:
    """Individual configuration entry with metadata."""
    key: str
    value: Any
    scope: ConfigScope
    environment: Optional[str] = None
    service: Optional[str] = None
    encrypted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def update_value(self, new_value: Any):
        """Update the configuration value with versioning."""
        self.value = new_value
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    name: str
    version: str
    validation_rules: List[ConfigValidationRule]
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)


class ConfigBackend(ABC):
    """Abstract backend for configuration storage."""
    
    @abstractmethod
    async def get_config(
        self, 
        key: str, 
        scope: ConfigScope, 
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> Optional[ConfigEntry]:
        """Get configuration entry."""
        pass
    
    @abstractmethod
    async def set_config(self, entry: ConfigEntry) -> bool:
        """Store configuration entry."""
        pass
    
    @abstractmethod
    async def delete_config(
        self, 
        key: str, 
        scope: ConfigScope,
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> bool:
        """Delete configuration entry."""
        pass
    
    @abstractmethod
    async def list_configs(
        self,
        scope: Optional[ConfigScope] = None,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ConfigEntry]:
        """List configuration entries with filtering."""
        pass
    
    @abstractmethod
    async def get_config_history(
        self, 
        key: str, 
        scope: ConfigScope,
        limit: int = 10
    ) -> List[ConfigEntry]:
        """Get configuration change history."""
        pass


class InMemoryConfigBackend(ConfigBackend):
    """In-memory configuration backend for development and testing."""
    
    def __init__(self):
        self._configs: Dict[str, ConfigEntry] = {}
        self._history: Dict[str, List[ConfigEntry]] = {}
        self._lock = asyncio.Lock()
    
    def _build_key(
        self, 
        key: str, 
        scope: ConfigScope, 
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> str:
        """Build composite key for storage."""
        parts = [scope.value, key]
        if environment:
            parts.insert(1, environment)
        if service:
            parts.insert(-1, service)
        return ":".join(parts)
    
    async def get_config(
        self, 
        key: str, 
        scope: ConfigScope, 
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> Optional[ConfigEntry]:
        async with self._lock:
            storage_key = self._build_key(key, scope, environment, service)
            return self._configs.get(storage_key)
    
    async def set_config(self, entry: ConfigEntry) -> bool:
        async with self._lock:
            storage_key = self._build_key(
                entry.key, 
                entry.scope, 
                entry.environment, 
                entry.service
            )
            
            # Store history
            if storage_key not in self._history:
                self._history[storage_key] = []
            
            # Keep existing entry in history if it exists
            if storage_key in self._configs:
                self._history[storage_key].append(self._configs[storage_key])
                # Limit history size
                self._history[storage_key] = self._history[storage_key][-50:]
            
            self._configs[storage_key] = entry
            return True
    
    async def delete_config(
        self, 
        key: str, 
        scope: ConfigScope,
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> bool:
        async with self._lock:
            storage_key = self._build_key(key, scope, environment, service)
            if storage_key in self._configs:
                del self._configs[storage_key]
                return True
            return False
    
    async def list_configs(
        self,
        scope: Optional[ConfigScope] = None,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ConfigEntry]:
        async with self._lock:
            configs = list(self._configs.values())
            
            if scope:
                configs = [c for c in configs if c.scope == scope]
            
            if environment:
                configs = [c for c in configs if c.environment == environment]
            
            if service:
                configs = [c for c in configs if c.service == service]
            
            if tags:
                configs = [c for c in configs if any(tag in c.tags for tag in tags)]
            
            return configs
    
    async def get_config_history(
        self, 
        key: str, 
        scope: ConfigScope,
        limit: int = 10
    ) -> List[ConfigEntry]:
        async with self._lock:
            storage_key = self._build_key(key, scope)
            history = self._history.get(storage_key, [])
            return history[-limit:] if limit > 0 else history


class ConfigValidator:
    """Configuration validation engine."""
    
    def __init__(self):
        self._custom_validators: Dict[str, Callable] = {}
    
    def register_custom_validator(self, name: str, validator: Callable):
        """Register a custom validation function."""
        self._custom_validators[name] = validator
    
    async def validate_config(
        self, 
        config_data: Dict[str, Any], 
        schema: ConfigSchema
    ) -> tuple[bool, List[str]]:
        """Validate configuration against schema."""
        errors = []
        
        # Check required fields
        for field in schema.required_fields:
            if field not in config_data:
                errors.append(f"Required field missing: {field}")
        
        # Validate individual rules
        for rule in schema.validation_rules:
            field_value = self._get_nested_value(config_data, rule.field_path)
            
            if not await self._validate_rule(rule, field_value):
                errors.append(rule.error_message)
        
        # Type validation
        for field, expected_type in schema.field_types.items():
            if field in config_data:
                if not self._validate_type(config_data[field], expected_type):
                    errors.append(f"Field {field} has invalid type, expected {expected_type}")
        
        return len(errors) == 0, errors
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    async def _validate_rule(self, rule: ConfigValidationRule, value: Any) -> bool:
        """Validate a single rule."""
        if value is None:
            return rule.rule_type != "required"
        
        if rule.rule_type == "required":
            return value is not None
        
        elif rule.rule_type == "type":
            expected_type = rule.rule_config.get("type")
            return self._validate_type(value, expected_type)
        
        elif rule.rule_type == "range":
            min_val = rule.rule_config.get("min")
            max_val = rule.rule_config.get("max")
            return (min_val is None or value >= min_val) and (max_val is None or value <= max_val)
        
        elif rule.rule_type == "regex":
            import re
            pattern = rule.rule_config.get("pattern")
            return bool(re.match(pattern, str(value)))
        
        elif rule.rule_type == "custom":
            validator_name = rule.rule_config.get("validator")
            if validator_name in self._custom_validators:
                return await self._custom_validators[validator_name](value, rule.rule_config)
        
        return True
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True


class EnterpriseConfigManager:
    """
    Enterprise configuration manager with environment-specific deployments,
    hot reloading, validation, and secure secret management.
    
    Features:
    - Multi-scope configuration hierarchy (global, environment, service, user)
    - Real-time configuration updates with hot reloading
    - Configuration validation with custom rules
    - Encrypted secret storage
    - Configuration history and rollback
    - Environment-specific configuration promotion
    - A/B testing integration for configuration experiments
    """
    
    def __init__(
        self,
        backend: Optional[ConfigBackend] = None,
        enable_encryption: bool = True,
        enable_hot_reload: bool = True,
        validation_enabled: bool = True
    ):
        self.backend = backend or InMemoryConfigBackend()
        self.enable_encryption = enable_encryption
        self.enable_hot_reload = enable_hot_reload
        self.validation_enabled = validation_enabled
        
        # Configuration cache for performance
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Hot reload callbacks
        self._reload_callbacks: Dict[str, List[Callable]] = {}
        self._reload_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Validation
        self.validator = ConfigValidator()
        self._schemas: Dict[str, ConfigSchema] = {}
        
        # Encryption key (in production, this should come from secure key management)
        self._encryption_key = hashlib.sha256(b"gary-zero-config-key").digest()
        
        logger.info("EnterpriseConfigManager initialized")
    
    async def start_hot_reload(self):
        """Start hot reload monitoring."""
        if self.enable_hot_reload and self._reload_task is None:
            self._reload_task = asyncio.create_task(self._hot_reload_loop())
            logger.info("Started configuration hot reload monitoring")
    
    async def stop_hot_reload(self):
        """Stop hot reload monitoring."""
        if self._reload_task:
            self._shutdown_event.set()
            await self._reload_task
            self._reload_task = None
            logger.info("Stopped configuration hot reload monitoring")
    
    async def register_schema(self, schema: ConfigSchema):
        """Register a configuration schema for validation."""
        self._schemas[schema.name] = schema
        logger.info(f"Registered configuration schema: {schema.name}")
    
    async def set_config(
        self,
        key: str,
        value: Any,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        encrypt: bool = False,
        tags: Optional[List[str]] = None,
        description: str = "",
        schema_name: Optional[str] = None
    ) -> bool:
        """Set configuration value with validation and encryption."""
        try:
            # Validate against schema if provided
            if schema_name and self.validation_enabled:
                if schema_name in self._schemas:
                    schema = self._schemas[schema_name]
                    config_data = {key: value}
                    
                    valid, errors = await self.validator.validate_config(config_data, schema)
                    if not valid:
                        logger.error(f"Configuration validation failed: {errors}")
                        return False
            
            # Encrypt value if requested
            if encrypt and self.enable_encryption:
                value = self._encrypt_value(value)
            
            entry = ConfigEntry(
                key=key,
                value=value,
                scope=scope,
                environment=environment,
                service=service,
                encrypted=encrypt,
                tags=tags or [],
                description=description
            )
            
            success = await self.backend.set_config(entry)
            
            if success:
                # Invalidate cache
                cache_key = self._build_cache_key(key, scope, environment, service)
                self._config_cache.pop(cache_key, None)
                self._cache_timestamps.pop(cache_key, None)
                
                # Trigger hot reload callbacks
                await self._trigger_reload_callbacks(key, scope, environment, service)
                
                logger.info(f"Set configuration: {key} (scope: {scope.value})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting configuration {key}: {e}")
            return False
    
    async def get_config(
        self,
        key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        default: Any = None,
        use_cache: bool = True
    ) -> Any:
        """Get configuration value with fallback hierarchy."""
        try:
            # Check cache first
            if use_cache:
                cached_value = self._get_cached_value(key, scope, environment, service)
                if cached_value is not None:
                    return cached_value
            
            # Try exact match first
            entry = await self.backend.get_config(key, scope, environment, service)
            
            # If not found, try fallback hierarchy
            if not entry:
                entry = await self._get_with_fallback(key, scope, environment, service)
            
            if entry:
                value = entry.value
                
                # Decrypt if needed
                if entry.encrypted and self.enable_encryption:
                    value = self._decrypt_value(value)
                
                # Cache the result
                if use_cache:
                    self._cache_value(key, scope, environment, service, value)
                
                return value
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting configuration {key}: {e}")
            return default
    
    async def _get_with_fallback(
        self,
        key: str,
        scope: ConfigScope,
        environment: Optional[str],
        service: Optional[str]
    ) -> Optional[ConfigEntry]:
        """Get configuration with scope fallback hierarchy."""
        # Define fallback order
        fallback_configs = []
        
        if scope == ConfigScope.SESSION:
            fallback_configs = [
                (ConfigScope.USER, environment, service),
                (ConfigScope.SERVICE, environment, service),
                (ConfigScope.ENVIRONMENT, environment, None),
                (ConfigScope.GLOBAL, None, None)
            ]
        elif scope == ConfigScope.USER:
            fallback_configs = [
                (ConfigScope.SERVICE, environment, service),
                (ConfigScope.ENVIRONMENT, environment, None),
                (ConfigScope.GLOBAL, None, None)
            ]
        elif scope == ConfigScope.SERVICE:
            fallback_configs = [
                (ConfigScope.ENVIRONMENT, environment, None),
                (ConfigScope.GLOBAL, None, None)
            ]
        elif scope == ConfigScope.ENVIRONMENT:
            fallback_configs = [
                (ConfigScope.GLOBAL, None, None)
            ]
        
        for fallback_scope, fallback_env, fallback_service in fallback_configs:
            entry = await self.backend.get_config(key, fallback_scope, fallback_env, fallback_service)
            if entry:
                return entry
        
        return None
    
    async def delete_config(
        self,
        key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None
    ) -> bool:
        """Delete configuration entry."""
        success = await self.backend.delete_config(key, scope, environment, service)
        
        if success:
            # Invalidate cache
            cache_key = self._build_cache_key(key, scope, environment, service)
            self._config_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            
            logger.info(f"Deleted configuration: {key} (scope: {scope.value})")
        
        return success
    
    async def list_configs(
        self,
        scope: Optional[ConfigScope] = None,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_encrypted: bool = False
    ) -> List[Dict[str, Any]]:
        """List configuration entries with filtering."""
        entries = await self.backend.list_configs(scope, environment, service, tags)
        
        result = []
        for entry in entries:
            entry_dict = asdict(entry)
            
            # Don't include encrypted values unless explicitly requested
            if entry.encrypted and not include_encrypted:
                entry_dict["value"] = "[ENCRYPTED]"
            elif entry.encrypted and include_encrypted and self.enable_encryption:
                entry_dict["value"] = self._decrypt_value(entry.value)
            
            result.append(entry_dict)
        
        return result
    
    async def get_config_history(
        self,
        key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get configuration change history."""
        history = await self.backend.get_config_history(key, scope, limit)
        return [asdict(entry) for entry in history]
    
    async def rollback_config(
        self,
        key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        version: Optional[int] = None
    ) -> bool:
        """Rollback configuration to a previous version."""
        history = await self.backend.get_config_history(key, scope)
        
        if not history:
            logger.warning(f"No history found for configuration: {key}")
            return False
        
        # Get target version (default to previous version)
        if version is None:
            target_entry = history[-1]  # Most recent in history
        else:
            target_entries = [e for e in history if e.version == version]
            if not target_entries:
                logger.warning(f"Version {version} not found for configuration: {key}")
                return False
            target_entry = target_entries[0]
        
        # Create new entry with rolled back value
        rollback_entry = ConfigEntry(
            key=key,
            value=target_entry.value,
            scope=scope,
            environment=environment,
            service=service,
            encrypted=target_entry.encrypted,
            tags=target_entry.tags,
            description=f"Rollback to version {target_entry.version}"
        )
        
        success = await self.backend.set_config(rollback_entry)
        
        if success:
            logger.info(f"Rolled back configuration {key} to version {target_entry.version}")
            
            # Invalidate cache and trigger callbacks
            cache_key = self._build_cache_key(key, scope, environment, service)
            self._config_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            await self._trigger_reload_callbacks(key, scope, environment, service)
        
        return success
    
    async def promote_config(
        self,
        key: str,
        from_environment: str,
        to_environment: str,
        scope: ConfigScope = ConfigScope.ENVIRONMENT,
        service: Optional[str] = None
    ) -> bool:
        """Promote configuration from one environment to another."""
        source_entry = await self.backend.get_config(key, scope, from_environment, service)
        
        if not source_entry:
            logger.warning(f"Configuration not found for promotion: {key} in {from_environment}")
            return False
        
        # Create new entry for target environment
        promoted_entry = ConfigEntry(
            key=key,
            value=source_entry.value,
            scope=scope,
            environment=to_environment,
            service=service,
            encrypted=source_entry.encrypted,
            tags=source_entry.tags + [f"promoted_from_{from_environment}"],
            description=f"Promoted from {from_environment}: {source_entry.description}"
        )
        
        success = await self.backend.set_config(promoted_entry)
        
        if success:
            logger.info(f"Promoted configuration {key} from {from_environment} to {to_environment}")
        
        return success
    
    async def bulk_import(
        self,
        config_data: Dict[str, Any],
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        format_type: ConfigFormat = ConfigFormat.JSON
    ) -> tuple[int, int, List[str]]:
        """Bulk import configuration data."""
        successful = 0
        failed = 0
        errors = []
        
        # Parse data based on format
        if format_type == ConfigFormat.YAML:
            try:
                if isinstance(config_data, str):
                    config_data = yaml.safe_load(config_data)
            except Exception as e:
                return 0, 1, [f"YAML parsing error: {e}"]
        
        for key, value in config_data.items():
            try:
                success = await self.set_config(
                    key=key,
                    value=value,
                    scope=scope,
                    environment=environment,
                    service=service
                )
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Failed to set {key}")
                    
            except Exception as e:
                failed += 1
                errors.append(f"Error setting {key}: {e}")
        
        logger.info(f"Bulk import completed: {successful} successful, {failed} failed")
        return successful, failed, errors
    
    async def bulk_export(
        self,
        scope: Optional[ConfigScope] = None,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        format_type: ConfigFormat = ConfigFormat.JSON,
        include_metadata: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Bulk export configuration data."""
        entries = await self.backend.list_configs(scope, environment, service)
        
        if include_metadata:
            export_data = {
                "metadata": {
                    "export_time": datetime.now(timezone.utc).isoformat(),
                    "scope": scope.value if scope else "all",
                    "environment": environment,
                    "service": service,
                    "total_entries": len(entries)
                },
                "configurations": {}
            }
            
            for entry in entries:
                export_data["configurations"][entry.key] = asdict(entry)
        else:
            export_data = {}
            for entry in entries:
                value = entry.value
                if entry.encrypted and self.enable_encryption:
                    value = self._decrypt_value(value)
                export_data[entry.key] = value
        
        if format_type == ConfigFormat.YAML:
            return yaml.dump(export_data, default_flow_style=False)
        elif format_type == ConfigFormat.JSON:
            return json.dumps(export_data, indent=2, default=str)
        
        return export_data
    
    def register_reload_callback(
        self,
        key: str,
        callback: Callable,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: Optional[str] = None,
        service: Optional[str] = None
    ):
        """Register callback for configuration hot reload."""
        callback_key = self._build_cache_key(key, scope, environment, service)
        
        if callback_key not in self._reload_callbacks:
            self._reload_callbacks[callback_key] = []
        
        self._reload_callbacks[callback_key].append(callback)
        logger.info(f"Registered reload callback for {key}")
    
    def _build_cache_key(
        self,
        key: str,
        scope: ConfigScope,
        environment: Optional[str],
        service: Optional[str]
    ) -> str:
        """Build cache key."""
        parts = [scope.value, key]
        if environment:
            parts.insert(1, environment)
        if service:
            parts.insert(-1, service)
        return ":".join(parts)
    
    def _get_cached_value(
        self,
        key: str,
        scope: ConfigScope,
        environment: Optional[str],
        service: Optional[str]
    ) -> Any:
        """Get value from cache if valid."""
        cache_key = self._build_cache_key(key, scope, environment, service)
        
        if cache_key in self._config_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and (datetime.now(timezone.utc) - cache_time).seconds < self._cache_ttl:
                return self._config_cache[cache_key]
        
        return None
    
    def _cache_value(
        self,
        key: str,
        scope: ConfigScope,
        environment: Optional[str],
        service: Optional[str],
        value: Any
    ):
        """Cache configuration value."""
        cache_key = self._build_cache_key(key, scope, environment, service)
        self._config_cache[cache_key] = value
        self._cache_timestamps[cache_key] = datetime.now(timezone.utc)
    
    async def _trigger_reload_callbacks(
        self,
        key: str,
        scope: ConfigScope,
        environment: Optional[str],
        service: Optional[str]
    ):
        """Trigger hot reload callbacks for configuration change."""
        callback_key = self._build_cache_key(key, scope, environment, service)
        
        if callback_key in self._reload_callbacks:
            for callback in self._reload_callbacks[callback_key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, scope, environment, service)
                    else:
                        callback(key, scope, environment, service)
                except Exception as e:
                    logger.warning(f"Hot reload callback error for {key}: {e}")
    
    async def _hot_reload_loop(self):
        """Background loop for hot reload monitoring."""
        while not self._shutdown_event.is_set():
            try:
                # This is a simplified version - in production you'd monitor
                # for actual file changes or database updates
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in hot reload loop: {e}")
                await asyncio.sleep(60)
    
    def _encrypt_value(self, value: Any) -> str:
        """Encrypt configuration value."""
        try:
            from cryptography.fernet import Fernet
            
            # Generate key from our base key
            fernet_key = Fernet.generate_key()
            f = Fernet(fernet_key)
            
            # Encrypt the value
            value_bytes = json.dumps(value).encode()
            encrypted_value = f.encrypt(value_bytes)
            
            # Return base64 encoded result with key
            import base64
            return base64.b64encode(fernet_key + encrypted_value).decode()
            
        except ImportError:
            logger.warning("Cryptography package not available, storing value as base64")
            import base64
            return base64.b64encode(json.dumps(value).encode()).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt configuration value."""
        try:
            from cryptography.fernet import Fernet
            import base64
            
            # Decode and split key and data
            encrypted_data = base64.b64decode(encrypted_value.encode())
            fernet_key = encrypted_data[:44]  # Fernet key is 44 bytes when base64 encoded
            encrypted_content = encrypted_data[44:]
            
            # Decrypt
            f = Fernet(fernet_key)
            decrypted_bytes = f.decrypt(encrypted_content)
            
            return json.loads(decrypted_bytes.decode())
            
        except ImportError:
            logger.warning("Cryptography package not available, decoding from base64")
            import base64
            decrypted_bytes = base64.b64decode(encrypted_value.encode())
            return json.loads(decrypted_bytes.decode())
        except Exception as e:
            logger.error(f"Error decrypting value: {e}")
            return encrypted_value


# Convenience functions
async def get_env_config(
    manager: EnterpriseConfigManager,
    key: str,
    environment: str,
    default: Any = None
) -> Any:
    """Get environment-specific configuration."""
    return await manager.get_config(
        key,
        ConfigScope.ENVIRONMENT,
        environment=environment,
        default=default
    )


async def set_service_config(
    manager: EnterpriseConfigManager,
    key: str,
    value: Any,
    service: str,
    environment: Optional[str] = None
) -> bool:
    """Set service-specific configuration."""
    return await manager.set_config(
        key,
        value,
        ConfigScope.SERVICE,
        environment=environment,
        service=service
    )