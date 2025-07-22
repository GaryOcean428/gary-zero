"""
Shared MCP Client Implementation
===============================

This module provides the shared MCP client implementation extracted from gary-zero.
It supports both local (stdio) and remote (SSE) MCP servers and provides a unified
interface for tool discovery and execution.
"""

import asyncio
import json
import re
import threading
from abc import ABC, abstractmethod
from collections.abc import Awaitable
from contextlib import AsyncExitStack, suppress
from datetime import timedelta
from shutil import which
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    TextIO,
    TypeVar,
    Union,
    cast,
)

from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.shared.message import SessionMessage
from mcp.types import CallToolResult, ListToolsResult
from pydantic import BaseModel, Discriminator, Field, PrivateAttr, Tag

from ..types import MCPServerRemoteConfig, MCPServerLocalConfig


def normalize_name(name: str) -> str:
    """Normalize a server name to be filesystem/URL safe"""
    name = name.strip().lower()
    name = re.sub(r"[^\w]", "_", name, flags=re.UNICODE)
    return name


T = TypeVar("T")


class SharedMCPClient:
    """Reusable MCP client for consuming external servers"""
    
    def __init__(self, settings_provider=None):
        """
        Initialize the shared MCP client
        
        Args:
            settings_provider: Function that returns settings dict with timeout values
        """
        self.config = MCPConfig(settings_provider)
        
    async def connect_to_servers(self, configs: list[dict[str, Any]]):
        """Connect to external MCP servers"""
        await self.config.update_from_configs(configs)
        
    def get_servers_status(self) -> list[dict[str, Any]]:
        """Get status of all connected servers"""
        return self.config.get_servers_status()
        
    def get_tools(self) -> list[dict[str, dict[str, Any]]]:
        """Get all tools from all servers"""
        return self.config.get_tools()
        
    def get_tools_prompt(self, server_name: str = "") -> str:
        """Get a prompt for all tools"""
        return self.config.get_tools_prompt(server_name)
        
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        return self.config.has_tool(tool_name)
        
    async def call_tool(self, tool_name: str, input_data: dict[str, Any]) -> CallToolResult:
        """Call a tool with the given input data"""
        return await self.config.call_tool(tool_name, input_data)


class MCPServerRemote(BaseModel):
    """Remote SSE MCP Server"""
    name: str = Field(default_factory=str)
    description: Optional[str] = Field(default="Remote SSE Server")
    url: str = Field(default_factory=str)
    headers: dict[str, Any] | None = Field(default_factory=dict[str, Any])
    init_timeout: int = Field(default=0)
    tool_timeout: int = Field(default=0)
    disabled: bool = Field(default=False)

    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __client: Optional["MCPClientRemote"] = PrivateAttr(default=None)

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        self.__client = MCPClientRemote(self)
        self.update(config)

    def get_error(self) -> str:
        with self.__lock:
            return self.__client.error  # type: ignore

    def get_log(self) -> str:
        with self.__lock:
            return self.__client.get_log()  # type: ignore

    def get_tools(self) -> list[dict[str, Any]]:
        """Get all tools from the server"""
        with self.__lock:
            return self.__client.tools  # type: ignore

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        with self.__lock:
            return self.__client.has_tool(tool_name)  # type: ignore

    async def call_tool(self, tool_name: str, input_data: dict[str, Any]) -> CallToolResult:
        """Call a tool with the given input data"""
        with self.__lock:
            return await self.__client.call_tool(tool_name, input_data)  # type: ignore

    def update(self, config: dict[str, Any]) -> "MCPServerRemote":
        with self.__lock:
            for key, value in config.items():
                if key in [
                    "name", "description", "url", "serverUrl", "headers",
                    "init_timeout", "tool_timeout", "disabled",
                ]:
                    if key == "name":
                        value = normalize_name(value)
                    if key == "serverUrl":
                        key = "url"  # remap serverUrl to url
                    setattr(self, key, value)
            return asyncio.run(self.__on_update())

    async def __on_update(self) -> "MCPServerRemote":
        await self.__client.update_tools()  # type: ignore
        return self


class MCPServerLocal(BaseModel):
    """Local StdIO MCP Server"""
    name: str = Field(default_factory=str)
    description: Optional[str] = Field(default="Local StdIO Server")
    command: str = Field(default_factory=str)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = Field(default_factory=dict[str, str])
    encoding: str = Field(default="utf-8")
    encoding_error_handler: Literal["strict", "ignore", "replace"] = Field(default="strict")
    init_timeout: int = Field(default=0)
    tool_timeout: int = Field(default=0)
    disabled: bool = Field(default=False)

    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __client: Optional["MCPClientLocal"] = PrivateAttr(default=None)

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        self.__client = MCPClientLocal(self)
        self.update(config)

    def get_error(self) -> str:
        with self.__lock:
            return self.__client.error  # type: ignore

    def get_log(self) -> str:
        with self.__lock:
            return self.__client.get_log()  # type: ignore

    def get_tools(self) -> list[dict[str, Any]]:
        """Get all tools from the server"""
        with self.__lock:
            return self.__client.tools  # type: ignore

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        with self.__lock:
            return self.__client.has_tool(tool_name)  # type: ignore

    async def call_tool(self, tool_name: str, input_data: dict[str, Any]) -> CallToolResult:
        """Call a tool with the given input data"""
        with self.__lock:
            return await self.__client.call_tool(tool_name, input_data)  # type: ignore

    def update(self, config: dict[str, Any]) -> "MCPServerLocal":
        with self.__lock:
            for key, value in config.items():
                if key in [
                    "name", "description", "command", "args", "env", "encoding",
                    "encoding_error_handler", "init_timeout", "tool_timeout", "disabled",
                ]:
                    if key == "name":
                        value = normalize_name(value)
                    setattr(self, key, value)
            return asyncio.run(self.__on_update())

    async def __on_update(self) -> "MCPServerLocal":
        await self.__client.update_tools()  # type: ignore
        return self


