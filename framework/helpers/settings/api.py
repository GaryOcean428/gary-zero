"""Public API for the settings module.

This module provides the public interface for accessing and modifying settings
while avoiding circular imports.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from framework.helpers import files
from framework.helpers.settings.types import Settings, DEFAULT_SETTINGS

# Constants
SETTINGS_FILE = files.get_abs_path("tmp/settings.json")


def get_settings() -> Settings:
    """Get the current settings.

    Returns:
        The current settings, loaded from file or default if not set.
    """
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
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
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)
    
    if apply:
        # Import here to avoid circular imports
        from framework.helpers.settings import _apply_settings
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
