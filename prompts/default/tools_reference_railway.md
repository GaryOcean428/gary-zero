# Complete Tools Reference for Railway/E2B Environment


## Core Tools

### 1. **code_execution_tool**

- **Purpose**: Execute code in secure E2B cloud sandboxes
- **Runtimes**:
  - `python` - Python 3.11+ environment
  - `javascript`/`nodejs` - Node.js environment
  - `terminal` - Bash shell commands
  - `secure_info` - Check execution environment
  - `docker` - Run in Docker container (with Docker Hub access)
- **Docker Hub Integration**:
  - Can pull any Docker image from Docker Hub
  - Access to private images with configured credentials
  - Run specialized environments (ML, databases, etc.)
- **Railway Context**: All Railway env vars available in sandbox
- **Security**: Complete isolation, no host access
- **Usage**: Primary tool for any code execution needs

#### Enhanced Docker Capabilities

With Docker Hub credentials configured:

```json
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "tensorflow/tensorflow:latest-gpu",
  "code": "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
}
```

### 2. **response**

- **Purpose**: Send final answer to user and end task
- **Usage**: Only use when task is complete
- **Format**: `{"tool": "response", "text": "Your complete answer"}`

### 3. **call_subordinate**

- **Purpose**: Delegate subtasks to specialized subordinate agents
- **Roles**: scientist, coder, engineer, researcher, etc.
- **Best Practice**: Provide clear context and goals

### 4. **searchxng_tool**

- **Purpose**: Privacy-focused web search
- **Categories**: general, news, tech, science, images
- **Railway Context**: Uses internal SearXNG service
- **No tracking**: Complete privacy preservation

### 5. **webpage_content_tool**

- **Purpose**: Extract text content from web pages
- **Input**: Full URL with http:// or https://
- **Output**: Main text content, cleaned and formatted


## Memory Tools

### 6. **memory_load**

- **Purpose**: Load saved memories and knowledge
- **Params**: query, threshold, limit, filter
- **Use Cases**: Recall previous solutions, personal info

### 7. **memorize**

- **Purpose**: Save important information long-term
- **Input**: List of memory items
- **Best Practice**: Save solutions, patterns, user preferences

### 8. **memories_delete**

- **Purpose**: Remove specific memories
- **Input**: List of memory IDs
- **Use When**: Outdated or incorrect information

### 9. **knowledge_tool**

- **Purpose**: Manage knowledge base items
- **Operations**: save, search, delete, update
- **Railway Context**: Persisted across deployments


## Browser Tools

### 10. **browser_agent**

- **Purpose**: Control browser via subordinate agent
- **Features**: Full Playwright automation
- **Use Cases**: Web scraping, form filling, testing

### 11. **browser_**** (direct controls)

- **Commands**: open, click, type, wait, search
- **Purpose**: Direct browser control without agent
- **Best For**: Simple, specific browser tasks


## Input/Output Tools

### 12. **input**

- **Purpose**: Send keyboard input to terminal
- **Usage**: Answer prompts, enter passwords
- **Session**: Specify terminal session number

### 13. **vision_load**

- **Purpose**: Load and analyze images
- **Formats**: Common image formats (jpg, png, etc)
- **Note**: Convert to bitmap if needed


## MCP (Model Context Protocol) Tools

### 14. **Dynamic MCP Tools**

- **Source**: External MCP servers
- **Configuration**: Settings → MCP → Configure Servers
- **Examples**:
  - GitHub tools (repos, issues, PRs)
  - Google Drive (docs, sheets)
  - Slack (messages, channels)
  - Custom database connectors
- **Railway Context**: Configured per environment


## Railway-Specific Considerations

### Environment Detection

Always check your environment:

```json
{
  "tool": "code_execution_tool",
  "runtime": "secure_info",
  "code": ""
}
```

### Service Communication

When calling other Railway services:

```json
{
  "tool": "code_execution_tool",
  "runtime": "python",
  "code": "import os\nimport requests\n\n# Internal service call\napi_url = f\"http://{os.getenv('API_RAILWAY_PRIVATE_DOMAIN')}:{os.getenv('API_PORT')}\"\nresponse = requests.get(f\"{api_url}/health\")\nprint(response.json())"
}
```

### Using E2B with Docker Hub

1. **Standard E2B sandboxes** - Default Python/Node/Terminal environments
2. **Docker-enhanced sandboxes** - Any Docker image from Docker Hub
3. **Private images** - Your custom tools and environments
4. **Specialized environments** - ML frameworks, databases, etc.
5. **Full isolation** - Docker runs within E2B's secure sandbox

### Best Practices

1. **Tool Selection**:
   - Standard code → code_execution_tool with python/nodejs
   - Specialized env → code_execution_tool with docker runtime
   - Web data → searchxng_tool or webpage_content_tool
   - Browser automation → browser_agent
   - Long-term storage → memorize/memory_load

2. **Docker Image Selection**:
   - Use official images when possible
   - Specify exact tags for reproducibility
   - Alpine variants for faster pulls
   - Test with public images first

3. **Error Handling**:
   - Always check tool responses
   - Use knowledge_tool for error research
   - Retry with modifications if needed

4. **Security**:
   - Never expose secrets in code
   - Use env vars for credentials
   - E2B provides isolation automatically
   - Docker credentials never exposed to containers

5. **Performance**:
   - Minimize tool calls
   - Batch operations when possible
   - Use appropriate session numbers
   - Cache common Docker images

### Advanced Docker Examples

Machine Learning with GPU:

```json
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime",
  "code": "import torch\nprint(f'CUDA available: {torch.cuda.is_available()}')\nprint(f'Device count: {torch.cuda.device_count()}')"
}
```

Database Operations:

```json
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "mongo:7",
  "code": "mongosh --eval 'db.version()'"
}
```

Custom Development:

```json
{
  "tool": "code_execution_tool",
  "runtime": "docker",
  "docker_image": "golang:1.21-alpine",
  "code": "go version && echo 'package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Hello from Go!\") }' > main.go && go run main.go"
}
```


## Docker Hub Access Benefits

With Docker Hub credentials configured:
1. **Unlimited environments** - Any public Docker image
2. **Private tools** - Your custom images
3. **Specialized software** - Pre-configured environments
4. **Version control** - Specific tagged versions
5. **No setup required** - Images ready to use

Your Gary-Zero now has access to:
- `DOCKER_USERNAME` - For authentication
- `DOCKER_PASSWORD` - For private images
- `DOCKER_REGISTRY` - Docker Hub by default

This dramatically expands execution capabilities beyond standard E2B environments!
