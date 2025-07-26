# MCP (Model Context Protocol) Integration Guide

This guide explains how to integrate and use MCP servers with Gary-Zero to extend AI model capabilities with
external tools and resources.

## What is MCP?

The Model Context Protocol (MCP) is a standardized way for AI models to interact with external tools, services, and
data sources. It enables:

- **Tool Discovery**: Automatically discover available tools from connected servers
- **Resource Access**: Access data and files from various sources
- **Service Integration**: Connect to APIs, databases, and external services
- **Cross-Model Compatibility**: Works with all modern AI models

## Architecture

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   AI Model  │────▶│  Gary-Zero   │────▶│ MCP Server  │
│  (Any LLM)  │     │  MCP Client  │     │  (Tools)    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Results    │
                    └──────────────┘
```

## Built-in MCP Servers

Gary-Zero includes several pre-configured MCP servers:

### 1. Filesystem Server
Access and manipulate files on the local system.

**Tools**:
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `create_directory` - Create new directories
- `delete_file` - Delete files
- `move_file` - Move/rename files

**Configuration**:

```python
"filesystem": {
    "allowed_directories": ["/home/user/projects", "/tmp"],
    "read_only": false
}
```

### 2. GitHub Server
Interact with GitHub repositories.

**Tools**:
- `create_repository` - Create new repos
- `list_repositories` - List user/org repos
- `get_file_contents` - Read files from repos
- `create_or_update_file` - Modify repo files
- `create_issue` - Create GitHub issues
- `create_pull_request` - Open PRs

**Configuration**:

```python
"github": {
    "token": "$GITHUB_TOKEN",
    "default_owner": "your-username"
}
```

### 3. Memory Server
Persistent memory storage for agents.

**Tools**:
- `store_memory` - Save information
- `recall_memory` - Retrieve stored data
- `search_memories` - Search memory by content
- `list_memories` - List all memories
- `delete_memory` - Remove memories

**Configuration**:

```python
"memory": {
    "storage_path": "./data/memories",
    "max_memories": 1000
}
```

### 4. Browser Automation (mcp-browserbase)
Control web browsers programmatically.

**Tools**:
- `navigate` - Go to URL
- `click` - Click elements
- `type` - Enter text
- `screenshot` - Capture page
- `extract_text` - Get page text
- `execute_script` - Run JavaScript

**Configuration**:

```python
"mcp-browserbase": {
    "headless": false,
    "timeout": 30000
}
```

### 5. Task Manager (mcp-taskmanager)
Manage and track tasks.

**Tools**:
- `create_task` - Create new task
- `update_task` - Modify task
- `complete_task` - Mark as done
- `list_tasks` - Get all tasks
- `get_task` - Get specific task

**Configuration**:

```python
"mcp-taskmanager": {
    "storage_backend": "sqlite",
    "database_path": "./data/tasks.db"
}
```

## Configuration

### Basic Setup

In your settings or environment:

```python
# Default MCP servers
"mcp_servers": "filesystem,github,memory,mcp-browserbase,mcp-taskmanager",

# Timeouts
"mcp_client_init_timeout": 30,    # Server startup timeout
"mcp_client_tool_timeout": 300,   # Tool execution timeout
```

### Advanced Configuration

Create `.mcp/config.json`:

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_PATHS": "/home/user/projects:/tmp"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "custom-api": {
      "command": "python",
      "args": ["./mcp_servers/custom_api.py"],
      "env": {
        "API_KEY": "${CUSTOM_API_KEY}"
      }
    }
  }
}
```

## Creating Custom MCP Servers

### Basic Python Server

