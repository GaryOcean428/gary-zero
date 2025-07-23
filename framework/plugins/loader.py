"""Plugin loader for dynamic tool loading."""

import importlib
import importlib.util
import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass
from .registry import PluginMetadata, PluginRegistry


class PluginLoader:
    """Handles dynamic loading and unloading of plugins."""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._loaded_modules: dict[str, Any] = {}
        self._loaded_tools: dict[str, type[Any]] = {}

    def load_plugin(self, name: str) -> type[Any] | None:
        """Load a plugin and return its tool class."""
        # Check if already loaded
        if name in self._loaded_tools:
            return self._loaded_tools[name]

        # Get plugin metadata
        metadata = self.registry.get_plugin(name)
        if not metadata or not metadata.enabled:
            return None

        # Get plugin path
        plugin_path = self.registry.get_plugin_path(name)
        if not plugin_path:
            return None

        # Load the plugin module
        try:
            tool_class = self._load_plugin_module(name, plugin_path, metadata)
            if tool_class:
                self._loaded_tools[name] = tool_class
            return tool_class
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")
            return None

    def _load_plugin_module(self, name: str, plugin_path: str, metadata: PluginMetadata) -> type[Any] | None:
        """Load a plugin module and extract the tool class."""
        entry_file = os.path.join(plugin_path, metadata.entry_point)

        if not os.path.exists(entry_file):
            print(f"Plugin entry point not found: {entry_file}")
            return None

        # Create module spec
        spec = importlib.util.spec_from_file_location(f"plugin_{name}", entry_file)
        if not spec or not spec.loader:
            print(f"Failed to create module spec for plugin {name}")
            return None

        # Load the module
        module = importlib.util.module_from_spec(spec)
        self._loaded_modules[name] = module

        # Add to sys.modules to allow imports
        sys.modules[f"plugin_{name}"] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Failed to execute plugin module {name}: {e}")
            return None

        # Find the tool class
        tool_class = self._find_tool_class(module, name)
        return tool_class

    def _find_tool_class(self, module: Any, plugin_name: str) -> type[Any] | None:
        """Find the tool class in the loaded module."""
        # Look for classes that could be tool classes
        candidates = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if (isinstance(attr, type) and
                hasattr(attr, 'execute') and
                callable(attr.execute) and
                attr_name not in ['Tool', 'PluginTool', 'BaseClass']):
                candidates.append((attr_name, attr))

        print(f"Plugin {plugin_name} candidates: {[name for name, _ in candidates]}")

        if not candidates:
            print(f"No tool class found in plugin {plugin_name}")
            return None

        # Prefer classes that inherit from Tool if available
        try:
            from framework.helpers.tool import Tool
            for name, candidate in candidates:
                if issubclass(candidate, Tool):
                    print(f"Selected Tool subclass: {name}")
                    return candidate
        except ImportError:
            pass

        # Fallback to any class with execute method
        selected = candidates[0][1]
        print(f"Selected fallback class: {candidates[0][0]}")
        return selected

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        try:
            # Remove from loaded tools
            if name in self._loaded_tools:
                del self._loaded_tools[name]

            # Remove from loaded modules
            if name in self._loaded_modules:
                del self._loaded_modules[name]

            # Remove from sys.modules
            module_name = f"plugin_{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            return True
        except Exception as e:
            print(f"Failed to unload plugin {name}: {e}")
            return False

    def reload_plugin(self, name: str) -> type[Any] | None:
        """Reload a plugin."""
        self.unload_plugin(name)
        return self.load_plugin(name)

    def get_loaded_plugins(self) -> list[str]:
        """Get list of currently loaded plugin names."""
        return list(self._loaded_tools.keys())

    def is_plugin_loaded(self, name: str) -> bool:
        """Check if a plugin is currently loaded."""
        return name in self._loaded_tools

    def validate_plugin_dependencies(self, metadata: PluginMetadata) -> bool:
        """Validate that plugin dependencies are available."""
        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                print(f"Plugin {metadata.name} dependency not available: {dep}")
                return False
        return True
