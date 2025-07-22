"""
Shared MCP Server Implementation
===============================

This module provides the shared MCP server implementation extracted from gary-zero.
It includes the core server functionality, tools, and middleware that can be reused
across all repositories in the Gary ecosystem.
"""

import os
import threading
from typing import Annotated, Literal, Union
from urllib.parse import urlparse

from fastmcp import FastMCP
from fastmcp.server.http import create_sse_app
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from ..types import ToolResponse, ToolError


class SharedMCPServer:
    """Reusable MCP server for all repositories"""
    
    def __init__(self, app_name: str, instructions: str = None):
        """
        Initialize the shared MCP server
        
        Args:
            app_name: Name of the application using this server
            instructions: Optional custom instructions for the server
        """
        self.app_name = app_name
        self.mcp = FastMCP(
            name=f"{app_name} integrated MCP Server",
            instructions=instructions or self._get_default_instructions()
        )
        self._tools = {}  # Registry for custom tools
        
    def _get_default_instructions(self) -> str:
        """Get default instructions for the MCP server"""
        return f"""
        Connect to remote {self.app_name} instance.
        {self.app_name} is a general AI assistant controlling its linux environment.
        {self.app_name} can install software, manage files, execute commands, code, use internet, etc.
        {self.app_name}'s environment is isolated unless configured otherwise.
        """
        
    def register_tools(self, tools: list):
        """Register application-specific tools"""
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'execute'):
                self._tools[tool.name] = tool
                # Register with FastMCP if it has the proper decorators
                if hasattr(tool, '_fastmcp_decorator'):
                    tool._fastmcp_decorator(self.mcp)
                    
    def register_message_handler(self, handler_func):
        """Register a message handler function"""
        @self.mcp.tool(
            name="send_message",
            description="Send a message to the remote instance",
            tags={
                "agent_zero", "chat", "remote", "communication", "dialogue",
                "sse", "send", "message", "start", "new", "continue",
            },
            annotations={
                "remote": True,
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
                "title": "Send a message to the remote instance",
            },
        )
        async def send_message_tool(
            message: Annotated[str, Field(description="The message to send", title="message")],
            attachments: Annotated[list[str], Field(description="Optional attachments", title="attachments")] | None = None,
            chat_id: Annotated[str, Field(description="Optional chat ID to continue", title="chat_id")] | None = None,
            persistent_chat: Annotated[bool, Field(description="Whether to use persistent chat", title="persistent_chat")] | None = None,
        ) -> Annotated[Union[ToolResponse, ToolError], Field(description="The response", title="response")]:
            try:
                return await handler_func(message, attachments, chat_id, persistent_chat)
            except Exception as e:
                return ToolError(error=str(e), chat_id=chat_id or "")
                
    def register_finish_chat_handler(self, handler_func):
        """Register a finish chat handler function"""
        @self.mcp.tool(
            name="finish_chat",
            description="Finish a chat with the remote instance",
            tags={
                "agent_zero", "chat", "remote", "communication", "dialogue",
                "sse", "finish", "close", "end", "stop",
            },
            annotations={
                "remote": True,
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": False,
                "openWorldHint": False,
                "title": "Finish a chat with the remote instance",
            },
        )
        async def finish_chat_tool(
            chat_id: Annotated[str, Field(description="ID of the chat to finish", title="chat_id")],
        ) -> Annotated[Union[ToolResponse, ToolError], Field(description="The response", title="response")]:
            try:
                return await handler_func(chat_id)
            except Exception as e:
                return ToolError(error=str(e), chat_id=chat_id)
                
    def get_fastmcp_instance(self) -> FastMCP:
        """Get the underlying FastMCP instance for advanced usage"""
        return self.mcp


class DynamicMcpProxy:
    """A dynamic proxy that allows swapping the underlying MCP application on the fly."""
    
    _instance: "DynamicMcpProxy | None" = None

    def __init__(self, token_provider=None):
        """
        Initialize the proxy
        
        Args:
            token_provider: Function that returns the current token
        """
        self.app: ASGIApp | None = None
        self._lock = threading.RLock()
        self.token_provider = token_provider
        self.shared_server: SharedMCPServer | None = None

    @staticmethod
    def get_instance(token_provider=None):
        if DynamicMcpProxy._instance is None:
            DynamicMcpProxy._instance = DynamicMcpProxy(token_provider)
        return DynamicMcpProxy._instance

    def reconfigure(self, shared_server: SharedMCPServer, token: str):
        """Reconfigure the proxy with a new server and token"""
        self.shared_server = shared_server
        sse_path = f"/t-{token}/sse"
        message_path = f"/t-{token}/messages/"

        with self._lock:
            self.app = create_sse_app(
                server=shared_server.get_fastmcp_instance(),
                message_path=message_path,
                sse_path=sse_path,
                middleware=[Middleware(BaseHTTPMiddleware, dispatch=self._create_middleware())],
            )

    def _create_middleware(self):
        """Create middleware function"""
        async def mcp_middleware(request: Request, call_next):
            # Add any middleware logic here
            # For now, just pass through
            return await call_next(request)
        return mcp_middleware

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Forward the ASGI calls to the current app"""
        with self._lock:
            app = self.app
        if app:
            await app(scope, receive, send)
        else:
            raise RuntimeError("MCP app not initialized")