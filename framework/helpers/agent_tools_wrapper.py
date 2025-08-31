"""AgentTools wrapper for Gary-Zero tools to work with OpenAI Agents SDK.

This module wraps existing Gary-Zero tools to be compatible with the OpenAI
Agents SDK tool interface, enabling seamless integration while maintaining
backward compatibility.
"""

import asyncio
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

# OpenAI Agents SDK imports
from agents import Tool as SDKTool

from framework.helpers.extract_tools import load_classes_from_folder
from framework.helpers.print_style import PrintStyle

# Gary-Zero imports
from framework.helpers.tool import Tool as GaryTool

# Forward reference imports
if TYPE_CHECKING:
    from agent import Agent


@dataclass
class ToolExecutionResult:
    """Result of tool execution with SDK compatibility."""

    success: bool
    result: Any
    error: str | None = None
    metadata: dict[str, Any] = None
    break_loop: bool = False

    def to_sdk_result(self) -> Any:
        """Convert to SDK-compatible result format."""
        if self.success:
            return self.result
        else:
            raise Exception(self.error or "Unknown error")


class SDKToolWrapper(SDKTool):
    """Wrapper to make Gary-Zero tools compatible with OpenAI Agents SDK."""

    def __init__(self, gary_tool_class: type[GaryTool], agent: "Agent"):
        self.gary_tool_class = gary_tool_class
        self.agent = agent
        self._tool_instance = None

        # Extract tool metadata
        self.tool_name = self._get_tool_name()
        self.tool_description = self._get_tool_description()
        self.tool_parameters = self._get_tool_parameters()

        super().__init__(
            name=self.tool_name,
            description=self.tool_description,
            parameters=self.tool_parameters,
        )

    def _get_tool_name(self) -> str:
        """Extract tool name from Gary-Zero tool class."""
        # Use class name or look for name attribute
        if hasattr(self.gary_tool_class, "name"):
            return self.gary_tool_class.name
        else:
            # Convert class name to snake_case
            name = self.gary_tool_class.__name__
            return "".join(
                ["_" + i.lower() if i.isupper() else i for i in name]
            ).lstrip("_")

    def _get_tool_description(self) -> str:
        """Extract tool description from Gary-Zero tool class."""
        if hasattr(self.gary_tool_class, "description"):
            return self.gary_tool_class.description
        elif self.gary_tool_class.__doc__:
            return self.gary_tool_class.__doc__.strip()
        else:
            return f"Tool: {self.tool_name}"

    def _get_tool_parameters(self) -> dict[str, Any]:
        """Extract tool parameters from Gary-Zero tool class."""
        parameters = {"type": "object", "properties": {}, "required": []}

        # Try to extract from execute method signature
        if hasattr(self.gary_tool_class, "execute"):
            sig = inspect.signature(self.gary_tool_class.execute)
            for param_name, param in sig.parameters.items():
                if param_name in ["self", "kwargs"]:
                    continue

                prop = {"type": "string"}  # Default type

                # Try to infer type from annotation
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        prop["type"] = "integer"
                    elif param.annotation == float:
                        prop["type"] = "number"
                    elif param.annotation == bool:
                        prop["type"] = "boolean"
                    elif param.annotation == list:
                        prop["type"] = "array"
                    elif param.annotation == dict:
                        prop["type"] = "object"

                # Add description if available
                if hasattr(param, "description"):
                    prop["description"] = param.description

                parameters["properties"][param_name] = prop

                # Mark as required if no default value
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

        return parameters

    async def execute(self, **kwargs) -> Any:
        """Execute the wrapped Gary-Zero tool."""
        try:
            # Create tool instance if not exists
            if self._tool_instance is None:
                self._tool_instance = self.gary_tool_class(
                    agent=self.agent,
                    name=self.tool_name,
                    method=None,
                    args=kwargs,
                    message="",
                )

            # Update args for this execution
            self._tool_instance.args = kwargs

            # Execute before_execution hook
            await self._tool_instance.before_execution(**kwargs)

            # Execute the tool
            gary_result = await self._tool_instance.execute(**kwargs)

            # Execute after_execution hook
            await self._tool_instance.after_execution(gary_result)

            # Convert Gary-Zero result to SDK format
            if hasattr(gary_result, "message"):
                # Gary-Zero tool result format
                result = ToolExecutionResult(
                    success=True,
                    result=gary_result.message,
                    break_loop=gary_result.break_loop,
                    metadata={"gary_zero_tool": True},
                )
            else:
                # Direct result
                result = ToolExecutionResult(
                    success=True,
                    result=str(gary_result),
                    metadata={"gary_zero_tool": True},
                )

            return result.to_sdk_result()

        except Exception as e:
            error_result = ToolExecutionResult(
                success=False,
                error=str(e),
                metadata={"gary_zero_tool": True, "error_type": type(e).__name__},
            )
            raise Exception(error_result.error)