MCPServer = Annotated[
    Union[
        Annotated[MCPServerRemote, Tag("MCPServerRemote")],
        Annotated[MCPServerLocal, Tag("MCPServerLocal")],
    ],
    Discriminator(lambda v: "MCPServerRemote" if "url" in v else "MCPServerLocal"),
]


class MCPConfig(BaseModel):
    """MCP Configuration Manager"""
    servers: list[MCPServer] = Field(default_factory=list)
    disconnected_servers: list[dict[str, Any]] = Field(default_factory=list)
    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __instance: ClassVar[Any] = PrivateAttr(default=None)
    __initialized: ClassVar[bool] = PrivateAttr(default=False)
    __settings_provider: Any = PrivateAttr(default=None)

    def __init__(self, settings_provider=None):
        super().__init__()
        self.__settings_provider = settings_provider or (lambda: {
            "mcp_client_init_timeout": 30,
            "mcp_client_tool_timeout": 60
        })
        self.servers = []
        self.disconnected_servers = []

    async def update_from_configs(self, configs: list[dict[str, Any]]):
        """Update configuration from a list of server configs"""
        with self.__lock:
            self.servers = []
            self.disconnected_servers = []
            
            for config in configs:
                if config.get("disabled", False):
                    server_name = normalize_name(config.get("name", "unnamed_server"))
                    self.disconnected_servers.append({
                        "config": config,
                        "error": "Disabled in config",
                        "name": server_name,
                    })
                    continue
                    
                try:
                    if config.get("url") or config.get("serverUrl"):
                        self.servers.append(MCPServerRemote(config))
                    else:
                        self.servers.append(MCPServerLocal(config))
                except Exception as e:
                    server_name = normalize_name(config.get("name", "unnamed_server"))
                    self.disconnected_servers.append({
                        "config": config,
                        "error": str(e),
                        "name": server_name
                    })

    def get_servers_status(self) -> list[dict[str, Any]]:
        """Get status of all servers"""
        result = []
        with self.__lock:
            # add connected/working servers
            for server in self.servers:
                name = server.name
                tool_count = len(server.get_tools())
                connected = True
                error = server.get_error()
                has_log = server.get_log() != ""

                result.append({
                    "name": name,
                    "connected": connected,
                    "error": error,
                    "tool_count": tool_count,
                    "has_log": has_log,
                })

            # add failed servers
            for disconnected in self.disconnected_servers:
                result.append({
                    "name": disconnected["name"],
                    "connected": False,
                    "error": disconnected["error"],
                    "tool_count": 0,
                    "has_log": False,
                })

        return result

    def get_tools(self) -> list[dict[str, dict[str, Any]]]:
        """Get all tools from all servers"""
        with self.__lock:
            tools = []
            for server in self.servers:
                for tool in server.get_tools():
                    tool_copy = tool.copy()
                    tool_copy["server"] = server.name
                    tools.append({f"{server.name}.{tool['name']}": tool_copy})
            return tools

    def get_tools_prompt(self, server_name: str = "") -> str:
        """Get a prompt for all tools"""
        with self.__lock:
            pass

        prompt = '## "Remote (MCP Server) Agent Tools" available:\n\n'
        server_names = []
        for server in self.servers:
            if not server_name or server.name == server_name:
                server_names.append(server.name)

        if server_name and server_name not in server_names:
            raise ValueError(f"Server {server_name} not found")

        for server in self.servers:
            if server.name in server_names:
                server_name = server.name
                prompt += f"### {server_name}\n"
                prompt += f"{server.description}\n"
                tools = server.get_tools()

                for tool in tools:
                    prompt += (
                        f"\n### {server_name}.{tool['name']}:\n"
                        f"{tool['description']}\n\n"
                    )

                    input_schema = json.dumps(tool["input_schema"]) if tool["input_schema"] else ""
                    prompt += f"#### Input schema for tool_args:\n{input_schema}\n\n"

                    prompt += (
                        f"#### Usage:\n"
                        f"{{\n"
                        f'    "thoughts": ["..."],\n'
                        f"    \"tool_name\": \"{server_name}.{tool['name']}\",\n"
                        f'    "tool_args": !follow schema above\n'
                        f"}}\n"
                    )

        return prompt

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        if "." not in tool_name:
            return False
        server_name_part, tool_name_part = tool_name.split(".", 1)
        with self.__lock:
            for server in self.servers:
                if server.name == server_name_part:
                    return server.has_tool(tool_name_part)
            return False

    async def call_tool(self, tool_name: str, input_data: dict[str, Any]) -> CallToolResult:
        """Call a tool with the given input data"""
        if "." not in tool_name:
            raise ValueError(f"Tool {tool_name} not found")
        server_name_part, tool_name_part = tool_name.split(".", 1)
        with self.__lock:
            for server in self.servers:
                if server.name == server_name_part and server.has_tool(tool_name_part):
                    return await server.call_tool(tool_name_part, input_data)
            raise ValueError(f"Tool {tool_name} not found")


