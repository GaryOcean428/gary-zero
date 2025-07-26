# Claude Code CLI Integration

This directory contains the integration files for the Claude Code CLI tool, which provides advanced code editing and terminal operations using Anthropic's Claude language model.

## Installation

### Automatic Installation

The CLI will be automatically installed when `claude_cli_auto_install=true` is set in the configuration and the CLI is not found at startup.

### Manual Installation

You can manually install the CLI using:

```bash
npm install -g @anthropic/claude-code-cli
```

Or run the installation script:

```bash
./install.sh
```

## Configuration

After installation, authenticate with your Anthropic API key:

```bash
claude-code auth login
```

Or set the API key directly:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

## Features

- **Context-Aware Editing**: Multi-file editing with project context
- **Git Integration**: Built-in Git operations and workflow support
- **Terminal Commands**: Execute shell commands with AI assistance
- **File Operations**: Read, write, create, and delete files safely
- **Workspace Management**: Project-wide operations and insights
- **Code Review**: Automated code review and suggestions

## Usage Examples

### File Operations

```bash
claude-code read --file src/main.py
claude-code write --file src/utils.py --content "..."
claude-code create --file new_module.py
claude-code list --directory src/
```

### Git Operations

```bash
claude-code git status
claude-code git add --files src/main.py
claude-code git commit --message "Add new feature"
claude-code git push
```

### Terminal Commands

```bash
claude-code terminal --command "npm test"
claude-code terminal --command "python manage.py migrate"
```

### Workspace Operations

```bash
claude-code workspace info
claude-code workspace search --pattern "TODO"
claude-code workspace tree --max-depth 3
```

## Agent Integration

The Claude Code CLI is integrated into the Zero Agent framework through:

1. **Auto-detection**: Checks for CLI availability at startup
2. **Auto-installation**: Downloads and installs CLI if missing and auto-install is enabled
3. **Environment variables**: Sets `CLAUDE_CODE_CLI_PATH` when available
4. **Tool wrapper**: Provides `claude_code` tool for agent use
5. **Approval workflow**: High-risk operations require approval for security
6. **Sandboxed execution**: All operations run in controlled environment

## Configuration Options

In agent settings:
- `claude_cli_enabled`: Enable/disable the CLI integration
- `claude_cli_path`: Path to the CLI binary (default: "claude-code")
- `claude_cli_approval_mode`: Approval mode ("auto", "suggest", "manual")
- `claude_cli_auto_install`: Enable automatic installation if CLI is missing

## Security Features

- **Approval Workflows**: Sensitive operations require user approval
- **Path Restrictions**: Limited to allowed directories and file types
- **File Size Limits**: Prevents processing oversized files
- **Backup Creation**: Automatic backups before file modifications
- **Risk Assessment**: Operations categorized by risk level

## Requirements

- Node.js 16 or higher
- npm package manager
- Anthropic API key
- Git (for Git operations)
- Internet connection for API requests

## Troubleshooting

### CLI Not Found

If the CLI is not detected:
1. Check if it's installed: `claude-code --version`
2. Ensure Node.js and npm are installed
3. Verify CLI is in PATH or set custom path in settings
4. Enable auto-install in configuration

### Authentication Issues

If authentication fails:
1. Check your API key is valid
2. Run `claude-code auth login` to re-authenticate
3. Verify API key permissions
4. Check internet connectivity

### Permission Errors

If file operations fail:
1. Check file and directory permissions
2. Ensure you're in the correct working directory
3. Verify path restrictions in configuration
4. Check if files are not locked by other processes

### Git Errors

If Git operations fail:
1. Ensure you're in a Git repository
2. Check Git configuration and credentials
3. Verify repository remote settings
4. Ensure working directory is clean for certain operations

## Links

- [Claude Code CLI Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- [Claude Model Guide](https://docs.anthropic.com/claude/docs)
- [Anthropic Console](https://console.anthropic.com/)
