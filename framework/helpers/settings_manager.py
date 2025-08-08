"""Settings management for the application.

This module provides a thread-safe way to manage application settings
without using global variables.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import TYPE_CHECKING

from . import files

if TYPE_CHECKING:
    from .settings import get_default_settings, normalize_settings
    from .settings_types import Settings
else:
    # These will be imported locally at runtime to avoid circular imports
    get_default_settings = None  # type: ignore
    normalize_settings = None  # type: ignore
    Settings = dict  # type: ignore


class SettingsManager:
    """Manages application settings in a thread-safe manner.

    This class provides a singleton instance that manages the application settings,
    handling loading, saving, and applying settings changes.
    """

    _instance: SettingsManager | None = None
    _settings: Settings | None = None

    @property
    def _settings_file(self) -> str:
        """Get the settings file path, evaluating DATA_DIR at runtime."""
        return files.get_data_path("settings.json")

    def __new__(cls) -> SettingsManager:
        """Ensure only one instance of SettingsManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = None
        return cls._instance

    @classmethod
    def get_instance(cls) -> SettingsManager:
        """Get the singleton instance of SettingsManager."""
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance

    def get_settings(self) -> Settings:
        """Get the current settings.

        Returns:
            The current settings, loaded from file or default if not set,
            with environment variable overrides applied.
        """
        if self._settings is None:
            # Import from the settings.py file directly using importlib
            import importlib.util
            import os

            settings_file_path = os.path.join(os.path.dirname(__file__), "settings.py")
            spec = importlib.util.spec_from_file_location(
                "settings", settings_file_path
            )
            if spec and spec.loader:
                settings_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings_module)
                get_default_settings = settings_module.get_default_settings
                normalize_settings = settings_module.normalize_settings
            else:
                raise ImportError("Could not import settings module")

            default_settings = get_default_settings()
            loaded_settings = self._read_settings_file()
            self._settings = (
                normalize_settings(loaded_settings)
                if loaded_settings
                else default_settings
            )
            
        # Always apply environment variable overrides on access
        # This ensures environment variables always take priority
        try:
            from framework.helpers.settings.env_priority import apply_env_var_overrides
            result = apply_env_var_overrides(self._settings)
            return result  # type: ignore[return-value]
        except ImportError as e:
            print(f"Warning: Failed to import env_priority, using stored settings only: {e}")
            # Fallback to original behavior if import fails
            return self._settings  # type: ignore[return-value]

    def set_settings(self, settings: Settings, apply: bool = True) -> None:
        """Update the current settings and optionally apply them.

        Args:
            settings: The new settings to apply
            apply: If True, apply the settings immediately
        """
        # Import from the settings.py file directly
        import importlib.util
        import os

        settings_file_path = os.path.join(os.path.dirname(__file__), "settings.py")
        spec = importlib.util.spec_from_file_location("settings", settings_file_path)
        if spec and spec.loader:
            settings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings_module)
            normalize_settings = settings_module.normalize_settings
        else:
            raise ImportError("Could not import settings module")

        previous = self._settings
        self._settings = normalize_settings(settings)  # type: ignore[assignment]
        self._write_settings_file(self._settings)

        if apply and previous is not None:
            from .settings import _apply_settings  # type: ignore

            _apply_settings(previous)

    def _read_settings_file(self) -> Settings | None:
        """Read settings from the settings file.

        Returns:
            The loaded settings if successful, None otherwise.
        """
        # Check for migration from legacy location
        self._migrate_legacy_settings()

        if not os.path.exists(self._settings_file):
            return None

        try:
            with open(self._settings_file, encoding="utf-8") as f:
                settings = json.load(f)
                from .settings import normalize_settings  # type: ignore

                return normalize_settings(settings)  # type: ignore[return-value]
        except (json.JSONDecodeError, OSError):
            return None

    def _migrate_legacy_settings(self) -> None:
        """Migrate settings from legacy location if needed."""
        legacy_settings_file = files.get_abs_path("tmp/settings.json")

        # Only migrate if new file doesn't exist but legacy file does
        if not os.path.exists(self._settings_file) and os.path.exists(
            legacy_settings_file
        ):
            try:
                # Create the new directory structure
                os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)

                # Copy the legacy file to the new location
                shutil.copy2(legacy_settings_file, self._settings_file)

                # Log the migration
                print(
                    f"Settings migrated from {legacy_settings_file} to {self._settings_file}"
                )

            except OSError as e:
                # If migration fails, log the error but don't raise it
                print(f"Warning: Failed to migrate settings from legacy location: {e}")

    def _write_settings_file(self, settings: Settings) -> None:
        """Write settings to the settings file."""
        os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
        with open(self._settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, default=str)

    def reset_to_defaults(self) -> None:
        """Reset settings to their default values."""
        from .settings import get_default_settings  # type: ignore

        self._settings = get_default_settings()  # type: ignore[assignment]
        self._write_settings_file(self._settings)


# Global instance for backward compatibility
settings_manager = SettingsManager()
