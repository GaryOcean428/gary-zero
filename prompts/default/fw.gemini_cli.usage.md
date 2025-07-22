# Google Gemini CLI Usage

The Google Gemini CLI tool is available with the following actions:

## Available Actions
{{available_actions}}

## Usage Examples

### Chat with Gemini
```
action: chat
message: Explain how machine learning works
model: gemini-pro
```

### Generate/analyze code
```
action: code
task: Create a function to sort an array
language: python
file_path: /path/to/file.py (optional)
```

### Generate content
```
action: generate
prompt: Write a technical blog post about microservices
format: markdown
output_file: /path/to/output.md (optional)
```

### Configure CLI
```
action: config
key: api_key
value: YOUR_API_KEY
```

### List configuration
```
action: config
list: true
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