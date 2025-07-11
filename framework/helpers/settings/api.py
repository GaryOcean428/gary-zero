"""Public API for the settings module.

This module provides the public interface for accessing and modifying settings
while avoiding circular imports.
"""

from __future__ import annotations

import json
import os
from typing import Any, cast

from framework.helpers import files
from framework.helpers.settings.types import (
    DEFAULT_SETTINGS,
    Settings,
    SettingsField,
    SettingsOutput,
    SettingsSection,
)

# Constants
SETTINGS_FILE = files.get_abs_path("tmp/settings.json")
MODEL_PARAMS_DESCRIPTION = (
    """Any other parameters supported by the model. Format is KEY=VALUE """
    """on individual lines, just like .env file."""
)
PASSWORD_PLACEHOLDER = "****PSWD****"


def get_settings() -> Settings:
    """Get the current settings.

    Returns:
        The current settings, loaded from file or default if not set.
    """
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            settings_data = json.load(f)
        return cast(Settings, settings_data)
    except (json.JSONDecodeError, OSError):
        # If there's an error reading the file, return defaults
        return DEFAULT_SETTINGS.copy()


def set_settings(settings: Settings, apply: bool = True) -> None:
    """Apply settings to the running application.

    Args:
        settings: The new settings to apply
        apply: If True, apply the settings immediately
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    # Write settings to file
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    if apply:
        _apply_settings(settings)


def set_settings_delta(delta: dict[str, Any], apply: bool = True) -> None:
    """Update settings with the given delta.

    Args:
        delta: Dictionary of settings to update
        apply: If True, apply the settings immediately
    """
    current = get_settings()
    updated = {**current, **delta}
    set_settings(cast(Settings, updated), apply=apply)


def convert_out(settings: Settings) -> SettingsOutput:
    """Convert settings to UI format.

    Args:
        settings: The settings to convert

    Returns:
        Settings formatted for the UI
    """
    # Import models here to avoid circular imports
    try:
        import models

        ModelProvider = models.ModelProvider
    except ImportError:
        # Fallback if models not available
        class ModelProvider:
            @classmethod
            def __iter__(cls):
                return iter([])

    # Main model section
    chat_model_fields: list[SettingsField] = []
    chat_model_fields.append(
        {
            "id": "chat_model_provider",
            "title": "Chat model provider",
            "description": "Select provider for main chat model used by Gary-Zero",
            "type": "select",
            "value": settings["chat_model_provider"],
            "options": [{"value": p.name, "label": p.value} for p in ModelProvider],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_name",
            "title": "Chat model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["chat_model_name"],
        }
    )

    chat_model_section: SettingsSection = {
        "id": "chat_model",
        "title": "Chat Model",
        "description": "Selection and settings for main chat model used by Gary-Zero",
        "fields": chat_model_fields,
        "tab": "agent",
    }

    # Add the section to the result
    result: SettingsOutput = {
        "sections": [
            chat_model_section,
        ]
    }
    return result


def _apply_settings(settings: Settings) -> None:
    """Apply settings to the running application.

    Args:
        settings: The settings to apply
    """
    # For now, this is a placeholder
    # In the future, this would update the running application
    pass
