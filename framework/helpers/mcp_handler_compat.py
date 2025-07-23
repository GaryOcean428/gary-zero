"""
Gary-Zero MCP Handler Integration
===============================

This module provides backward compatibility for gary-zero MCP client functionality
while using the shared MCP library.
"""

import json
from typing import Any

from framework.helpers import dirty_json, settings
from framework.helpers.print_style import PrintStyle
from framework.helpers.tool import Response, Tool
from shared_mcp.client import SharedMCPClient


def initialize_mcp(mcp_servers_config: str):
    """Initialize MCP with configuration string (backward compatibility)"""
    if not MCPConfig.get_instance().is_initialized():
        try:
            MCPConfig.update(mcp_servers_config)
        except Exception as e:
            from agent import AgentContext

            AgentContext.log_to_all(
                type="warning",
                content=f"Failed to update MCP settings: {e}",
                temp=False,
            )

            PrintStyle(background_color="black", font_color="red", padding=True).print(
                f"Failed to update MCP settings: {e}"
            )


class MCPTool(Tool):
    """MCP Tool wrapper (backward compatibility)"""

    async def execute(self, **kwargs: Any):
        error = ""
        try:
            client = MCPConfig.get_instance().get_shared_client()
            response = await client.call_tool(self.name, kwargs)
            message = "\n\n".join([item.text for item in response.content if item.type == "text"])
            if response.isError:
                error = message
        except Exception as e:
            error = f"MCP Tool Exception: {str(e)}"
            message = f"ERROR: {str(e)}"

        if error:
            PrintStyle(
                background_color="#CC34C3", font_color="white", bold=True, padding=True
            ).print(f"MCPTool::Failed to call mcp tool {self.name}:")
            PrintStyle(background_color="#AA4455", font_color="white", padding=False).print(error)

            self.agent.context.log.log(
                type="warning",
                content=f"{self.name}: {error}",
            )

        return Response(message=message, break_loop=False)

    async def before_execution(self, **kwargs: Any):
        PrintStyle(
            font_color="#1B4F72", padding=True, background_color="white", bold=True
        ).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
        self.log = self.get_log_object()

        for key, value in self.args.items():
            PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key) + ": ")
            PrintStyle(
                font_color="#85C1E9", padding=isinstance(value, str) and "\n" in value
            ).stream(value)
            PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs: Any):
        raw_tool_response = response.message.strip() if response.message else ""
        if not raw_tool_response:
            PrintStyle(font_color="red").print(
                f"Warning: Tool '{self.name}' returned an empty message."
            )
            raw_tool_response = "[Tool returned no textual content]"

        # Prepare user message context
        user_message_text = "No specific user message context available for this exact step."
        if self.agent and self.agent.last_user_message and self.agent.last_user_message.content:
            content = self.agent.last_user_message.content
            if isinstance(content, dict):
                user_message_text = content.get("message", json.dumps(content, indent=2))
            elif isinstance(content, str):
                user_message_text = content
            else:
                user_message_text = str(content)

        user_message_text = str(user_message_text)

        # Truncate user message context if it's too long
        max_user_context_len = 500
        if len(user_message_text) > max_user_context_len:
            user_message_text = user_message_text[:max_user_context_len] + "... (truncated)"

        final_text_for_agent = raw_tool_response

        self.agent.hist_add_tool_result(self.name, final_text_for_agent)
        PrintStyle(
            font_color="#1B4F72", background_color="white", padding=True, bold=True
        ).print(
            f"{self.agent.agent_name}: Response from tool '{self.name}' (plus context added)"
        )
        PrintStyle(font_color="#85C1E9").print(
            raw_tool_response if raw_tool_response else "[No direct textual output from tool]"
        )
        if self.log:
            self.log.update(content=final_text_for_agent)


