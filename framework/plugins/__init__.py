"""Plugin system for Gary-Zero."""

from .loader import PluginLoader
from .registry import PluginMetadata, PluginRegistry
from .security import PluginSecurityManager

__all__ = ["PluginRegistry", "PluginMetadata", "PluginSecurityManager", "PluginLoader"]
