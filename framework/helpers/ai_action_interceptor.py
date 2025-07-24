"""
AI Action Interceptor Middleware for Unified Action Visualization.

This module provides comprehensive action detection and interception for all major
AI providers including Claude Computer Use, OpenAI Operator, and Google AI models.
It captures desktop automation, browser interactions, and visual computer tasks
for real-time visualization and transparency.
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from framework.helpers.log import Log


class AIActionType(Enum):
    """Types of AI actions that can be intercepted."""

    COMPUTER_USE = "computer_use"
    BROWSER_AUTOMATION = "browser_automation"
    DESKTOP_INTERACTION = "desktop_interaction"
    VISUAL_COMPUTER_TASK = "visual_computer_task"
    SHELL_COMMAND = "shell_command"
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    SCREENSHOT = "screenshot"
    MOUSE_ACTION = "mouse_action"
    KEYBOARD_ACTION = "keyboard_action"
    WINDOW_OPERATION = "window_operation"


class AIProvider(Enum):
    """AI providers that can be intercepted."""

    ANTHROPIC_CLAUDE = "anthropic_claude"
    OPENAI_OPERATOR = "openai_operator"
    GOOGLE_AI = "google_ai"
    GARY_ZERO_NATIVE = "gary_zero_native"
    BROWSER_USE = "browser_use"
    KALI_SHELL = "kali_shell"


@dataclass
class AIAction:
    """Represents a single AI action for visualization."""

    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    provider: AIProvider = AIProvider.GARY_ZERO_NATIVE
    action_type: AIActionType = AIActionType.CODE_EXECUTION
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str = "default"
    agent_name: str = "Unknown Agent"
    status: str = "started"  # started, completed, failed, error
    execution_time: float | None = None
    result: dict[str, Any] | None = None
    ui_url: str | None = None
    screenshot_path: str | None = None


class ActionInterceptor:
    """Base class for action interceptors."""

    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.active = True
        self.action_handlers: list[Callable[[AIAction], None]] = []

    def add_handler(self, handler: Callable[[AIAction], None]):
        """Add an action handler."""
        self.action_handlers.append(handler)

    def remove_handler(self, handler: Callable[[AIAction], None]):
        """Remove an action handler."""
        if handler in self.action_handlers:
            self.action_handlers.remove(handler)

    async def intercept_action(self, action: AIAction):
        """Intercept and process an action."""
        if not self.active:
            return

        # Notify all handlers
        for handler in self.action_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(action)
                else:
                    handler(action)
            except Exception as e:
                Log.log().error(f"Action handler error: {e}")


class ClaudeComputerUseInterceptor(ActionInterceptor):
    """Interceptor for Anthropic Claude Computer Use actions."""

    def __init__(self):
        super().__init__(AIProvider.ANTHROPIC_CLAUDE)
        self.original_methods = {}

    def hook_into_computer_use(self):
        """Hook into Claude Computer Use API calls."""
        try:
            # Try to import and hook into computer use tools
            from framework.tools.anthropic_computer_use import AnthropicComputerUse

            # Store original execute method
            if not hasattr(AnthropicComputerUse, "_original_execute"):
                AnthropicComputerUse._original_execute = AnthropicComputerUse.execute

                # Replace with intercepted version
                async def intercepted_execute(self, **kwargs):
                    action = AIAction(
                        provider=AIProvider.ANTHROPIC_CLAUDE,
                        action_type=self._map_action_type(
                            kwargs.get("action", "screenshot")
                        ),
                        description=f"Claude Computer Use: {kwargs.get('action', 'screenshot')}",
                        parameters=kwargs,
                        agent_name="Claude Computer Use Agent",
                    )

                    # Notify interceptor
                    await self.intercept_action(action)

                    # Execute original method
                    start_time = time.time()
                    try:
                        result = await AnthropicComputerUse._original_execute(
                            self, **kwargs
                        )
                        action.status = "completed"
                        action.execution_time = time.time() - start_time
                        action.result = {
                            "message": result.message
                            if hasattr(result, "message")
                            else str(result)
                        }
                    except Exception as e:
                        action.status = "error"
                        action.execution_time = time.time() - start_time
                        action.result = {"error": str(e)}
                        raise
                    finally:
                        # Notify completion
                        await self.intercept_action(action)

                    return result

                # Bind the intercepted method
                import types

                AnthropicComputerUse.execute = intercepted_execute

        except ImportError:
            Log.log().warning("Claude Computer Use tool not available for interception")

    def _map_action_type(self, action: str) -> AIActionType:
        """Map Claude action types to standard action types."""
        mapping = {
            "screenshot": AIActionType.SCREENSHOT,
            "click": AIActionType.MOUSE_ACTION,
            "type": AIActionType.KEYBOARD_ACTION,
            "key": AIActionType.KEYBOARD_ACTION,
            "move": AIActionType.MOUSE_ACTION,
            "scroll": AIActionType.MOUSE_ACTION,
        }
        return mapping.get(action, AIActionType.COMPUTER_USE)


class OpenAIOperatorInterceptor(ActionInterceptor):
    """Interceptor for OpenAI Operator actions."""

    def __init__(self):
        super().__init__(AIProvider.OPENAI_OPERATOR)

    def hook_into_operator(self):
        """Hook into OpenAI Operator API calls."""
        # TODO: Implement when OpenAI Operator integration is available
        Log.log().info("OpenAI Operator interceptor ready for integration")


class GoogleAIInterceptor(ActionInterceptor):
    """Interceptor for Google AI model actions."""

    def __init__(self):
        super().__init__(AIProvider.GOOGLE_AI)

    def hook_into_google_ai(self):
        """Hook into Google AI API calls."""
        # TODO: Implement when Google AI integration is available
        Log.log().info("Google AI interceptor ready for integration")


class BrowserUseInterceptor(ActionInterceptor):
    """Interceptor for browser automation actions."""

    def __init__(self):
        super().__init__(AIProvider.BROWSER_USE)

    def hook_into_browser_tools(self):
        """Hook into browser automation tools."""
        try:
            # Hook into existing browser tools
            from framework.tools import browser_agent, browser_do, browser_open

            # Hook browser_agent if available
            if hasattr(browser_agent, "BrowserAgentTool"):
                self._hook_browser_tool(browser_agent.BrowserAgentTool, "Browser Agent")

        except ImportError:
            Log.log().warning("Browser tools not available for interception")

    def _hook_browser_tool(self, tool_class, tool_name: str):
        """Hook a browser tool class."""
        if not hasattr(tool_class, "_original_execute"):
            tool_class._original_execute = tool_class.execute

            async def intercepted_execute(self, **kwargs):
                action = AIAction(
                    provider=AIProvider.BROWSER_USE,
                    action_type=AIActionType.BROWSER_AUTOMATION,
                    description=f"{tool_name}: {kwargs.get('action', 'browser operation')}",
                    parameters=kwargs,
                    agent_name=f"{tool_name} Agent",
                )

                await self.intercept_action(action)

                start_time = time.time()
                try:
                    result = await tool_class._original_execute(self, **kwargs)
                    action.status = "completed"
                    action.execution_time = time.time() - start_time
                    action.result = {"result": str(result)}
                except Exception as e:
                    action.status = "error"
                    action.execution_time = time.time() - start_time
                    action.result = {"error": str(e)}
                    raise
                finally:
                    await self.intercept_action(action)

                return result

            tool_class.execute = intercepted_execute


class KaliShellInterceptor(ActionInterceptor):
    """Interceptor for Kali shell actions (extends existing)."""

    def __init__(self):
        super().__init__(AIProvider.KALI_SHELL)

    def hook_into_shell_tools(self):
        """Hook into shell execution tools."""
        try:
            from framework.tools.shell_execute import ShellExecuteTool

            if not hasattr(ShellExecuteTool, "_original_call"):
                ShellExecuteTool._original_call = ShellExecuteTool.call

                async def intercepted_call(self, agent=None, **kwargs):
                    action = AIAction(
                        provider=AIProvider.KALI_SHELL,
                        action_type=AIActionType.SHELL_COMMAND,
                        description=f"Shell Command: {kwargs.get('command', 'unknown')}",
                        parameters=kwargs,
                        agent_name="Kali Shell Agent",
                        session_id=kwargs.get("session_id", "default"),
                    )

                    await self.intercept_action(action)

                    start_time = time.time()
                    try:
                        result = await ShellExecuteTool._original_call(
                            self, agent, **kwargs
                        )
                        action.status = (
                            "completed" if result.get("success") else "failed"
                        )
                        action.execution_time = time.time() - start_time
                        action.result = result
                        action.ui_url = result.get("ui_url")
                    except Exception as e:
                        action.status = "error"
                        action.execution_time = time.time() - start_time
                        action.result = {"error": str(e)}
                        raise
                    finally:
                        await self.intercept_action(action)

                    return result

                import types

                ShellExecuteTool.call = intercepted_call

        except ImportError:
            Log.log().warning("Shell tools not available for interception")


class AIActionInterceptorManager:
    """Central manager for all AI action interceptors."""

    def __init__(self):
        self.interceptors: dict[AIProvider, ActionInterceptor] = {}
        self.action_handlers: list[Callable[[AIAction], None]] = []
        self.action_history: list[AIAction] = []
        self.max_history_size = 1000
        self.active = False

        # Initialize interceptors
        self._initialize_interceptors()

    def _initialize_interceptors(self):
        """Initialize all available interceptors."""
        interceptors = [
            ClaudeComputerUseInterceptor(),
            OpenAIOperatorInterceptor(),
            GoogleAIInterceptor(),
            BrowserUseInterceptor(),
            KaliShellInterceptor(),
        ]

        for interceptor in interceptors:
            self.interceptors[interceptor.provider] = interceptor
            interceptor.add_handler(self._handle_action)

    def start_interception(self):
        """Start intercepting AI actions."""
        if self.active:
            return

        Log.log().info("🎯 Starting AI Action Interception")

        # Hook into all providers
        for provider, interceptor in self.interceptors.items():
            try:
                if provider == AIProvider.ANTHROPIC_CLAUDE:
                    interceptor.hook_into_computer_use()
                elif provider == AIProvider.BROWSER_USE:
                    interceptor.hook_into_browser_tools()
                elif provider == AIProvider.KALI_SHELL:
                    interceptor.hook_into_shell_tools()
                elif provider == AIProvider.OPENAI_OPERATOR:
                    interceptor.hook_into_operator()
                elif provider == AIProvider.GOOGLE_AI:
                    interceptor.hook_into_google_ai()

                Log.log().info(f"✅ Hooked into {provider.value}")
            except Exception as e:
                Log.log().warning(f"⚠️ Failed to hook into {provider.value}: {e}")

        self.active = True
        Log.log().info("🎯 AI Action Interception active")

    def stop_interception(self):
        """Stop intercepting AI actions."""
        self.active = False
        Log.log().info("🛑 AI Action Interception stopped")

    def add_action_handler(self, handler: Callable[[AIAction], None]):
        """Add a global action handler."""
        self.action_handlers.append(handler)

    def remove_action_handler(self, handler: Callable[[AIAction], None]):
        """Remove a global action handler."""
        if handler in self.action_handlers:
            self.action_handlers.remove(handler)

    async def _handle_action(self, action: AIAction):
        """Handle intercepted actions."""
        if not self.active:
            return

        # Add to history
        self.action_history.append(action)
        if len(self.action_history) > self.max_history_size:
            self.action_history.pop(0)

        # Notify handlers
        for handler in self.action_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(action)
                else:
                    handler(action)
            except Exception as e:
                Log.log().error(f"Action handler error: {e}")

    def get_recent_actions(self, limit: int = 50) -> list[AIAction]:
        """Get recent actions."""
        return self.action_history[-limit:]

    def get_actions_by_provider(
        self, provider: AIProvider, limit: int = 50
    ) -> list[AIAction]:
        """Get actions by provider."""
        provider_actions = [a for a in self.action_history if a.provider == provider]
        return provider_actions[-limit:]

    def get_actions_by_type(
        self, action_type: AIActionType, limit: int = 50
    ) -> list[AIAction]:
        """Get actions by type."""
        type_actions = [a for a in self.action_history if a.action_type == action_type]
        return type_actions[-limit:]


# Global interceptor manager instance
_ai_action_manager = None


def get_ai_action_manager() -> AIActionInterceptorManager:
    """Get the global AI action interceptor manager."""
    global _ai_action_manager
    if _ai_action_manager is None:
        _ai_action_manager = AIActionInterceptorManager()
    return _ai_action_manager


def start_ai_action_interception():
    """Start global AI action interception."""
    manager = get_ai_action_manager()
    manager.start_interception()


def stop_ai_action_interception():
    """Stop global AI action interception."""
    manager = get_ai_action_manager()
    manager.stop_interception()