```python
# mcp_servers/weather_server.py
import json
import sys
from typing import Dict, Any

class WeatherMCPServer:
    def __init__(self):
        self.tools = {
            "get_weather": {
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name == "get_weather":
            location = arguments["location"]
            units = arguments.get("units", "celsius")
            # Implement weather API call here
            return {
                "location": location,
                "temperature": 22,
                "units": units,
                "conditions": "sunny"
            }

    def run(self):
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)

            if request["method"] == "tools/list":
                response = {
                    "tools": list(self.tools.values())
                }
            elif request["method"] == "tools/call":
                result = self.handle_tool_call(
                    request["params"]["name"],
                    request["params"]["arguments"]
                )
                response = {"result": result}

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    server = WeatherMCPServer()
    server.run()
```

### TypeScript/Node.js Server

```typescript
// mcp_servers/database_server.ts
import { Server } from '@modelcontextprotocol/sdk';
import { Database } from 'better-sqlite3';

const server = new Server({
  name: 'database-server',
  version: '1.0.0',
});

const db = new Database('./data.db');

server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'query_database',
        description: 'Execute SQL query',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string' },
            params: { type: 'array' }
          },
          required: ['query']
        }
      }
    ]
  };
});

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'query_database') {
    const { query, params = [] } = args;
    const stmt = db.prepare(query);
    const results = stmt.all(...params);
    return { result: results };
  }

  throw new Error(`Unknown tool: ${name}`);
});

server.start();
```

## Using MCP in Gary-Zero

### In Agent Code

```python
from framework.mcp import MCPClient

# Initialize MCP client
mcp_client = MCPClient()

# List available tools from all servers
tools = await mcp_client.list_tools()
print(f"Available tools: {[t['name'] for t in tools]}")

# Call a tool
result = await mcp_client.call_tool(
    server_name="github",
    tool_name="list_repositories",
    arguments={"owner": "gary-zero"}
)

# Access resources
resource = await mcp_client.get_resource(
    server_name="filesystem",
    uri="file:///home/user/data.json"
)
```

### In Workflows

```python
# workflow_example.py
async def research_and_document_workflow():
    """Example workflow using multiple MCP tools"""

    # 1. Search GitHub for relevant repos
    repos = await mcp_client.call_tool(
        "github",
        "search_repositories",
        {"query": "AI agents MCP"}
    )

    # 2. Read documentation from top repo
    docs = await mcp_client.call_tool(
        "github",
        "get_file_contents",
        {
            "owner": repos[0]["owner"],
            "repo": repos[0]["name"],
            "path": "README.md"
        }
    )

    # 3. Store findings in memory
    await mcp_client.call_tool(
        "memory",
        "store_memory",
        {
            "key": "mcp_research",
            "content": docs,
            "metadata": {"date": "2025-01-26"}
        }
    )

    # 4. Create summary document
    await mcp_client.call_tool(
        "filesystem",
        "write_file",
        {
            "path": "./research/mcp_summary.md",
            "content": f"# MCP Research\n\n{docs}"
        }
    )
```

## Best Practices

### 1. Security

- **Limit Permissions**: Only grant necessary access
- **Use Environment Variables**: Never hardcode secrets
- **Validate Input**: Sanitize all tool arguments
- **Audit Logs**: Track all MCP tool usage

```python
# Good: Environment variable
"github": {
    "token": "${GITHUB_TOKEN}"
}

# Bad: Hardcoded token
"github": {
    "token": "ghp_xxxxxxxxxxxx"
}
```

### 2. Performance

- **Cache Results**: Store frequently accessed data
- **Batch Operations**: Combine multiple calls when possible
- **Set Timeouts**: Prevent hanging operations
- **Async Execution**: Use async/await for non-blocking calls

### 3. Error Handling

```python
try:
    result = await mcp_client.call_tool(
        "github",
        "create_issue",
        {"title": "Bug report", "body": "..."}
    )
except MCPToolError as e:
    # Handle tool-specific errors
    if e.code == "RATE_LIMIT":
        await asyncio.sleep(60)
        # Retry
    else:
        logger.error(f"Tool error: {e}")
except MCPServerError as e:
    # Handle server connection issues
    logger.error(f"Server error: {e}")
```

### 4. Tool Discovery

