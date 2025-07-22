# OpenAI Codex CLI Integration

This instrument provides integration with the OpenAI Codex CLI for context-aware code editing, file creation, and terminal commands.

## Features

- **Code Editing**: Edit existing files with AI assistance using context-aware instructions
- **File Creation**: Create new files based on natural language descriptions  
- **Terminal Commands**: Execute shell commands with AI guidance and context
- **Safety Controls**: Configurable approval modes and sandboxing for secure execution
- **Auto Installation**: Automatic installation of the CLI tool when needed

## Installation

The OpenAI Codex CLI can be installed automatically when auto-install is enabled, or manually:

```bash
npm install -g @openai/codex-cli
```

## Usage

### Code Editing
Edit an existing file with specific instructions:
```
action: edit
file_path: /path/to/file.py
instruction: Add error handling to the main function
```

### File Creation
Create a new file from a description:
```
action: create
file_path: /path/to/newfile.js
description: Create a React component for user authentication
```

### Shell Commands
Execute terminal commands with context:
```
action: shell
command: git status
context: Check repository status before committing changes
```

### Status Check
Get current CLI status and configuration:
```
action: status
```

### Installation
Install the CLI tool:
```
action: install
```

## Configuration

Configure the tool through Gary-Zero settings:

- **Enable/Disable**: Toggle Codex CLI integration
- **CLI Path**: Path to the executable (default: 'codex')
- **Approval Mode**: 
  - `suggest`: Ask for user approval before each action
  - `auto`: Execute automatically (use with caution)
  - `block`: Block all operations
- **Auto Install**: Automatically install CLI if not found

## Safety Features

- **Approval Workflow**: All operations can require user approval
- **Sandboxed Execution**: Commands run in controlled environment
- **Timeout Controls**: Prevent runaway processes
- **Error Handling**: Comprehensive error reporting and recovery

## API Keys

Ensure your OpenAI API key is configured in Gary-Zero settings for the CLI to function properly.