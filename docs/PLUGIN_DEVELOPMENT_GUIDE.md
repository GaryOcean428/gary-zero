# Plugin Development Guide

## Overview

Gary-Zero now supports a dynamic plugin system that allows you to create, install, and manage tools at runtime without modifying the core codebase.

## Plugin Structure

A plugin consists of:

1. **Plugin Directory**: A folder containing all plugin files
2. **Metadata File**: `plugin.json` with plugin information
3. **Implementation File**: Python file with the tool class (default: `plugin.py`)

### Plugin Directory Structure

```
plugins/
└── your_plugin_name/
    ├── plugin.json          # Plugin metadata
    ├── plugin.py           # Plugin implementation
    └── README.md           # Optional documentation
```

## Plugin Metadata (plugin.json)

```json
{
  "name": "your_plugin_name",
  "version": "1.0.0",
  "description": "Description of what your plugin does",
  "author": "your-name",
  "capabilities": ["capability1", "capability2"],
  "dependencies": ["json", "datetime"],
  "entry_point": "plugin.py"
}
```

### Required Fields

- `name`: Unique plugin identifier (alphanumeric, underscore, dash only)
- `version`: Semantic version (e.g., "1.0.0")
- `description`: Brief description of plugin functionality
- `author`: Plugin author/maintainer
- `capabilities`: List of capabilities provided
- `dependencies`: Python modules required (must be whitelisted)
- `entry_point`: Main Python file (default: "plugin.py")

## Plugin Implementation

### Basic Plugin Template

```python
"""Your plugin description."""

import json
from datetime import datetime

# Try to import the full Tool class, fallback to our simple base
try:
    from framework.helpers.tool import Response, Tool
    BaseClass = Tool
except ImportError:
    from framework.plugins.base import Response, PluginTool
    BaseClass = PluginTool


class YourPluginClass(BaseClass):
    """Your plugin class description."""

    async def execute(self, **kwargs) -> Response:
        """Execute the plugin."""

        action = self.args.get("action", "default").lower()

        if action == "action1":
            return await self._action1()
        elif action == "action2":
            return await self._action2()
        else:
            return Response(
                message=f"Unknown action: {action}. Available: action1, action2",
                break_loop=False
            )

    async def _action1(self) -> Response:
        """Handle action1."""
        return Response(
            message="Action1 completed successfully",
            break_loop=False
        )

    async def _action2(self) -> Response:
        """Handle action2."""
        param = self.args.get("param", "default")
        return Response(
            message=f"Action2 completed with param: {param}",
            break_loop=False
        )
```

### Response Object

All plugin methods should return a `Response` object:

```python
Response(
    message="Your response message",  # Required: text to display
    break_loop=False                  # Optional: whether to break execution loop
)
```

## Plugin Management CLI

Use the `plugin_manager.py` script to manage plugins:

### List Plugins

```bash
python plugin_manager.py list
python plugin_manager.py list --enabled-only
```

### Show Plugin Details

```bash
python plugin_manager.py show plugin_name
```

### Enable/Disable Plugins

```bash
python plugin_manager.py enable plugin_name
python plugin_manager.py disable plugin_name
```

### Install Plugin

```bash
python plugin_manager.py install /path/to/plugin/directory
python plugin_manager.py install /path/to/plugin/directory --disable
```

### Uninstall Plugin

```bash
python plugin_manager.py uninstall plugin_name
python plugin_manager.py uninstall plugin_name --force
```

### Other Commands

```bash
python plugin_manager.py refresh          # Refresh plugin discovery
python plugin_manager.py validate plugin_name  # Check dependencies
python plugin_manager.py capabilities     # List all capabilities
```

## Security Considerations

### Whitelisted Dependencies

Only these Python modules are allowed in plugins:
- `os`, `sys`, `json`, `re`, `datetime`, `typing`, `pathlib`
- `requests`, `httpx`, `aiohttp`, `asyncio`, `sqlite3`
- `framework.helpers.tool`, `framework.helpers.response`

### Restricted Operations

Plugins cannot use:
- `subprocess`, `eval`, `exec`, `compile`, `globals`, `__import__`
- World-writable files
- Unsigned plugins from untrusted authors

### Trusted Authors

- `gary-zero-official`: Official Gary-Zero plugins
- `system`: System-level plugins

## Example Plugins

### 1. Simple Test Plugin

```json
{
  "name": "simple_test",
  "version": "1.0.0",
  "description": "Simple test plugin with minimal dependencies",
  "author": "gary-zero-official",
  "capabilities": ["testing", "demo"],
  "dependencies": ["json"],
  "entry_point": "plugin.py"
}
```

### 2. Calendar Integration

```json
{
  "name": "calendar_integration",
  "version": "1.0.0",
  "description": "Integration with calendar systems",
  "author": "gary-zero-official",
  "capabilities": ["calendar", "scheduling", "events"],
  "dependencies": ["datetime", "json"],
  "entry_point": "plugin.py"
}
```

## Usage in Agent

Once installed and enabled, plugins can be called like any other tool:

```json
{
  "tool_name": "your_plugin_name",
  "tool_args": {
    "action": "action1",
    "param": "value"
  }
}
```

## Best Practices

1. **Use semantic versioning** for plugin versions
2. **Provide clear descriptions** and documentation
3. **Handle errors gracefully** with informative messages
4. **Validate input parameters** in your plugin methods
5. **Use meaningful capability names** to help users discover functionality
6. **Keep dependencies minimal** to avoid conflicts
7. **Test your plugin thoroughly** before distribution

## Troubleshooting

### Plugin Not Loading

- Check that `plugin.json` is valid JSON
- Ensure the entry point file exists
- Verify all dependencies are whitelisted
- Check for syntax errors in plugin code

### Permission Denied

- Ensure plugin directory is not world-writable
- Check file permissions are appropriate

### Import Errors

- Verify all dependencies are listed in metadata
- Ensure dependencies are installed and whitelisted

### Plugin Not Found

- Run `python plugin_manager.py refresh` to discover new plugins
- Check plugin is in the correct directory structure
- Verify plugin name matches directory name
