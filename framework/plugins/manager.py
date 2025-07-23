"""Plugin manager that coordinates all plugin system components."""

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass
from .loader import PluginLoader
from .registry import PluginMetadata, PluginRegistry
from .security import PluginSecurityManager


class PluginManager:
    """Central manager for the plugin system."""

    def __init__(self, plugins_dir: str = "plugins", db_file: str = "plugins.db"):
        self.registry = PluginRegistry(plugins_dir, db_file)
        self.loader = PluginLoader(self.registry)
        self.security = PluginSecurityManager()

        # Auto-discover and sync plugins on initialization
        self.refresh_plugins()

    def get_tool(self, name: str) -> type[Any] | None:
        """Get a tool class by name from plugins."""
        # Check if plugin is loaded
        if self.loader.is_plugin_loaded(name):
            return self.loader._loaded_tools.get(name)

        # Try to load the plugin
        return self.loader.load_plugin(name)

    def install_plugin(self, plugin_path: str, auto_enable: bool = True) -> bool:
        """Install a plugin from a directory path."""
        try:
            # Discover plugin metadata
            import json
            import os

            metadata_file = os.path.join(plugin_path, "plugin.json")
            if not os.path.exists(metadata_file):
                print(f"Plugin metadata file not found: {metadata_file}")
                return False

            with open(metadata_file) as f:
                data = json.load(f)
                metadata = PluginMetadata(**data)

            # Security validation
            if not self.security.validate_plugin(metadata, plugin_path):
                print(f"Plugin failed security validation: {metadata.name}")
                return False

            # Copy plugin to plugins directory
            import shutil
            dest_path = os.path.join(self.registry.plugins_dir, metadata.name)

            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)

            shutil.copytree(plugin_path, dest_path)

            # Register plugin
            metadata.enabled = auto_enable
            if self.registry.register_plugin(metadata):
                print(f"Plugin {metadata.name} installed successfully")
                return True
            else:
                print(f"Failed to register plugin {metadata.name}")
                return False

        except Exception as e:
            print(f"Failed to install plugin: {e}")
            return False

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin."""
        try:
            # Unload if loaded
            self.loader.unload_plugin(name)

            # Remove from registry
            self.registry.unregister_plugin(name)

            # Remove from filesystem
            import shutil
            plugin_path = self.registry.get_plugin_path(name)
            if plugin_path and os.path.exists(plugin_path):
                shutil.rmtree(plugin_path)

            print(f"Plugin {name} uninstalled successfully")
            return True

        except Exception as e:
            print(f"Failed to uninstall plugin {name}: {e}")
            return False

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if self.registry.enable_plugin(name):
            print(f"Plugin {name} enabled")
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        # Unload if loaded
        self.loader.unload_plugin(name)

        if self.registry.disable_plugin(name):
            print(f"Plugin {name} disabled")
            return True
        return False

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin."""
        tool_class = self.loader.reload_plugin(name)
        if tool_class:
            print(f"Plugin {name} reloaded successfully")
            return True
        return False

    def list_plugins(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        """List all plugins with their status."""
        plugins = self.registry.list_plugins(enabled_only)
        result = []

        for plugin in plugins:
            loaded = self.loader.is_plugin_loaded(plugin.name)
            result.append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "enabled": plugin.enabled,
                "loaded": loaded,
                "capabilities": plugin.capabilities,
                "install_date": plugin.install_date
            })

        return result

    def get_plugin_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about a plugin."""
        metadata = self.registry.get_plugin(name)
        if not metadata:
            return None

        loaded = self.loader.is_plugin_loaded(name)

        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "capabilities": metadata.capabilities,
            "dependencies": metadata.dependencies,
            "entry_point": metadata.entry_point,
            "enabled": metadata.enabled,
            "loaded": loaded,
            "install_date": metadata.install_date,
            "last_updated": metadata.last_updated,
            "path": self.registry.get_plugin_path(name)
        }

    def refresh_plugins(self):
        """Refresh plugin discovery and sync with registry."""
        self.registry.sync_discovered_plugins()

    def validate_plugin_dependencies(self, name: str) -> bool:
        """Validate that a plugin's dependencies are available."""
        metadata = self.registry.get_plugin(name)
        if not metadata:
            return False

        return self.loader.validate_plugin_dependencies(metadata)

    def get_available_capabilities(self) -> list[str]:
        """Get all capabilities provided by enabled plugins."""
        capabilities = set()
        plugins = self.registry.list_plugins(enabled_only=True)

        for plugin in plugins:
            capabilities.update(plugin.capabilities)

        return sorted(list(capabilities))
