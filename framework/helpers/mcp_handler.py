"""
MCP Handler (Compatibility Layer)
===============================

This module provides backward compatibility for gary-zero's MCP handler implementation.
The actual implementation has been moved to the shared MCP library.

This module re-exports the necessary components to maintain backward compatibility.
"""

# Import from compatibility layer
from .mcp_handler_compat import (
    initialize_mcp,
    MCPTool,
    MCPConfig,
    normalize_name,
)

# Re-export for backward compatibility
__all__ = [
    "initialize_mcp",
    "MCPTool", 
    "MCPConfig",
    "normalize_name",
]
