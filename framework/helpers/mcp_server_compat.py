"""
Gary-Zero MCP Server Integration
===============================

This module provides backward compatibility for gary-zero while using the shared MCP library.
"""

import os
from urllib.parse import urlparse

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from agent import AgentContext, AgentContextType, UserMessage
from framework.helpers import settings
from framework.helpers.persist_chat import remove_chat
from framework.helpers.print_style import PrintStyle
from initialize import initialize_agent
from shared_mcp.server import DynamicMcpProxy, SharedMCPServer
from shared_mcp.types import ToolError, ToolResponse

_PRINTER = PrintStyle(italic=True, font_color="green", padding=False)

# Create shared server instance
shared_mcp_server = SharedMCPServer(
    app_name="Gary-Zero",
    instructions="""
    Connect to remote Gary-Zero instance.
    Gary-Zero is a general AI assistant controlling it's linux environment.
    Gary-Zero can install software, manage files, execute commands, code, use internet, etc.
    Gary-Zero's environment is isolated unless configured otherwise.
    """
)

# For backward compatibility, expose the FastMCP instance as mcp_server
mcp_server = shared_mcp_server.get_fastmcp_instance()


async def _send_message_handler(message: str, attachments: list[str] | None = None,
                               chat_id: str | None = None, persistent_chat: bool | None = None) -> ToolResponse | ToolError:
    """Message handler implementation for the shared server"""
    context: AgentContext | None = None
    if chat_id:
        context = AgentContext.get(chat_id)
        if not context:
            return ToolError(error="Chat not found", chat_id=chat_id)
        else:
            persistent_chat = True
    else:
        config = initialize_agent()
        context = AgentContext(config=config, type=AgentContextType.MCP)

    if not message:
        return ToolError(error="Message is required", chat_id=context.id if persistent_chat else "")

    try:
        response = await _run_chat(context, message, attachments)
        if not persistent_chat:
            context.reset()
            AgentContext.remove(context.id)
            remove_chat(context.id)
        return ToolResponse(response=response, chat_id=context.id if persistent_chat else "")
    except Exception as e:
        return ToolError(error=str(e), chat_id=context.id if persistent_chat else "")


async def _finish_chat_handler(chat_id: str) -> ToolResponse | ToolError:
    """Finish chat handler implementation for the shared server"""
    if not chat_id:
        return ToolError(error="Chat ID is required", chat_id="")

    context = AgentContext.get(chat_id)
    if not context:
        return ToolError(error="Chat not found", chat_id=chat_id)
    else:
        context.reset()
        AgentContext.remove(context.id)
        remove_chat(context.id)
        return ToolResponse(response="Chat finished", chat_id=chat_id)


async def _run_chat(context: AgentContext, message: str, attachments: list[str] | None = None):
    """Run chat implementation (unchanged from original)"""
    try:
        _PRINTER.print("MCP Chat message received")

        # Process attachment filenames for logging
        attachment_filenames = []
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    attachment_filenames.append(attachment)
                else:
                    try:
                        url = urlparse(attachment)
                        if url.scheme in ["http", "https", "ftp", "ftps", "sftp"]:
                            attachment_filenames.append(attachment)
                        else:
                            _PRINTER.print(
                                f"Skipping attachment (unsupported scheme): [{attachment}]"
                            )
                    except (ValueError, AttributeError) as e:
                        _PRINTER.print(f"Skipping malformed attachment URL [{attachment}]: {e}")

        _PRINTER.print("User message:")
        _PRINTER.print(f"> {message}")
        if attachment_filenames:
            _PRINTER.print("Attachments:")
            for filename in attachment_filenames:
                _PRINTER.print(f"- {filename}")

        task = context.communicate(
            UserMessage(message=message, system_message=[], attachments=attachment_filenames)
        )
        result = await task.result()

        # Success
        _PRINTER.print(f"MCP Chat message completed: {result}")

        return result

    except (RuntimeError, ValueError, AttributeError, ConnectionError) as e:
        # Specific errors we expect from chat operations
        error_msg = f"Failed to process chat message: {e}"
        _PRINTER.print(f"MCP Chat message failed: {error_msg}")
        raise RuntimeError(error_msg) from e
    except Exception as e:
        # Catch-all for unexpected errors with more context
        error_msg = f"Unexpected error processing chat message: {e}"
        _PRINTER.print(f"MCP Chat message failed: {error_msg}")
        raise RuntimeError(error_msg) from e


# Register handlers with the shared server
shared_mcp_server.register_message_handler(_send_message_handler)
shared_mcp_server.register_finish_chat_handler(_finish_chat_handler)


class DynamicMcpProxy(DynamicMcpProxy):
    """Backward compatible dynamic proxy"""

    def __init__(self):
        cfg = settings.get_settings()
        super().__init__(token_provider=lambda: cfg["mcp_server_token"])
        self.reconfigure(shared_mcp_server, cfg["mcp_server_token"])

    def reconfigure(self, token: str):
        """Reconfigure with new token (backward compatibility)"""
        super().reconfigure(shared_mcp_server, token)


async def mcp_middleware(request: Request, call_next):
    """MCP middleware (unchanged from original)"""
    # check if MCP server is enabled
    cfg = settings.get_settings()
    if not cfg["mcp_server_enabled"]:
        PrintStyle.error("[MCP] Access denied: MCP server is disabled in settings.")
        raise StarletteHTTPException(status_code=403, detail="MCP server is disabled in settings.")

    return await call_next(request)