class ToolRegistry:
    """Registry for managing SDK-wrapped tools."""

    def __init__(self):
        self.registered_tools: dict[str, SDKToolWrapper] = {}
        self.tool_categories: dict[str, list[str]] = {}
        self.gary_tool_classes: dict[str, type[GaryTool]] = {}

    def discover_gary_tools(self) -> dict[str, type[GaryTool]]:
        """Discover all available Gary-Zero tools."""
        tool_classes = {}

        try:
            # Load tools from framework/tools directory
            classes = load_classes_from_folder("framework/tools", "*.py", GaryTool)

            for tool_class in classes:
                tool_name = tool_class.__name__.lower()
                tool_classes[tool_name] = tool_class

            PrintStyle(font_color="cyan", padding=True).print(
                f"Discovered {len(tool_classes)} Gary-Zero tools"
            )

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error discovering tools: {e}"
            )

        self.gary_tool_classes = tool_classes
        return tool_classes

    def register_tool(
        self, gary_tool_class: type[GaryTool], agent: "Agent", category: str = "general"
    ) -> str:
        """Register a Gary-Zero tool as SDK-compatible tool."""
        wrapper = SDKToolWrapper(gary_tool_class, agent)
        tool_name = wrapper.tool_name

        self.registered_tools[tool_name] = wrapper

        # Add to category
        if category not in self.tool_categories:
            self.tool_categories[category] = []
        self.tool_categories[category].append(tool_name)

        PrintStyle(font_color="green", padding=True).print(
            f"Registered SDK tool: {tool_name} (category: {category})"
        )

        return tool_name

    def register_all_tools(self, agent: "Agent") -> list[str]:
        """Register all discovered Gary-Zero tools."""
        if not self.gary_tool_classes:
            self.discover_gary_tools()

        registered_names = []

        for tool_name, tool_class in self.gary_tool_classes.items():
            try:
                # Categorize tools based on their module or class name
                category = self._categorize_tool(tool_class)
                registered_name = self.register_tool(tool_class, agent, category)
                registered_names.append(registered_name)
            except Exception as e:
                PrintStyle(font_color="yellow", padding=True).print(
                    f"Failed to register tool {tool_name}: {e}"
                )

        return registered_names

    def _categorize_tool(self, tool_class: type[GaryTool]) -> str:
        """Categorize a tool based on its characteristics."""
        class_name = tool_class.__name__.lower()
        module_name = tool_class.__module__.lower()

        # Code-related tools
        if any(
            keyword in class_name for keyword in ["code", "python", "execute", "script"]
        ):
            return "coding"

        # Browser/web tools
        elif any(
            keyword in class_name for keyword in ["browser", "web", "page", "click"]
        ):
            return "browser"

        # File system tools
        elif any(
            keyword in class_name for keyword in ["file", "directory", "read", "write"]
        ):
            return "filesystem"

        # Communication tools
        elif any(
            keyword in class_name
            for keyword in ["message", "email", "chat", "response"]
        ):
            return "communication"

        # Search tools
        elif any(keyword in class_name for keyword in ["search", "find", "query"]):
            return "search"

        # Analysis tools
        elif any(keyword in class_name for keyword in ["analyze", "process", "parse"]):
            return "analysis"

        else:
            return "general"

    def get_tool(self, tool_name: str) -> SDKToolWrapper | None:
        """Get a registered tool by name."""
        return self.registered_tools.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[SDKToolWrapper]:
        """Get all tools in a specific category."""
        tool_names = self.tool_categories.get(category, [])
        return [
            self.registered_tools[name]
            for name in tool_names
            if name in self.registered_tools
        ]

    def get_all_tools(self) -> list[SDKToolWrapper]:
        """Get all registered tools."""
        return list(self.registered_tools.values())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return {
            "name": tool.tool_name,
            "description": tool.tool_description,
            "parameters": tool.tool_parameters,
            "category": self._get_tool_category(tool_name),
            "gary_zero_class": tool.gary_tool_class.__name__,
        }

    def _get_tool_category(self, tool_name: str) -> str:
        """Get the category of a tool."""
        for category, tools in self.tool_categories.items():
            if tool_name in tools:
                return category
        return "unknown"

    def list_tools(self) -> dict[str, list[dict[str, Any]]]:
        """List all tools organized by category."""
        result = {}

        for category, tool_names in self.tool_categories.items():
            result[category] = []
            for tool_name in tool_names:
                tool_info = self.get_tool_info(tool_name)
                if tool_info:
                    result[category].append(tool_info)

        return result


