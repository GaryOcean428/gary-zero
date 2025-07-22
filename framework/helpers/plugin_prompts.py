"""System prompt enhancement for plugin capabilities."""

from framework.plugins.manager import PluginManager


def get_available_tools_description():
    """Get description of available tools including plugins."""
    try:
        manager = PluginManager()
        plugins = manager.list_plugins(enabled_only=True)
        capabilities = manager.get_available_capabilities()
        
        if not plugins:
            return "Static tools available in framework/tools directory."
        
        description = f"Available tools include {len(plugins)} dynamic plugins providing capabilities: {', '.join(capabilities)}.\n\n"
        description += "Available plugins:\n"
        
        for plugin in plugins:
            description += f"- {plugin['name']}: {plugin['description']}\n"
        
        description += "\nStatic tools in framework/tools are also available."
        
        return description
        
    except Exception as e:
        return f"Static tools available. Plugin system: {e}"


def get_plugin_tools_prompt():
    """Get a prompt section describing plugin tools."""
    return f"""
## Available Tools

{get_available_tools_description()}

Use tools by calling them with JSON format:
```json
{{
  "tool_name": "plugin_name",
  "tool_args": {{
    "action": "action_name",
    "param": "value"
  }}
}}
```

Plugin capabilities can be combined and chained for complex workflows.
"""


if __name__ == "__main__":
    print(get_plugin_tools_prompt())