"""Configuration management for the hierarchical planner.

This module provides configuration options for the hierarchical planning engine,
integrating with the existing settings system.
"""

from typing import Any

from framework.helpers.dotenv import get_dotenv_value
from framework.helpers.hierarchical_planner import PlanningConfig


class PlannerSettings:
    """Settings management for hierarchical planner configuration."""

    _config_cache: PlanningConfig | None = None

    @classmethod
    def get_config(cls) -> PlanningConfig:
        """Get the current planner configuration.

        Returns:
            PlanningConfig: Current configuration
        """
        if cls._config_cache is None:
            cls._config_cache = cls._load_config()
        return cls._config_cache

    @classmethod
    def update_config(cls, **kwargs) -> PlanningConfig:
        """Update planner configuration.

        Args:
            **kwargs: Configuration parameters to update

        Returns:
            PlanningConfig: Updated configuration
        """
        current_config = cls.get_config().dict()
        current_config.update(kwargs)
        cls._config_cache = PlanningConfig(**current_config)
        cls._save_config(cls._config_cache)
        return cls._config_cache

    @classmethod
    def reset_config(cls) -> PlanningConfig:
        """Reset to default configuration.

        Returns:
            PlanningConfig: Default configuration
        """
        cls._config_cache = PlanningConfig.get_default()
        cls._save_config(cls._config_cache)
        return cls._config_cache

    @classmethod
    def _load_config(cls) -> PlanningConfig:
        """Load configuration from environment and settings.

        Returns:
            PlanningConfig: Loaded configuration
        """
        # Load from environment variables with fallbacks
        config_dict = {
            "auto_planning_enabled": cls._get_bool_setting(
                "PLANNER_AUTO_PLANNING", True
            ),
            "max_recursion_depth": cls._get_int_setting(
                "PLANNER_MAX_RECURSION_DEPTH", 3
            ),
            "model_name": cls._get_str_setting("PLANNER_MODEL", "o3"),
            "max_subtasks": cls._get_int_setting("PLANNER_MAX_SUBTASKS", 10),
            "verification_enabled": cls._get_bool_setting("PLANNER_VERIFICATION", True),
            "retry_failed_subtasks": cls._get_bool_setting(
                "PLANNER_RETRY_FAILED", True
            ),
        }

        return PlanningConfig(**config_dict)

    @classmethod
    def _save_config(cls, config: PlanningConfig) -> None:
        """Save configuration to persistent storage.

        Args:
            config: Configuration to save
        """
        # Save to settings file or environment
        # For now, we'll keep it in memory as the framework uses its own settings system
        pass

    @classmethod
    def _get_bool_setting(cls, key: str, default: bool) -> bool:
        """Get boolean setting from environment.

        Args:
            key: Environment variable key
            default: Default value

        Returns:
            bool: Setting value
        """
        value = get_dotenv_value(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    @classmethod
    def _get_int_setting(cls, key: str, default: int) -> int:
        """Get integer setting from environment.

        Args:
            key: Environment variable key
            default: Default value

        Returns:
            int: Setting value
        """
        value = get_dotenv_value(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    @classmethod
    def _get_str_setting(cls, key: str, default: str) -> str:
        """Get string setting from environment.

        Args:
            key: Environment variable key
            default: Default value

        Returns:
            str: Setting value
        """
        value = get_dotenv_value(key)
        return value if value is not None else default

    @classmethod
    def get_settings_dict(cls) -> dict[str, Any]:
        """Get configuration as dictionary for API/UI display.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config = cls.get_config()
        return {
            "auto_planning_enabled": config.auto_planning_enabled,
            "max_recursion_depth": config.max_recursion_depth,
            "model_name": config.model_name,
            "max_subtasks": config.max_subtasks,
            "verification_enabled": config.verification_enabled,
            "retry_failed_subtasks": config.retry_failed_subtasks,
        }

    @classmethod
    def validate_config(cls, config_dict: dict[str, Any]) -> dict[str, str]:
        """Validate configuration parameters.

        Args:
            config_dict: Configuration to validate

        Returns:
            Dict[str, str]: Validation errors (empty if valid)
        """
        errors = {}

        if "max_recursion_depth" in config_dict:
            if (
                not isinstance(config_dict["max_recursion_depth"], int)
                or config_dict["max_recursion_depth"] < 1
            ):
                errors["max_recursion_depth"] = "Must be a positive integer"

        if "max_subtasks" in config_dict:
            if (
                not isinstance(config_dict["max_subtasks"], int)
                or config_dict["max_subtasks"] < 1
            ):
                errors["max_subtasks"] = "Must be a positive integer"

        if "model_name" in config_dict:
            if (
                not isinstance(config_dict["model_name"], str)
                or not config_dict["model_name"].strip()
            ):
                errors["model_name"] = "Must be a non-empty string"

        return errors
