"""Simple test plugin with minimal dependencies."""

import json
from datetime import datetime

# Try to import the full Tool class, fallback to our simple base
try:
    from framework.helpers.tool import Response, Tool
    BaseClass = Tool
except ImportError:
    from framework.plugins.base import Response, PluginTool
    BaseClass = PluginTool


class SimpleTest(BaseClass):
    """Simple test plugin for demonstrating the plugin system."""

    async def execute(self, **kwargs) -> Response:
        """Execute the test plugin."""
        
        action = self.args.get("action", "info").lower()
        
        if action == "info":
            return await self._get_info()
        elif action == "echo":
            return await self._echo()
        elif action == "time":
            return await self._get_time()
        else:
            return Response(
                message=f"Unknown action: {action}. Available actions: info, echo, time",
                break_loop=False
            )

    async def _get_info(self) -> Response:
        """Get plugin information."""
        info = {
            "name": "Simple Test Plugin",
            "version": "1.0.0",
            "status": "operational",
            "capabilities": ["testing", "demo"]
        }
        
        return Response(
            message=f"📋 Plugin Information:\n{json.dumps(info, indent=2)}",
            break_loop=False
        )

    async def _echo(self) -> Response:
        """Echo back the provided message."""
        message = self.args.get("message", "Hello from plugin!")
        
        return Response(
            message=f"🔊 Echo: {message}",
            break_loop=False
        )

    async def _get_time(self) -> Response:
        """Get current time."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Response(
            message=f"🕒 Current time: {current_time}",
            break_loop=False
        )