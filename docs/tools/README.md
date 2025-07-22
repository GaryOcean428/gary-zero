# Gary-Zero Tools Documentation

This directory contains documentation for Gary-Zero's tools and instruments.

## Available Tools

### Core Tools
- [Anthropic Computer Use & Claude Code](./anthropic-computer-use-claude-code.md) - Desktop automation and advanced code editing capabilities

### Tool Categories

#### Desktop Automation
- **Computer Use Tool**: Mouse, keyboard, and window control for desktop automation

#### Code Development  
- **Claude Code Tool**: Multi-file editing, Git operations, and terminal commands

#### Browser Automation
- **Browser Agent**: Web automation and interaction capabilities (existing)

#### Code Execution
- **Code Execution Tool**: Python, Node.js, and terminal execution (existing)

#### Knowledge & Memory
- **Knowledge Tool**: Access to knowledge base and documentation (existing)
- **Memory Tools**: Save, load, and manage agent memory (existing)

## Tool Development

### Creating New Tools

1. **Inherit from Tool base class**:
   ```python
   from framework.helpers.tool import Tool, Response
   
   class MyCustomTool(Tool):
       async def execute(self, **kwargs) -> Response:
           # Tool implementation
           return Response(message="Result", break_loop=False)
   ```

2. **Add to framework/tools/ directory**
3. **Create comprehensive tests**
4. **Update settings if needed**
5. **Add documentation**

### Tool Design Principles

- **Security First**: Tools should be disabled by default and include appropriate safety measures
- **User Control**: Provide granular settings for tool behavior
- **Error Handling**: Gracefully handle errors and edge cases
- **Documentation**: Include clear usage examples and troubleshooting guides
- **Testing**: Comprehensive test coverage including edge cases

### Settings Integration

Tools with configurable behavior should:

1. **Define settings in `framework/helpers/settings/types.py`**
2. **Add default values in `DEFAULT_SETTINGS`**
3. **Create section builder in `framework/helpers/settings/section_builders.py`**
4. **Include section in `framework/helpers/settings/api.py`**

Example settings pattern:
```python
# In types.py
tool_enabled: bool
tool_max_actions: int

# In DEFAULT_SETTINGS
"tool_enabled": False,
"tool_max_actions": 100,
```

## Security Considerations

### Tool Safety
- Tools should default to disabled state
- Implement approval mechanisms for sensitive operations
- Use workspace sandboxing where applicable
- Validate inputs and restrict dangerous operations

### Access Controls
- File system access should be restricted to workspace
- Network access should be configurable
- Command execution should have timeouts and restrictions

### Audit Trail
- Log all tool actions
- Provide clear feedback to users
- Enable monitoring of tool usage

## Contributing

When contributing new tools:

1. Follow existing patterns and conventions
2. Prioritize security and user safety
3. Include comprehensive tests
4. Document usage and configuration
5. Consider backwards compatibility

## See Also

- [Framework Architecture](../framework/README.md)
- [Settings System](../settings/README.md)
- [Security Guidelines](../security/README.md)