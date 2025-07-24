"""Simplified base classes for plugins to avoid heavy dependencies."""

from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class Response:
    """Simple response class for plugins."""

    message: str
    break_loop: bool = False


class PluginTool:
    """Simplified base class for plugin tools."""

    def __init__(
        self, agent, name: str, method: str | None, args: dict, message: str, **kwargs
    ):
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.message = message

    @abstractmethod
    async def execute(self, **kwargs) -> Response:
        """Execute the plugin tool."""
        pass

    async def before_execution(self, **kwargs):
        """Called before execution."""
        print(f"Using plugin tool '{self.name}'")

    async def after_execution(self, response: Response, **kwargs):
        """Called after execution."""
        print(f"Plugin tool '{self.name}' completed")
