from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.mcp_handler import MCPConfig


class McpServersStatus(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:

        # try:
        status = MCPConfig.get_instance().get_servers_status()
        return {"success": True, "status": status}

    # except Exception as e:
    #     return {"success": False, "error": str(e)}
