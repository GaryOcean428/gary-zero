"""Settings management for the application.

This module provides a thread-safe way to manage application settings
without using global variables.
"""
from __future__ import annotations

import json
import os
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
    _settings_file: str = files.get_abs_path("tmp/settings.json")

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
            The current settings, loaded from file or default if not set.
        """
        if self._settings is None:
            from .settings import get_default_settings, normalize_settings  # type: ignore
            default_settings = get_default_settings()
            loaded_settings = self._read_settings_file()
            self._settings = (
                normalize_settings(loaded_settings)
                if loaded_settings else default_settings
            )
        return self._settings  # type: ignore[return-value]

    def set_settings(self, settings: Settings, apply: bool = True) -> None:
        """Update the current settings and optionally apply them.

        Args:
            settings: The new settings to apply
            apply: If True, apply the settings immediately
        """
        from .settings import normalize_settings  # type: ignore
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
        if not os.path.exists(self._settings_file):
            return None

        try:
            with open(self._settings_file, encoding='utf-8') as f:
                settings = json.load(f)
                from .settings import normalize_settings  # type: ignore
                return normalize_settings(settings)  # type: ignore[return-value]
        except (json.JSONDecodeError, OSError):
            return None

    def _write_settings_file(self, settings: Settings) -> None:
        """Write settings to the settings file."""
        os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
        with open(self._settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, default=str)

    def reset_to_defaults(self) -> None:
        """Reset settings to their default values."""
        from .settings import get_default_settings  # type: ignore
        self._settings = get_default_settings()  # type: ignore[assignment]
        self._write_settings_file(self._settings)


# Global instance for backward compatibility
settings_manager = SettingsManager()
