"""
Shared MCP Types
===============

Common type definitions used across the MCP implementation.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """Standard successful tool response"""
    status: Literal["success"] = Field(description="The status of the response", default="success")
    response: str = Field(description="The response from the remote instance")
    chat_id: str = Field(description="The id of the chat this message belongs to.")


class ToolError(BaseModel):
    """Standard error tool response"""
    status: Literal["error"] = Field(description="The status of the response", default="error")
    error: str = Field(description="The error message from the remote instance")
    chat_id: str = Field(description="The id of the chat this message belongs to.")


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str = Field(description="Server name")
    description: str = Field(default="", description="Server description")
    disabled: bool = Field(default=False, description="Whether the server is disabled")
    init_timeout: int = Field(default=0, description="Initialization timeout in seconds")
    tool_timeout: int = Field(default=0, description="Tool execution timeout in seconds")


class MCPServerRemoteConfig(MCPServerConfig):
    """Configuration for a remote MCP server"""
    url: str = Field(description="Server URL")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")


class MCPServerLocalConfig(MCPServerConfig):
    """Configuration for a local MCP server"""
    command: str = Field(description="Command to start the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    encoding: str = Field(default="utf-8", description="Text encoding")
    encoding_error_handler: Literal["strict", "ignore", "replace"] = Field(
        default="strict", description="Encoding error handler"
    )