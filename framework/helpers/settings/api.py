"""Public API for the settings module.

This module provides the public interface for accessing and modifying settings
while avoiding circular imports.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, cast

from framework.helpers import files
from framework.helpers.settings.types import (
    DEFAULT_SETTINGS,
    Settings,
    SettingsField,
    SettingsOutput,
    SettingsSection,
)
from framework.helpers.model_catalog import get_models_for_provider, get_all_models

# Constants
SETTINGS_FILE = files.get_abs_path("tmp/settings.json")
MODEL_PARAMS_DESCRIPTION = (
    """Any other parameters supported by the model. Format is KEY=VALUE """
    """on individual lines, just like .env file."""
)
PASSWORD_PLACEHOLDER = "****PSWD****"


def _dict_to_env(data_dict):
    """Convert a dictionary to environment variable format.
    
    Args:
        data_dict: Dictionary to convert
        
    Returns:
        String in KEY=VALUE format
    """
    lines = []
    for key, value in data_dict.items():
        if "\n" in str(value):
            value = f"'{value}'"
        elif " " in str(value) or value == "" or any(c in str(value) for c in "\"'"):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _env_to_dict(data: str) -> dict[str, str]:
    """Convert environment variable format to dictionary.
    
    Args:
        data: String in KEY=VALUE format
        
    Returns:
        Dictionary with the parsed key-value pairs
    """
    env_dict = {}
    line_pattern = re.compile(r"\s*([^#][^=]*)\s*=\s*(.*)")
    for line in data.splitlines():
        match = line_pattern.match(line)
        if match:
            key, value = match.groups()
            # Remove optional surrounding quotes (single or double)
            value = value.strip().strip('"').strip("'")
            env_dict[key.strip()] = value
    return env_dict


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
    from framework.helpers.settings.section_builders import SectionBuilder
    
    # Build all sections using the section builders
    sections = [
        SectionBuilder.build_agent_config_section(settings),
        SectionBuilder.build_chat_model_section(settings),
        SectionBuilder.build_util_model_section(settings),
        SectionBuilder.build_embed_model_section(settings),
        SectionBuilder.build_browser_model_section(settings),
        SectionBuilder.build_stt_section(settings),
        SectionBuilder.build_api_keys_section(settings),
        SectionBuilder.build_auth_section(settings),
        SectionBuilder.build_mcp_client_section(settings),
        SectionBuilder.build_mcp_server_section(settings),
        SectionBuilder.build_computer_use_section(settings),
        SectionBuilder.build_claude_code_section(settings),
        SectionBuilder.build_dev_section(settings),
    ]

    # Return all sections
    result: SettingsOutput = {
        "sections": sections
    }
    return result


def convert_in(settings_data: dict[str, Any]) -> Settings:
    """Convert UI format settings to internal Settings format.

    Args:
        settings_data: Settings data from the UI (containing 'sections' with 'fields')

    Returns:
        Settings object ready for use by the application
    """
    current = get_settings()
    
    # Ensure api_keys exists
    if "api_keys" not in current:
        current["api_keys"] = {}
    
    # Process sections if they exist in the input data
    if "sections" in settings_data:
        for section in settings_data["sections"]:
            if "fields" in section:
                for field in section["fields"]:
                    field_id = field.get("id")
                    field_value = field.get("value")
                    
                    # Skip password placeholders - keep existing values
                    if field_value != PASSWORD_PLACEHOLDER and field_id:
                        if field_id.endswith("_kwargs"):
                            # Convert environment-style string to dictionary
                            current[field_id] = _env_to_dict(field_value)
                        elif field_id.startswith("api_key_"):
                            # Handle API keys specially - store in api_keys dict
                            provider = field_id.replace("api_key_", "")
                            current["api_keys"][provider] = field_value
                        else:
                            # Regular field - store directly
                            current[field_id] = field_value
    
    return cast(Settings, current)


def _apply_settings(settings: Settings) -> None:
    """Apply settings to the running application.

    Args:
        settings: The settings to apply
    """
    # For now, this is a placeholder
    # In the future, this would update the running application
    pass
