# Usage Examples for Shared MCP Library

This document provides examples of how to use the shared MCP library in different repositories within the Gary ecosystem.

## Table of Contents

1. [Server Examples](#server-examples)
2. [Client Examples](#client-examples)
3. [Migration from Gary-Zero](#migration-from-gary-zero)
4. [Integration in Other Repositories](#integration-in-other-repositories)

## Server Examples

### Basic Server Setup

```python
from shared_mcp.server import SharedMCPServer
from shared_mcp.types import ToolResponse, ToolError

# Create server instance
server = SharedMCPServer(
    app_name="my-app",
    instructions="Custom instructions for my application"
)

# Define message handler
async def handle_message(message, attachments, chat_id, persistent_chat):
    try:
        # Your message processing logic here
        result = f"Processed message: {message}"
        return ToolResponse(
            response=result,
            chat_id=chat_id or "new-chat"
        )
    except Exception as e:
        return ToolError(
            error=str(e),
            chat_id=chat_id or ""
        )

# Register the handler
server.register_message_handler(handle_message)

# Define finish chat handler
async def handle_finish_chat(chat_id):
    try:
        # Your chat cleanup logic here
        return ToolResponse(
            response="Chat finished successfully",
            chat_id=chat_id
        )
    except Exception as e:
        return ToolError(
            error=str(e),
            chat_id=chat_id
        )

# Register the finish handler
server.register_finish_chat_handler(handle_finish_chat)

# Get FastMCP instance for advanced usage
mcp_instance = server.get_fastmcp_instance()
```

### Server with Custom Tools

```python
from shared_mcp.server import SharedMCPServer

server = SharedMCPServer("my-app")

# Register custom tools (example)
custom_tools = [
    # Your custom tool implementations
]
server.register_tools(custom_tools)

# Use with dynamic proxy for HTTP serving
from shared_mcp.server import DynamicMcpProxy

proxy = DynamicMcpProxy.get_instance()
proxy.reconfigure(server, "my-token")
```

## Client Examples

### Basic Client Setup

```python
from shared_mcp.client import SharedMCPClient

# Create client instance
client = SharedMCPClient()

# Define server configurations
server_configs = [
    {
        "name": "local-server",
        "description": "Local MCP server",
        "command": "python",
        "args": ["my_mcp_server.py"],
        "disabled": False
    },
    {
        "name": "remote-server",
        "description": "Remote MCP server",
        "url": "http://localhost:8000/sse",
        "headers": {"Authorization": "Bearer token"},
        "disabled": False
    }
]

# Connect to servers
await client.connect_to_servers(server_configs)

# Get server status
status = client.get_servers_status()
print("Server status:", status)

# List available tools
tools = client.get_tools()
print("Available tools:", tools)

# Use a tool
if client.has_tool("local-server.my-tool"):
    result = await client.call_tool("local-server.my-tool", {
        "param1": "value1",
        "param2": "value2"
    })
    print("Tool result:", result)
```

### Client with Custom Settings

```python
from shared_mcp.client import SharedMCPClient

# Define settings provider
def my_settings_provider():
    return {
        "mcp_client_init_timeout": 60,  # seconds
        "mcp_client_tool_timeout": 120  # seconds
    }

# Create client with custom settings
client = SharedMCPClient(my_settings_provider)

# Rest of usage same as above...
```

## Migration from Gary-Zero

The shared library maintains backward compatibility, so existing gary-zero code continues to work:

### Before (Gary-Zero specific)

```python
from framework.helpers.mcp_server import mcp_server, DynamicMcpProxy
from framework.helpers.mcp_handler import MCPConfig, initialize_mcp

# This still works unchanged
config = MCPConfig.get_instance()
initialize_mcp('{"servers": []}')
```

### After (Using Shared Library Directly)

```python
from shared_mcp.server import SharedMCPServer
from shared_mcp.client import SharedMCPClient

# New approach - more flexible and reusable
server = SharedMCPServer("gary-zero")
client = SharedMCPClient()
```

### Migration Steps

1. **Phase 1 (Immediate)**: Continue using existing imports - backward compatibility maintained
2. **Phase 2 (Optional)**: Gradually migrate to direct shared library usage for new features
3. **Phase 3 (Future)**: Consider full migration to shared library for cleaner architecture

## Integration in Other Repositories

### For monkey1 Repository

```python
# In monkey1/mcp_integration.py
from shared_mcp.server import SharedMCPServer
from shared_mcp.client import SharedMCPClient

class Monkey1MCPServer:
    def __init__(self):
        self.server = SharedMCPServer(
            app_name="monkey1",
            instructions="""
            Connect to monkey1 AI agent.
            Monkey1 specializes in data analysis and machine learning tasks.
            """
        )
        self._setup_handlers()

    def _setup_handlers(self):
        async def handle_analysis_request(message, attachments, chat_id, persistent_chat):
            # Monkey1-specific analysis logic
            result = self._perform_analysis(message, attachments)
            return ToolResponse(response=result, chat_id=chat_id or "")

        self.server.register_message_handler(handle_analysis_request)

    def _perform_analysis(self, message, attachments):
        # Your monkey1-specific logic here
        return f"Analysis complete: {message}"

# Usage
monkey1_server = Monkey1MCPServer()
```

### For Gary8D Repository

```python
# In gary8d/mcp_integration.py
from shared_mcp.server import SharedMCPServer
from shared_mcp.client import SharedMCPClient

class Gary8DServer:
    def __init__(self):
        self.server = SharedMCPServer(
            app_name="gary8d",
            instructions="""
            Connect to Gary8D multi-dimensional AI assistant.
            Gary8D handles complex multi-step reasoning and planning.
            """
        )
        self._setup_handlers()

    def _setup_handlers(self):
        async def handle_planning_request(message, attachments, chat_id, persistent_chat):
            # Gary8D-specific planning logic
            plan = self._create_plan(message)
            return ToolResponse(response=plan, chat_id=chat_id or "")

        self.server.register_message_handler(handle_planning_request)

    def _create_plan(self, message):
        # Your Gary8D-specific logic here
        return f"Plan created for: {message}"

# Usage
gary8d_server = Gary8DServer()
```

### Cross-Repository Communication

```python
# Repository A connecting to Repository B
from shared_mcp.client import SharedMCPClient

async def connect_to_other_repos():
    client = SharedMCPClient()

    # Connect to multiple repositories
    configs = [
        {
            "name": "gary-zero",
            "url": "http://gary-zero.local:8000/sse",
            "description": "Main Gary-Zero instance"
        },
        {
            "name": "monkey1",
            "url": "http://monkey1.local:8001/sse",
            "description": "Monkey1 analysis agent"
        },
        {
            "name": "gary8d",
            "url": "http://gary8d.local:8002/sse",
            "description": "Gary8D planning agent"
        }
    ]

    await client.connect_to_servers(configs)

    # Use tools from different repositories
    gary_result = await client.call_tool("gary-zero.send_message", {
        "message": "Hello from another repo"
    })

    analysis_result = await client.call_tool("monkey1.analyze_data", {
        "data": "some data to analyze"
    })

    plan_result = await client.call_tool("gary8d.create_plan", {
        "goal": "complex multi-step task"
    })

    return gary_result, analysis_result, plan_result
```

## Configuration Examples

### Server Configuration for Production

```python
from shared_mcp.server import SharedMCPServer, DynamicMcpProxy

# Production server setup
def setup_production_server(app_name, token):
    server = SharedMCPServer(
        app_name=app_name,
        instructions=f"""
        Production {app_name} server.
        This server handles production workloads with enhanced security and monitoring.
        """
    )

    # Register production handlers with error handling
    async def production_handler(message, attachments, chat_id, persistent_chat):
        try:
            # Production logic with logging, monitoring, etc.
            result = await process_production_request(message, attachments)
            return ToolResponse(response=result, chat_id=chat_id or "")
        except Exception as e:
            # Log error, send alerts, etc.
            log_production_error(e)
            return ToolError(error="Internal server error", chat_id=chat_id or "")

    server.register_message_handler(production_handler)

    # Setup proxy with production token
    proxy = DynamicMcpProxy.get_instance()
    proxy.reconfigure(server, token)

    return server, proxy

async def process_production_request(message, attachments):
    # Your production processing logic
    return f"Production processed: {message}"

def log_production_error(error):
    # Your production error logging
    print(f"Production error: {error}")
```

### Client Configuration for Multiple Environments

```python
from shared_mcp.client import SharedMCPClient

class MultiEnvironmentClient:
    def __init__(self, environment="development"):
        self.environment = environment
        self.client = SharedMCPClient(self._get_settings)

    def _get_settings(self):
        if self.environment == "production":
            return {
                "mcp_client_init_timeout": 30,
                "mcp_client_tool_timeout": 60
            }
        else:
            return {
                "mcp_client_init_timeout": 60,
                "mcp_client_tool_timeout": 120
            }

    async def connect_to_environment(self):
        configs = self._get_environment_configs()
        await self.client.connect_to_servers(configs)

    def _get_environment_configs(self):
        if self.environment == "production":
            return [
                {
                    "name": "prod-gary-zero",
                    "url": "https://gary-zero.prod.local/sse",
                    "headers": {"Authorization": f"Bearer {self._get_prod_token()}"}
                }
            ]
        else:
            return [
                {
                    "name": "dev-gary-zero",
                    "url": "http://localhost:8000/sse"
                }
            ]

    def _get_prod_token(self):
        # Get production token from secure source
        return "production-token"

# Usage
prod_client = MultiEnvironmentClient("production")
await prod_client.connect_to_environment()
```

These examples show how the shared MCP library can be used across different repositories while maintaining consistency and enabling powerful cross-repository communication.
