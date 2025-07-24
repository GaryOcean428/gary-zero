# Shared MCP Library

This is the shared MCP (Model Context Protocol) library extracted from gary-zero. It provides reusable MCP server and client implementations that can be used across all repositories in the Gary ecosystem.


## Features

- **MCP Server Implementation**: FastMCP-based server with tool registration and dynamic configuration
- **MCP Client Implementation**: Support for both local (stdio) and remote (SSE) MCP servers
- **Type Definitions**: Common types and configurations for consistent usage
- **Thread-Safe**: Built with threading safety for concurrent usage


## Installation

```bash
pip install shared-mcp
```


## Usage

### MCP Server

```python
from shared_mcp.server import SharedMCPServer

# Create a server instance
server = SharedMCPServer("my-app", "Custom instructions for my app")

# Register message handler
async def handle_message(message, attachments, chat_id, persistent_chat):
    # Your message handling logic here
    return {"status": "success", "response": "Message processed", "chat_id": chat_id or ""}

server.register_message_handler(handle_message)

# Get FastMCP instance for advanced usage
mcp_instance = server.get_fastmcp_instance()
```

### MCP Client

```python
from shared_mcp.client import SharedMCPClient

# Create a client instance
client = SharedMCPClient()

# Connect to servers
configs = [
    {
        "name": "my-server",
        "url": "http://localhost:8000/sse",
        "description": "My MCP server"
    }
]
await client.connect_to_servers(configs)

# Use tools
tools = client.get_tools()
result = await client.call_tool("my-server.my-tool", {"param": "value"})
```


## Architecture

The library is organized into the following modules:

- `shared_mcp.server`: MCP server implementation and proxy
- `shared_mcp.client`: MCP client implementation and configuration
- `shared_mcp.types`: Common type definitions and configurations


## Compatibility

This library maintains backward compatibility with the original gary-zero implementation while providing a clean, reusable interface for other repositories.


## License

See LICENSE file for details.
