# Anthropic Computer Use & Claude Code Tools Documentation

This document describes the newly integrated Anthropic Computer Use and Claude Code tools that enable desktop automation and advanced code editing capabilities in Gary-Zero.

## Table of Contents

1. [Overview](#overview)
2. [Anthropic Computer Use Tool](#anthropic-computer-use-tool)
3. [Claude Code Tool](#claude-code-tool)
4. [Settings Configuration](#settings-configuration)
5. [Security Considerations](#security-considerations)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)

## Overview

Gary-Zero now supports two powerful new tools that extend its capabilities beyond text-based interactions:

- **Anthropic Computer Use Tool**: Enables desktop automation through keyboard, mouse, and window control
- **Claude Code Tool**: Provides context-aware multi-file editing, Git operations, and terminal command execution

Both tools are designed with security in mind and are disabled by default. They require explicit user configuration and, in the case of Computer Use, approval for sensitive operations.

## Anthropic Computer Use Tool

### Features

The Computer Use tool enables Gary-Zero to interact with your desktop environment directly:

- **Screenshot Capture**: Take and save screenshots for analysis
- **Mouse Control**: Click, double-click, move cursor to specific coordinates
- **Keyboard Input**: Type text and send key combinations (Ctrl+C, Alt+Tab, etc.)
- **Scrolling**: Scroll in specific directions at given coordinates
- **Window Management**: Interact with desktop applications and windows

### Configuration

Access settings via the **Tools** tab in the Gary-Zero settings panel:

| Setting | Description | Default |
|---------|-------------|---------|
| Enable Computer Use | Master switch to enable/disable the tool | `false` |
| Require Approval | Request user approval before executing actions | `true` |
| Screenshot Interval | Time between automatic screenshots (seconds) | `1.0` |
| Max Actions Per Session | Maximum actions allowed per session | `50` |

### Safety Features

- **Disabled by Default**: Tool is disabled until explicitly enabled
- **Approval System**: Actions require user confirmation when enabled
- **Action Limits**: Prevents runaway automation with session limits
- **Coordinate Validation**: Ensures mouse actions stay within screen bounds
- **GUI Detection**: Gracefully handles headless environments

### Supported Actions

```python
# Screenshot
{"action": "screenshot"}

# Mouse Click
{"action": "click", "x": 100, "y": 200, "button": "left", "double_click": false}

# Type Text
{"action": "type", "text": "Hello, World!"}

# Key Press
{"action": "key", "keys": "ctrl+c"}  # or "enter", "tab", etc.

# Mouse Movement
{"action": "move", "x": 300, "y": 400}

# Scrolling
{"action": "scroll", "x": 500, "y": 600, "direction": "up", "clicks": 3}
```

## Claude Code Tool

### Features

The Claude Code tool provides advanced code editing and development workflow automation:

- **File Operations**: Read, write, create, delete files and directories
- **Git Integration**: Full Git workflow support (status, add, commit, push, pull)
- **Terminal Commands**: Execute shell commands with timeout controls
- **Workspace Management**: Project navigation, search, and structure analysis
- **Multi-file Editing**: Context-aware editing across multiple files

### Configuration

Access settings via the **Tools** tab in the Gary-Zero settings panel:

| Setting | Description | Default |
|---------|-------------|---------|
| Enable Claude Code | Master switch to enable/disable the tool | `false` |
| Max File Size | Maximum file size in bytes that can be processed | `1048576` (1MB) |
| Enable Git Operations | Allow Git commands | `true` |
| Enable Terminal Commands | Allow shell command execution | `true` |

### Security Features

- **Disabled by Default**: Tool is disabled until explicitly enabled
- **Path Restrictions**: Prevents access to sensitive directories (`.git`, `node_modules`, etc.)
- **File Type Filtering**: Only allows editing of approved file extensions
- **Size Limits**: Prevents processing of excessively large files
- **Workspace Sandboxing**: Operations restricted to project workspace

### Supported Operations

#### File Operations

```python
# Read file
{"operation_type": "file", "operation": "read", "path": "src/main.py"}

# Write file (creates backup)
{"operation_type": "file", "operation": "write", "path": "src/main.py", "content": "new content"}

# Create new file
{"operation_type": "file", "operation": "create", "path": "src/new_file.py", "content": "initial content"}

# Delete file
{"operation_type": "file", "operation": "delete", "path": "temp.txt"}

# List directory
{"operation_type": "file", "operation": "list", "path": "src/"}
```

#### Git Operations

```python
# Git status
{"operation_type": "git", "operation": "status"}

# Add files
{"operation_type": "git", "operation": "add", "files": ["file1.py", "file2.py"]}

# Commit changes
{"operation_type": "git", "operation": "commit", "message": "Add new feature"}

# Push/pull
{"operation_type": "git", "operation": "push"}
{"operation_type": "git", "operation": "pull"}
```

#### Terminal Operations

```python
# Execute command
{"operation_type": "terminal", "command": "npm test", "cwd": "./", "timeout": 60}
```

#### Workspace Operations

```python
# Get workspace info
{"operation_type": "workspace", "operation": "info"}

# Search files
{"operation_type": "workspace", "operation": "search", "pattern": "config"}

# Directory tree
{"operation_type": "workspace", "operation": "tree", "max_depth": 3}
```

## Settings Configuration

### Enabling the Tools

1. Open Gary-Zero settings
2. Navigate to the **Tools** tab
3. Toggle the desired tools to enabled
4. Configure additional settings as needed
5. Save settings

### Security Recommendations

For production use, consider these security practices:

- Keep Computer Use approval requirement enabled
- Set conservative action limits for Computer Use
- Limit Claude Code file size restrictions
- Review allowed file extensions for Claude Code
- Monitor terminal command execution logs

## Security Considerations

### Computer Use Tool

- **Physical Security**: Can control mouse and keyboard
- **Screen Access**: Can capture screenshots
- **Application Control**: Can interact with any desktop application
- **Mitigation**: Approval system, action limits, coordinate validation

### Claude Code Tool

- **File System Access**: Can read, write, and delete files
- **Git Operations**: Can commit and push code changes
- **Terminal Access**: Can execute arbitrary shell commands
- **Mitigation**: Path restrictions, file type filtering, workspace sandboxing

### General Security

- Both tools are **disabled by default**
- Tools respect workspace boundaries
- Comprehensive logging of all actions
- Error handling prevents crashes from affecting the main system

## Usage Examples

### Example 1: Automated Screenshot Analysis

```python
# Agent takes screenshot and analyzes it
tool_response = await computer_use_tool.execute(action="screenshot")
# Tool saves screenshot and provides path for analysis
```

### Example 2: Code Review and Modification

```python
# Read existing code
code_content = await claude_code_tool.execute(
    operation_type="file",
    operation="read",
    path="src/api.py"
)

# Modify code based on analysis
await claude_code_tool.execute(
    operation_type="file",
    operation="write",
    path="src/api.py",
    content=modified_code
)

# Commit changes
await claude_code_tool.execute(
    operation_type="git",
    operation="commit",
    message="Fix API endpoint validation"
)
```

### Example 3: Development Workflow Automation

```python
# Check project status
await claude_code_tool.execute(operation_type="workspace", operation="info")

# Run tests
await claude_code_tool.execute(
    operation_type="terminal",
    command="npm test",
    timeout=120
)

# If tests pass, push changes
await claude_code_tool.execute(operation_type="git", operation="push")
```

## Troubleshooting

### Computer Use Tool

**Problem**: "Computer Use tool requires GUI environment"
- **Solution**: Tool requires a display. Not available in headless environments.

**Problem**: "Maximum actions per session reached"
- **Solution**: Increase the action limit in settings or restart the session.

**Problem**: "Invalid coordinates"
- **Solution**: Ensure click coordinates are within screen bounds.

### Claude Code Tool

**Problem**: "Access denied to path"
- **Solution**: Path is restricted for security. Ensure path is within workspace.

**Problem**: "File type not allowed"
- **Solution**: File extension not in allowed list. Check settings configuration.

**Problem**: "File too large"
- **Solution**: File exceeds size limit. Increase limit in settings or split file.

**Problem**: "Git operations are disabled"
- **Solution**: Enable Git operations in tool settings.

### General Issues

**Problem**: Tools not appearing in agent capabilities
- **Solution**: Ensure tools are enabled in settings and restart if necessary.

**Problem**: Permission errors
- **Solution**: Check file/directory permissions and workspace configuration.

## API Reference

Both tools inherit from the base `Tool` class and implement the standard Gary-Zero tool interface:

```python
class AnthropicComputerUse(Tool):
    async def execute(self, **kwargs) -> Response:
        # Implementation

class ClaudeCode(Tool):
    async def execute(self, **kwargs) -> Response:
        # Implementation
```

Response format:

```python
@dataclass
class Response:
    message: str      # Result description
    break_loop: bool  # Whether to stop agent execution
```

## Contributing

To extend these tools:

1. Follow the existing tool patterns in `framework/tools/`
2. Add appropriate tests in `tests/`
3. Update settings configuration if needed
4. Ensure security considerations are addressed
5. Update documentation

## See Also

- [Gary-Zero Tool Development Guide](../development/tools.md)
- [Settings System Documentation](../settings/README.md)
- [Security Best Practices](../security/best-practices.md)
