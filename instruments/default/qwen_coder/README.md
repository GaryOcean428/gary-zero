# Qwen Coder CLI Integration

This directory contains the integration files for the Qwen Coder CLI tool, which provides AI-powered code assistance and generation capabilities using Alibaba's Qwen language model.

## Installation

### Automatic Installation
The CLI will be automatically installed when `qwen_cli_auto_install=true` is set in the configuration and the CLI is not found at startup.

### Manual Installation
You can manually install the CLI using:
```bash
pip install qwen-coder-cli
```

Or run the installation script:
```bash
./install.sh
```

## Configuration

After installation, configure your API key:
```bash
qwen-coder config set api_key YOUR_QWEN_API_KEY
```

Get your API key from: https://dashscope.aliyun.com/

## Features

- **Code Generation**: Generate code from natural language descriptions
- **Code Review**: Analyze code for bugs, security issues, and improvements
- **Code Completion**: Auto-complete code at specific locations
- **Code Explanation**: Get detailed explanations of code functionality
- **Code Refactoring**: Modernize and optimize existing code

## Usage Examples

### Generate Code
```bash
qwen-coder generate --prompt "Create a Python function to sort a list using quicksort" --language python
```

### Review Code
```bash
qwen-coder review --file src/main.py --focus security
```

### Complete Code
```bash
qwen-coder complete --file src/utils.py --line 42
```

### Explain Code
```bash
qwen-coder explain --code "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
```

### Refactor Code
```bash
qwen-coder refactor --file legacy_code.py --type modernize
```

## Agent Integration

The Qwen Coder CLI is integrated into the Zero Agent framework through:

1. **Auto-detection**: Checks for CLI availability at startup
2. **Auto-installation**: Downloads and installs CLI if missing and auto-install is enabled
3. **Environment variables**: Sets `QWEN_CODER_CLI_PATH` when available
4. **Tool wrapper**: Provides `qwen_coder_cli` tool for agent use
5. **Approval workflow**: Respects configured approval modes for security

## Configuration Options

In agent settings:
- `qwen_cli_enabled`: Enable/disable the CLI integration
- `qwen_cli_path`: Path to the CLI binary (default: "qwen-coder")
- `qwen_cli_approval_mode`: Approval mode ("auto", "suggest", "manual")
- `qwen_cli_auto_install`: Enable automatic installation if CLI is missing

## Requirements

- Python 3.8 or higher
- pip package manager
- Qwen API key from Alibaba DashScope
- Internet connection for API requests

## Troubleshooting

### CLI Not Found
If the CLI is not detected:
1. Check if it's installed: `qwen-coder --version`
2. Ensure it's in PATH or set custom path in settings
3. Enable auto-install in configuration
4. Check Python and pip installation

### API Errors
If API requests fail:
1. Verify your API key is configured correctly
2. Check API key permissions and quotas
3. Ensure internet connectivity
4. Check DashScope service status

### Permission Issues
If installation fails due to permissions:
1. Use `pip install --user qwen-coder-cli` for user installation
2. Or use virtual environments
3. Check write permissions in installation directory

## Links

- [Qwen Model Documentation](https://qwen.readthedocs.io/)
- [DashScope API Documentation](https://help.aliyun.com/zh/dashscope/)
- [Qwen GitHub Repository](https://github.com/QwenLM/Qwen)
