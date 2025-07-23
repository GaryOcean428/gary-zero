"""Settings module initialization and public API.

This module provides the public interface for working with application settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Import types for type checking to avoid circular imports
if TYPE_CHECKING:
    from .api import get_settings, set_settings, set_settings_delta
    from .types import Settings

# Re-export the public API
from .api import (  # noqa: F401
    PASSWORD_PLACEHOLDER,
    convert_in,
    convert_out,
    get_settings,
    set_settings,
    set_settings_delta,
)
from .types import Settings  # noqa: F401

__all__ = [
    "Settings",
    "get_settings",
    "set_settings",
    "set_settings_delta",
    "convert_in",
    "convert_out",
    "PASSWORD_PLACEHOLDER",
]
