"""Plugin management CLI for Gary-Zero."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.plugins.manager import PluginManager


def list_plugins(args):
    """List all plugins."""
    manager = PluginManager()
    plugins = manager.list_plugins(enabled_only=args.enabled_only)
    
    if not plugins:
        print("No plugins found.")
        return
    
    print(f"{'Name':<20} {'Version':<10} {'Status':<10} {'Loaded':<8} {'Author':<15}")
    print("-" * 75)
    
    for plugin in plugins:
        status = "Enabled" if plugin['enabled'] else "Disabled"
        loaded = "Yes" if plugin['loaded'] else "No"
        print(f"{plugin['name']:<20} {plugin['version']:<10} {status:<10} {loaded:<8} {plugin['author']:<15}")


def show_plugin(args):
    """Show detailed information about a plugin."""
    manager = PluginManager()
    info = manager.get_plugin_info(args.name)
    
    if not info:
        print(f"Plugin '{args.name}' not found.")
        return
    
    print(f"Plugin: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Description: {info['description']}")
    print(f"Author: {info['author']}")
    print(f"Status: {'Enabled' if info['enabled'] else 'Disabled'}")
    print(f"Loaded: {'Yes' if info['loaded'] else 'No'}")
    print(f"Capabilities: {', '.join(info['capabilities'])}")
    print(f"Dependencies: {', '.join(info['dependencies'])}")
    print(f"Entry Point: {info['entry_point']}")
    print(f"Install Date: {info['install_date']}")
    print(f"Last Updated: {info['last_updated']}")
    print(f"Path: {info['path']}")


def enable_plugin(args):
    """Enable a plugin."""
    manager = PluginManager()
    
    if manager.enable_plugin(args.name):
        print(f"Plugin '{args.name}' enabled successfully.")
    else:
        print(f"Failed to enable plugin '{args.name}'.")


def disable_plugin(args):
    """Disable a plugin."""
    manager = PluginManager()
    
    if manager.disable_plugin(args.name):
        print(f"Plugin '{args.name}' disabled successfully.")
    else:
        print(f"Failed to disable plugin '{args.name}'.")


def reload_plugin(args):
    """Reload a plugin."""
    manager = PluginManager()
    
    if manager.reload_plugin(args.name):
        print(f"Plugin '{args.name}' reloaded successfully.")
    else:
        print(f"Failed to reload plugin '{args.name}'.")


def install_plugin(args):
    """Install a plugin from a directory."""
    manager = PluginManager()
    
    if manager.install_plugin(args.path, auto_enable=not args.disable):
        print(f"Plugin installed successfully from '{args.path}'.")
    else:
        print(f"Failed to install plugin from '{args.path}'.")


def uninstall_plugin(args):
    """Uninstall a plugin."""
    manager = PluginManager()
    
    if not args.force:
        confirm = input(f"Are you sure you want to uninstall plugin '{args.name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Uninstall cancelled.")
            return
    
    if manager.uninstall_plugin(args.name):
        print(f"Plugin '{args.name}' uninstalled successfully.")
    else:
        print(f"Failed to uninstall plugin '{args.name}'.")


def refresh_plugins(args):
    """Refresh plugin discovery."""
    manager = PluginManager()
    manager.refresh_plugins()
    print("Plugin discovery refreshed.")


def validate_plugin(args):
    """Validate a plugin's dependencies."""
    manager = PluginManager()
    
    if manager.validate_plugin_dependencies(args.name):
        print(f"Plugin '{args.name}' dependencies are valid.")
    else:
        print(f"Plugin '{args.name}' has missing dependencies.")


def list_capabilities(args):
    """List all available capabilities."""
    manager = PluginManager()
    capabilities = manager.get_available_capabilities()
    
    if not capabilities:
        print("No capabilities found.")
        return
    
    print("Available capabilities:")
    for capability in capabilities:
        print(f"  • {capability}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Gary-Zero Plugin Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List plugins
    list_parser = subparsers.add_parser('list', help='List plugins')
    list_parser.add_argument('--enabled-only', action='store_true', help='Show only enabled plugins')
    list_parser.set_defaults(func=list_plugins)
    
    # Show plugin info
    show_parser = subparsers.add_parser('show', help='Show plugin information')
    show_parser.add_argument('name', help='Plugin name')
    show_parser.set_defaults(func=show_plugin)
    
    # Enable plugin
    enable_parser = subparsers.add_parser('enable', help='Enable a plugin')
    enable_parser.add_argument('name', help='Plugin name')
    enable_parser.set_defaults(func=enable_plugin)
    
    # Disable plugin
    disable_parser = subparsers.add_parser('disable', help='Disable a plugin')
    disable_parser.add_argument('name', help='Plugin name')
    disable_parser.set_defaults(func=disable_plugin)
    
    # Reload plugin
    reload_parser = subparsers.add_parser('reload', help='Reload a plugin')
    reload_parser.add_argument('name', help='Plugin name')
    reload_parser.set_defaults(func=reload_plugin)
    
    # Install plugin
    install_parser = subparsers.add_parser('install', help='Install a plugin')
    install_parser.add_argument('path', help='Path to plugin directory')
    install_parser.add_argument('--disable', action='store_true', help='Install but do not enable')
    install_parser.set_defaults(func=install_plugin)
    
    # Uninstall plugin
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall a plugin')
    uninstall_parser.add_argument('name', help='Plugin name')
    uninstall_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    uninstall_parser.set_defaults(func=uninstall_plugin)
    
    # Refresh plugins
    refresh_parser = subparsers.add_parser('refresh', help='Refresh plugin discovery')
    refresh_parser.set_defaults(func=refresh_plugins)
    
    # Validate plugin
    validate_parser = subparsers.add_parser('validate', help='Validate plugin dependencies')
    validate_parser.add_argument('name', help='Plugin name')
    validate_parser.set_defaults(func=validate_plugin)
    
    # List capabilities
    capabilities_parser = subparsers.add_parser('capabilities', help='List available capabilities')
    capabilities_parser.set_defaults(func=list_capabilities)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()