class MCPClientBase(ABC):
    """Base class for MCP clients"""
    
    __lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, server: Union[MCPServerLocal, MCPServerRemote]):
        self.server = server
        self.tools: list[dict[str, Any]] = []
        self.error: str = ""
        self.log: list[str] = []
        self.log_file: Optional[TextIO] = None

    @abstractmethod
    async def _create_stdio_transport(self, current_exit_stack: AsyncExitStack) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Create stdio/write streams using the provided exit_stack."""
        ...

    async def _execute_with_session(
        self,
        coro_func: Callable[[ClientSession], Awaitable[T]],
        read_timeout_seconds=60,
    ) -> T:
        """Manages the lifecycle of an MCP session for a single operation."""
        try:
            async with AsyncExitStack() as temp_stack:
                stdio, write = await self._create_stdio_transport(temp_stack)
                session = await temp_stack.enter_async_context(
                    ClientSession(
                        stdio,  # type: ignore
                        write,  # type: ignore
                        read_timeout_seconds=timedelta(seconds=read_timeout_seconds),
                    )
                )
                await session.initialize()
                result = await coro_func(session)
                return result
        except Exception as e:
            raise e from None

    async def update_tools(self) -> "MCPClientBase":
        """Update the tools list from the server"""
        async def list_tools_op(current_session: ClientSession):
            response: ListToolsResult = await current_session.list_tools()
            with self.__lock:
                self.tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

        try:
            await self._execute_with_session(list_tools_op, read_timeout_seconds=30)
        except Exception as e:
            with self.__lock:
                self.tools = []
                self.error = f"Failed to initialize. {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}"
        return self

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available (uses cached tools)"""
        with self.__lock:
            for tool in self.tools:
                if tool["name"] == tool_name:
                    return True
        return False

    def get_tools(self) -> list[dict[str, Any]]:
        """Get all tools from the server (uses cached tools)"""
        with self.__lock:
            return self.tools

    async def call_tool(self, tool_name: str, input_data: dict[str, Any]) -> CallToolResult:
        """Call a tool on the server"""
        if not self.has_tool(tool_name):
            await self.update_tools()
            if not self.has_tool(tool_name):
                raise ValueError(f"Tool {tool_name} not found after refreshing tool list.")

        async def call_tool_op(current_session: ClientSession):
            response: CallToolResult = await current_session.call_tool(
                tool_name,
                input_data,
                read_timeout_seconds=timedelta(seconds=60),
            )
            return response

        try:
            return await self._execute_with_session(call_tool_op)
        except Exception as e:
            raise ConnectionError(
                f"Failed to call tool '{tool_name}' on server '{self.server.name}'. Error: {e}"
            ) from e

    def get_log(self):
        """Get the log content"""
        if not hasattr(self, "log_file") or self.log_file is None:
            return ""
        self.log_file.seek(0)
        try:
            log = self.log_file.read()
        except Exception:
            log = ""
        return log


class MCPClientLocal(MCPClientBase):
    """Local stdio MCP client"""
    
    def __del__(self):
        if hasattr(self, "log_file") and self.log_file is not None:
            with suppress(Exception):
                self.log_file.close()
            self.log_file = None

    async def _create_stdio_transport(self, current_exit_stack: AsyncExitStack) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Connect to an MCP server, init client and save stdio/write streams"""
        server: MCPServerLocal = cast(MCPServerLocal, self.server)

        if not server.command:
            raise ValueError("Command not specified")
        if not which(server.command):
            raise ValueError(f"Command '{server.command}' not found")

        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=server.env,
            encoding=server.encoding,
            encoding_error_handler=server.encoding_error_handler,
        )
        
        import tempfile
        if not hasattr(self, "log_file") or self.log_file is None:
            self.log_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8")

        stdio_transport = await current_exit_stack.enter_async_context(
            stdio_client(server_params, errlog=self.log_file)
        )
        return stdio_transport


class MCPClientRemote(MCPClientBase):
    """Remote SSE MCP client"""
    
    async def _create_stdio_transport(self, current_exit_stack: AsyncExitStack) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Connect to an MCP server, init client and save stdio/write streams"""
        server: MCPServerRemote = cast(MCPServerRemote, self.server)
        stdio_transport = await current_exit_stack.enter_async_context(
            sse_client(
                url=server.url,
                headers=server.headers,
                timeout=server.init_timeout or 30,
                sse_read_timeout=server.tool_timeout or 60,
            )
        )
        return stdio_transport