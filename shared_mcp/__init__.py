"""
Shared MCP Library for Gary-Zero
===============================

This package provides reusable MCP (Model Context Protocol) implementations
that can be shared across all Gary ecosystem repositories.

The library includes:
- MCP Server implementation (FastMCP-based)
- MCP Client implementation (supports local/remote servers)
- Protocol handlers and tool definitions
- Type definitions and utilities

Usage:
    from shared_mcp.server import SharedMCPServer
    from shared_mcp.client import SharedMCPClient
"""

__version__ = "1.0.0"
__author__ = "Gary Ocean"
__email__ = "gary@garyocean.com"

# Re-export main classes for convenience
from .server import SharedMCPServer
from .client import SharedMCPClient, MCPConfig

__all__ = [
    "SharedMCPServer", 
    "SharedMCPClient", 
    "MCPConfig",
    "__version__"
]