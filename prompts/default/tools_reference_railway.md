# Complete Tools Reference for Railway/E2B Environment

## Core Tools

### 1. **code_execution_tool**
- **Purpose**: Execute code in secure E2B cloud sandboxes
- **Runtimes**: python, javascript/nodejs, terminal, secure_info
- **Railway Context**: All Railway env vars available in sandbox
- **Security**: Complete isolation, no host access
- **Usage**: Primary tool for any code execution needs

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

### Using E2B Effectively
1. **Sandboxes are ephemeral** - Save outputs you need
2. **Network access allowed** - Can call external APIs
3. **Railway vars available** - All env vars accessible
4. **Package installation** - Use terminal runtime first
5. **File operations** - Limited to sandbox directory

### Best Practices

1. **Tool Selection**:
   - Code execution → code_execution_tool
   - Web data → searchxng_tool or webpage_content_tool
   - Browser automation → browser_agent
   - Long-term storage → memorize/memory_load

2. **Error Handling**:
   - Always check tool responses
   - Use knowledge_tool for error research
   - Retry with modifications if needed

3. **Security**:
   - Never expose secrets in code
   - Use env vars for credentials
   - E2B provides isolation automatically

4. **Performance**:
   - Minimize tool calls
   - Batch operations when possible
   - Use appropriate session numbers

### Tool Chaining Example

Research and implement a solution:
```json
// Step 1: Search for information
{
  "tool": "searchxng_tool",
  "query": "Railway.com environment variables best practices"
}

// Step 2: Save important findings
{
  "tool": "memorize",
  "memory": ["Railway uses PORT env var", "Must bind to 0.0.0.0"]
}

// Step 3: Implement solution
{
  "tool": "code_execution_tool",
  "runtime": "python",
  "code": "# Implementation based on research"
}

// Step 4: Respond to user
{
  "tool": "response",
  "text": "Task completed successfully!"
}
```

## Docker Hub Integration Benefits

When Docker Hub is connected:
1. **Custom tool containers** - Deploy specialized environments
2. **Private images** - Keep proprietary tools secure
3. **Version control** - Tag and track tool versions
4. **Faster deploys** - Cached layers speed up builds

Connect via Railway dashboard or set:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `DOCKER_REGISTRY` (optional)