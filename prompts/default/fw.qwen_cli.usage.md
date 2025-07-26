# Qwen Coder CLI Usage

The Qwen Coder CLI tool provides AI-powered code assistance and generation capabilities.

## Available Actions

### Generate Code

Generate new code based on a prompt:

```
qwen_coder_cli action=generate prompt="Create a Python function to calculate fibonacci numbers" language=python output_file=fibonacci.py
```

### Review Code

Review existing code for quality, bugs, and improvements:

```
qwen_coder_cli action=review file_path=src/main.py focus=security
```

### Complete Code

Auto-complete code at a specific location:

```
qwen_coder_cli action=complete file_path=src/utils.py line_number=42 context="data processing function"
```

### Explain Code

Get detailed explanations of code functionality:

```
qwen_coder_cli action=explain code_snippet="def bubble_sort(arr): ..." detail_level=high
```

### Refactor Code

Refactor code for better structure and maintainability:

```
qwen_coder_cli action=refactor file_path=legacy_code.py refactor_type=modernize target=python3.12
```

### Status

Check CLI status and configuration:

```
qwen_coder_cli action=status
```

### Install

Install the CLI tool (if auto-install is enabled):

```
qwen_coder_cli action=install
```

## Parameters

- **action**: Required. One of: {{available_actions}}
- **prompt**: Text description for code generation
- **language**: Programming language (default: python)
- **file_path**: Path to code file to process
- **output_file**: Output file for generated code
- **focus**: Review focus area (security, performance, style, general)
- **line_number**: Specific line for code completion
- **context**: Additional context for operations
- **code_snippet**: Code snippet to explain
- **detail_level**: Explanation detail (low, medium, high)
- **refactor_type**: Type of refactoring (general, modernize, optimize)
- **target**: Target specification for refactoring

## Notes

- The CLI requires configuration with appropriate API keys
- All file operations respect the configured approval mode
- Generated code should be reviewed before use in production
- The tool supports multiple programming languages and frameworks