class MCPConfig:
    """MCP Configuration (backward compatibility wrapper)"""

    _instance = None
    _initialized = False

    def __init__(self):
        self.shared_client = SharedMCPClient(self._settings_provider)

    @staticmethod
    def _settings_provider():
        """Provide settings for the shared client"""
        cfg = settings.get_settings()
        return {
            "mcp_client_init_timeout": cfg.get("mcp_client_init_timeout", 30),
            "mcp_client_tool_timeout": cfg.get("mcp_client_tool_timeout", 60)
        }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def update(cls, config_str: str):
        """Update configuration from string"""
        instance = cls.get_instance()

        servers_data = []
        if config_str and config_str.strip():
            try:
                parsed_value = dirty_json.try_parse(config_str)
                normalized = cls.normalize_config(parsed_value)

                if isinstance(normalized, list):
                    valid_servers = []
                    for item in normalized:
                        if isinstance(item, dict):
                            valid_servers.append(item)
                        else:
                            PrintStyle(
                                background_color="yellow",
                                font_color="black",
                                padding=True,
                            ).print(
                                f"Warning: MCP config item was not a dictionary and was ignored: {item}"
                            )
                    servers_data = valid_servers
                else:
                    PrintStyle(background_color="red", font_color="white", padding=True).print(
                        f"Error: Parsed MCP config top-level structure is not a list. Config string: '{config_str}'"
                    )
            except Exception as e:
                PrintStyle.error(
                    f"Error parsing MCP config string: {e}. Config string: '{config_str}'"
                )

        # Update the shared client
        import asyncio
        asyncio.run(instance.shared_client.connect_to_servers(servers_data))
        cls._initialized = True
        return instance

    @classmethod
    def normalize_config(cls, servers):
        """Normalize configuration format"""
        normalized = []
        if isinstance(servers, list):
            for server in servers:
                if isinstance(server, dict):
                    normalized.append(server)
        elif isinstance(servers, dict):
            if "mcpServers" in servers:
                if isinstance(servers["mcpServers"], dict):
                    for key, value in servers["mcpServers"].items():
                        if isinstance(value, dict):
                            value["name"] = key
                            normalized.append(value)
                elif isinstance(servers["mcpServers"], list):
                    for server in servers["mcpServers"]:
                        if isinstance(server, dict):
                            normalized.append(server)
            else:
                normalized.append(servers)
        return normalized

    def is_initialized(self) -> bool:
        """Check if initialized"""
        return self._initialized

    def get_shared_client(self) -> SharedMCPClient:
        """Get the shared client instance"""
        return self.shared_client

    def get_servers_status(self) -> list[dict[str, Any]]:
        """Get servers status"""
        return self.shared_client.get_servers_status()

    def get_server_detail(self, server_name: str) -> dict[str, Any]:
        """Get server details"""
        status_list = self.get_servers_status()
        for status in status_list:
            if status["name"] == server_name:
                tools = []
                try:
                    all_tools = self.shared_client.get_tools()
                    for tool_dict in all_tools:
                        for tool_name, tool_info in tool_dict.items():
                            if tool_info.get("server") == server_name:
                                tools.append({
                                    "name": tool_info["name"],
                                    "description": tool_info["description"],
                                    "input_schema": tool_info.get("input_schema", {})
                                })
                except Exception:
                    tools = []

                return {
                    "name": server_name,
                    "description": status.get("description", ""),
                    "tools": tools,
                }
        return {}

    def get_server_log(self, server_name: str) -> str:
        """Get server log (placeholder)"""
        return ""

    def get_tools(self) -> list[dict[str, dict[str, Any]]]:
        """Get all tools"""
        return self.shared_client.get_tools()

    def get_tools_prompt(self, server_name: str = "") -> str:
        """Get tools prompt"""
        return self.shared_client.get_tools_prompt(server_name)

    def has_tool(self, tool_name: str) -> bool:
        """Check if tool exists"""
        return self.shared_client.has_tool(tool_name)

    def get_tool(self, agent: Any, tool_name: str) -> MCPTool | None:
        """Get tool instance"""
        if not self.has_tool(tool_name):
            return None
        return MCPTool(agent=agent, name=tool_name, method=None, args={}, message="")

    async def call_tool(self, tool_name: str, input_data: dict[str, Any]):
        """Call a tool"""
        return await self.shared_client.call_tool(tool_name, input_data)
