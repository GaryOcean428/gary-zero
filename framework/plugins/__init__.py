"""Plugin system for Gary-Zero."""

from .registry import PluginRegistry, PluginMetadata
from .security import PluginSecurityManager
from .loader import PluginLoader

__all__ = ["PluginRegistry", "PluginMetadata", "PluginSecurityManager", "PluginLoader"]