```python
# Discover tools dynamically
async def discover_capabilities():
    servers = await mcp_client.list_servers()

    for server in servers:
        tools = await mcp_client.list_tools(server)
        print(f"\n{server} capabilities:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
```

## Advanced Topics

### Resource Subscriptions

Subscribe to resource changes:

```python
# Subscribe to file changes
subscription = await mcp_client.subscribe_resource(
    "filesystem",
    "file:///path/to/config.json",
    on_change=handle_config_change
)

async def handle_config_change(resource):
    print(f"Config updated: {resource['content']}")
```

### Custom Transports

Implement custom transport mechanisms:

```python
class HTTPTransport(MCPTransport):
    """MCP over HTTP for remote servers"""

    async def send(self, message: dict):
        response = await self.session.post(
            f"{self.base_url}/mcp",
            json=message
        )
        return response.json()
```

### Server Composition

Chain multiple MCP servers:

```python
# Composite server that combines capabilities
class CompositeMCPServer:
    def __init__(self, servers: List[MCPServer]):
        self.servers = servers

    async def list_tools(self):
        tools = []
        for server in self.servers:
            tools.extend(await server.list_tools())
        return tools
```

## Troubleshooting

### Common Issues

#### Server won't start
- Check command and args in config
- Verify dependencies installed
- Check logs in `.mcp/logs/`

#### Tool calls timeout
- Increase `mcp_client_tool_timeout`
- Check server performance
- Verify network connectivity

#### Permission denied
- Check file/directory permissions
- Verify API tokens are valid
- Review server configuration

### Debug Mode

Enable detailed logging:

```python
# In settings
"mcp_debug": True,
"mcp_log_level": "DEBUG",
"mcp_log_file": "./logs/mcp.log"
```

### Health Checks

Monitor MCP server health:

```python
async def check_mcp_health():
    status = {}
    for server in await mcp_client.list_servers():
        try:
            await mcp_client.ping(server)
            status[server] = "healthy"
        except Exception as e:
            status[server] = f"unhealthy: {e}"
    return status
```

## Examples

### Example 1: Document Processing Pipeline

```python
async def process_documents():
    # List documents
    files = await mcp_client.call_tool(
        "filesystem",
        "list_directory",
        {"path": "./documents", "pattern": "*.pdf"}
    )

    for file in files:
        # Extract text (using custom PDF server)
        text = await mcp_client.call_tool(
            "pdf-processor",
            "extract_text",
            {"path": file}
        )

        # Analyze with AI
        analysis = await analyze_document(text)

        # Store results
        await mcp_client.call_tool(
            "memory",
            "store_memory",
            {
                "key": f"analysis_{file}",
                "content": analysis
            }
        )
```

### Example 2: Multi-Agent Coordination

```python
async def coordinate_agents():
    # Create task
    task = await mcp_client.call_tool(
        "mcp-taskmanager",
        "create_task",
        {
            "title": "Research AI trends",
            "agents": ["researcher", "writer", "reviewer"]
        }
    )

    # Researcher gathers data
    research = await mcp_client.call_tool(
        "web-search",
        "search",
        {"query": "AI trends 2025"}
    )

    # Writer creates report
    report = await mcp_client.call_tool(
        "ai-writer",
        "generate_report",
        {"research": research}
    )

    # Store and complete
    await mcp_client.call_tool(
        "filesystem",
        "write_file",
        {
            "path": "./reports/ai_trends.md",
            "content": report
        }
    )

    await mcp_client.call_tool(
        "mcp-taskmanager",
        "complete_task",
        {"task_id": task["id"]}
    )
```

## Related Documentation

- [Model Capabilities](./model-capabilities.md) - Model-specific features
- [Computer Use Guide](./computer-use-guide.md) - Desktop automation
- [API Reference](./api/) - Detailed API documentation
- [Security Guide](./SECURE_EXECUTION.md) - Security best practices

---

**Last Updated**: January 2025
**Version**: 1.0
