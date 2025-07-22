# OpenAI Codex CLI Usage

The OpenAI Codex CLI tool is available with the following actions:

## Available Actions
{{available_actions}}

## Usage Examples

### Edit a file
```
action: edit
file_path: /path/to/file.py
instruction: Add error handling to the main function
```

### Create a new file
```
action: create
file_path: /path/to/newfile.js
description: Create a React component for user authentication
```

### Execute shell command
```
action: shell
command: git status
context: Check repository status before committing changes
```

### Check tool status
```
action: status
```

### Install the CLI
```
action: install
```

Please specify the action and required parameters for your request.