"""
Configuration system for async task orchestration.

Provides settings management, backward compatibility controls,
and orchestration behavior configuration.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Configuration for async task orchestration system."""

    # Core orchestration settings
    enabled: bool = True
    max_concurrent_tasks: int = 10
    default_task_timeout_seconds: float = 300.0
    enable_performance_monitoring: bool = True

    # Dependency management
    max_dependency_depth: int = 10
    enable_cycle_detection: bool = True
    dependency_timeout_seconds: float = 600.0

    # Agent resource limits
    default_agent_max_concurrent_tasks: int = 3
    default_agent_max_requests_per_minute: int = 60
    default_agent_max_memory_mb: float = 1024.0

    # Retry and error handling
    default_max_retries: int = 2
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True

    # Performance adaptation
    adaptive_scheduling_enabled: bool = True
    cpu_high_threshold: float = 80.0
    memory_high_threshold: float = 80.0
    cpu_low_threshold: float = 50.0
    memory_low_threshold: float = 50.0

    # Backward compatibility
    fallback_to_sync_on_error: bool = True
    sync_mode_override: bool = False
    legacy_task_support: bool = True

    # Monitoring and logging
    enable_detailed_logging: bool = False
    metrics_collection_interval: float = 5.0
    performance_history_retention_minutes: int = 60

    # Custom agent configurations
    agent_specific_configs: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Advanced settings
    enable_task_preemption: bool = False
    priority_scheduling: bool = True
    resource_aware_scheduling: bool = True


class OrchestrationConfigManager:
    """Manages orchestration configuration with environment variable support."""

    def __init__(self):
        self._config = OrchestrationConfig()
        self._config_file_path: str | None = None
        self._load_from_environment()

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Core settings
        self._config.enabled = self._get_env_bool(
            "ORCHESTRATION_ENABLED", self._config.enabled
        )
        self._config.max_concurrent_tasks = self._get_env_int(
            "ORCHESTRATION_MAX_CONCURRENT", self._config.max_concurrent_tasks
        )
        self._config.default_task_timeout_seconds = self._get_env_float(
            "ORCHESTRATION_DEFAULT_TIMEOUT", self._config.default_task_timeout_seconds
        )

        # Performance settings
        self._config.enable_performance_monitoring = self._get_env_bool(
            "ORCHESTRATION_PERFORMANCE_MONITORING",
            self._config.enable_performance_monitoring,
        )
        self._config.adaptive_scheduling_enabled = self._get_env_bool(
            "ORCHESTRATION_ADAPTIVE_SCHEDULING",
            self._config.adaptive_scheduling_enabled,
        )

        # Resource limits
        self._config.default_agent_max_concurrent_tasks = self._get_env_int(
            "AGENT_MAX_CONCURRENT_TASKS",
            self._config.default_agent_max_concurrent_tasks,
        )
        self._config.default_agent_max_requests_per_minute = self._get_env_int(
            "AGENT_MAX_REQUESTS_PER_MINUTE",
            self._config.default_agent_max_requests_per_minute,
        )

        # Compatibility
        self._config.sync_mode_override = self._get_env_bool(
            "ORCHESTRATION_SYNC_MODE", self._config.sync_mode_override
        )
        self._config.fallback_to_sync_on_error = self._get_env_bool(
            "ORCHESTRATION_FALLBACK_SYNC", self._config.fallback_to_sync_on_error
        )

        # Logging
        self._config.enable_detailed_logging = self._get_env_bool(
            "ORCHESTRATION_DETAILED_LOGGING", self._config.enable_detailed_logging
        )

        logger.info("Orchestration configuration loaded from environment")

    def load_from_file(self, file_path: str):
        """Load configuration from JSON file."""
        try:
            with open(file_path) as f:
                config_data = json.load(f)

            # Update configuration with file data
            for key, value in config_data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")

            self._config_file_path = file_path
            logger.info(f"Configuration loaded from {file_path}")

        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")

    def save_to_file(self, file_path: str | None = None):
        """Save current configuration to JSON file."""
        target_path = file_path or self._config_file_path

        if not target_path:
            raise ValueError("No file path specified for saving configuration")

        try:
            # Convert config to dict
            config_dict = {}
            for key, value in self._config.__dict__.items():
                if isinstance(value, (str, int, float, bool, list, dict)):
                    config_dict[key] = value
                else:
                    # Convert complex types to string representation
                    config_dict[key] = str(value)

            with open(target_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            self._config_file_path = target_path
            logger.info(f"Configuration saved to {target_path}")

        except Exception as e:
            logger.error(f"Error saving configuration to {target_path}: {e}")
            raise

    def get_config(self) -> OrchestrationConfig:
        """Get the current configuration."""
        return self._config

    def update_config(self, **kwargs):
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                logger.debug(f"Updated configuration: {key} = {value}")
            else:
                logger.warning(f"Unknown configuration parameter: {key}")

    def get_agent_config(self, agent_id: str) -> dict[str, Any]:
        """Get agent-specific configuration."""
        agent_config = {
            "max_concurrent_tasks": self._config.default_agent_max_concurrent_tasks,
            "max_requests_per_minute": self._config.default_agent_max_requests_per_minute,
            "max_memory_mb": self._config.default_agent_max_memory_mb,
        }

        # Override with agent-specific settings if available
        if agent_id in self._config.agent_specific_configs:
            agent_config.update(self._config.agent_specific_configs[agent_id])

        return agent_config

    def set_agent_config(self, agent_id: str, config: dict[str, Any]):
        """Set agent-specific configuration."""
        self._config.agent_specific_configs[agent_id] = config
        logger.info(f"Updated configuration for agent {agent_id}")

    def is_orchestration_enabled(self) -> bool:
        """Check if orchestration is enabled."""
        return self._config.enabled and not self._config.sync_mode_override

    def should_use_sync_fallback(self) -> bool:
        """Check if sync fallback should be used."""
        return self._config.fallback_to_sync_on_error or self._config.sync_mode_override

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self._config = OrchestrationConfig()
        self._load_from_environment()
        logger.info("Configuration reset to defaults")

    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(
                f"Invalid integer value for {key}: {value}, using default {default}"
            )
            return default

    def _get_env_float(self, key: str, default: float) -> float:
        """Get float value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(
                f"Invalid float value for {key}: {value}, using default {default}"
            )
            return default


# Global configuration manager
_config_manager: OrchestrationConfigManager | None = None


def get_config_manager() -> OrchestrationConfigManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = OrchestrationConfigManager()
    return _config_manager


def get_orchestration_config() -> OrchestrationConfig:
    """Get the current orchestration configuration."""
    return get_config_manager().get_config()


def update_orchestration_config(**kwargs):
    """Update orchestration configuration."""
    get_config_manager().update_config(**kwargs)


def is_orchestration_enabled() -> bool:
    """Check if async orchestration is enabled."""
    return get_config_manager().is_orchestration_enabled()


def should_use_sync_fallback() -> bool:
    """Check if sync fallback should be used."""
    return get_config_manager().should_use_sync_fallback()
