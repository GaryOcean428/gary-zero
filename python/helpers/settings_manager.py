"""Settings management for the application.

This module provides a thread-safe way to manage application settings
without using global variables.
"""
from __future__ import annotations

import json
import os
from typing import TypeVar, cast

from . import files
from .settings import Settings, get_default_settings, normalize_settings

T = TypeVar('T')


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
        """Get the current settings, loading them if necessary."""
        if self._settings is None:
            self._settings = self._read_settings_file() or get_default_settings()
            self._settings = normalize_settings(self._settings)
        return self._settings

    def set_settings(self, settings: Settings, apply: bool = True) -> None:
        """Update the current settings and optionally apply them.

        Args:
            settings: The new settings to apply
            apply: If True, apply the settings immediately
        """
        previous = self._settings
        self._settings = normalize_settings(settings)
        self._write_settings_file(self._settings)

        if apply and previous is not None:
            from .settings import _apply_settings
            _apply_settings(previous)

    def _read_settings_file(self) -> Settings | None:
        """Read settings from the settings file."""
        if not os.path.exists(self._settings_file):
            return None

        try:
            with open(self._settings_file, encoding='utf-8') as f:
                data = json.load(f)
                return cast(Settings, data)
        except (json.JSONDecodeError, OSError):
            return None

    def _write_settings_file(self, settings: Settings) -> None:
        """Write settings to the settings file."""
        os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
        with open(self._settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, default=str)

    def reset_to_defaults(self) -> None:
        """Reset settings to their default values."""
        self._settings = get_default_settings()
        self._write_settings_file(self._settings)


# Global instance for backward compatibility
settings_manager = SettingsManager()