class ToolExecutor:
    """Executor for SDK-wrapped tools with enhanced capabilities."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.execution_history: list[dict[str, Any]] = []

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolExecutionResult:
        """Execute a tool by name with arguments."""
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False, error=f"Tool '{tool_name}' not found"
            )

        execution_record = {
            "tool_name": tool_name,
            "args": kwargs,
            "timestamp": asyncio.get_event_loop().time(),
            "success": False,
            "result": None,
            "error": None,
        }

        try:
            # Execute through SDK wrapper
            sdk_result = await tool.execute(**kwargs)

            # Convert back to our format
            if hasattr(sdk_result, "error") and sdk_result.error:
                result = ToolExecutionResult(success=False, error=sdk_result.error)
            else:
                result = ToolExecutionResult(
                    success=True,
                    result=(
                        sdk_result.result
                        if hasattr(sdk_result, "result")
                        else str(sdk_result)
                    ),
                    metadata=getattr(sdk_result, "metadata", {}),
                )

            execution_record.update(
                {
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                }
            )

            return result

        except Exception as e:
            execution_record.update({"success": False, "error": str(e)})

            return ToolExecutionResult(success=False, error=str(e))

        finally:
            self.execution_history.append(execution_record)
            # Keep only recent executions
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

    async def execute_tool_chain(
        self, tool_chain: list[dict[str, Any]]
    ) -> list[ToolExecutionResult]:
        """Execute a chain of tools in sequence."""
        results = []

        for step in tool_chain:
            tool_name = step.get("tool")
            args = step.get("args", {})

            if not tool_name:
                results.append(
                    ToolExecutionResult(
                        success=False, error="No tool name specified in chain step"
                    )
                )
                continue

            result = await self.execute_tool(tool_name, **args)
            results.append(result)

            # Stop on first error if specified
            if not result.success and step.get("stop_on_error", False):
                break

        return results

    def get_execution_stats(self) -> dict[str, Any]:
        """Get statistics about tool executions."""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = len([e for e in self.execution_history if e["success"]])

        # Tool usage frequency
        tool_usage = {}
        for execution in self.execution_history:
            tool_name = execution["tool_name"]
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0,
            "tool_usage_frequency": tool_usage,
            "most_used_tool": (
                max(tool_usage.items(), key=lambda x: x[1])[0] if tool_usage else None
            ),
        }


# Global registry and executor
_tool_registry: ToolRegistry | None = None
_tool_executor: ToolExecutor | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor."""
    global _tool_executor
    if _tool_executor is None:
        registry = get_tool_registry()
        _tool_executor = ToolExecutor(registry)
    return _tool_executor


def initialize_tools(agent: "Agent") -> list[str]:
    """Initialize tools for SDK integration."""
    registry = get_tool_registry()

    # Discover and register all Gary-Zero tools
    registered_tools = registry.register_all_tools(agent)

    PrintStyle(font_color="green", padding=True).print(
        f"Initialized {len(registered_tools)} tools for SDK integration"
    )

    return registered_tools


def get_sdk_tools_for_agent(agent: "Agent") -> list[SDKTool]:
    """Get all SDK-compatible tools for an agent."""
    registry = get_tool_registry()

    # Ensure tools are registered
    if not registry.registered_tools:
        initialize_tools(agent)

    return registry.get_all_tools()


# Convenience functions for backward compatibility
def wrap_gary_tool(tool_class: type[GaryTool], agent: "Agent") -> SDKToolWrapper:
    """Convenience function to wrap a single Gary-Zero tool."""
    return SDKToolWrapper(tool_class, agent)


def execute_wrapped_tool(
    tool_name: str, agent: "Agent", **kwargs
) -> ToolExecutionResult:
    """Convenience function to execute a wrapped tool."""
    executor = get_tool_executor()
    return asyncio.run(executor.execute_tool(tool_name, **kwargs))
