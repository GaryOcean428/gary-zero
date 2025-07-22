"""
MCP Server (Compatibility Layer)
===============================

This module provides backward compatibility for gary-zero's MCP server implementation.
The actual implementation has been moved to the shared MCP library.

This module re-exports the necessary components to maintain backward compatibility.
"""

# Import from compatibility layer
from .mcp_server_compat import (
    shared_mcp_server,
    mcp_server,
    DynamicMcpProxy,
    mcp_middleware,
    ToolResponse,
    ToolError,
)

# Re-export for backward compatibility
__all__ = [
    "mcp_server",
    "DynamicMcpProxy", 
    "mcp_middleware",
    "ToolResponse",
    "ToolError",
]
