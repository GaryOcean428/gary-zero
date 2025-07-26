# Google Gemini CLI Integration

This instrument provides integration with the Google Gemini CLI for local model interaction, code assistance, and content generation.

## Features

- **Chat Interface**: Interactive chat with Gemini models
- **Code Generation**: AI-powered code generation and analysis
- **Content Generation**: Create various types of content with AI assistance
- **Configuration Management**: Manage CLI settings and API keys
- **Safety Controls**: Configurable approval modes and secure execution
- **Auto Installation**: Automatic installation of the CLI tool when needed

## Installation

The Google Gemini CLI can be installed automatically when auto-install is enabled, or manually:

```bash
pip install google-generativeai[cli]
```

## Usage

### Chat Interaction

Chat with Gemini models:

```
action: chat
message: Explain how machine learning works
model: gemini-pro
```

### Code Generation/Analysis

Generate or analyze code:

```
action: code
task: Create a function to sort an array
language: python
file_path: /path/to/file.py (optional)
```

### Content Generation

Generate various types of content:

```
action: generate
prompt: Write a technical blog post about microservices
format: markdown
output_file: /path/to/output.md (optional)
```

### Configuration

Manage CLI configuration:

```
action: config
key: api_key
value: YOUR_API_KEY
```

List current configuration:

```
action: config
list: true
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

- **Enable/Disable**: Toggle Gemini CLI integration
- **CLI Path**: Path to the executable (default: 'gemini')
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

Ensure your Google AI API key is configured for the CLI to function properly:

```bash
gemini config set api_key YOUR_GOOGLE_AI_API_KEY
```

## Available Models

- `gemini-pro`: Standard Gemini model for general tasks
- `gemini-pro-vision`: Gemini model with vision capabilities
- `gemini-ultra`: Most capable Gemini model (when available)

## Examples

### Code Review

```
action: code
task: Review this function for potential bugs and improvements
language: javascript
file_path: ./src/utils.js
```

### Documentation Generation

```
action: generate
prompt: Generate API documentation for the user authentication endpoints
format: markdown
output_file: ./docs/auth-api.md
```

### Technical Writing

```
action: chat
message: Help me write a technical specification for a new microservice that handles user notifications
```
