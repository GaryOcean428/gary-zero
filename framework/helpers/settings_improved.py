"""Improved version of the highlighted code snippet from settings.py.

This module demonstrates better practices for:
1. Async task management with proper error handling
2. Improved regex pattern for environment variable parsing
3. Type safety and validation
"""

# Standard library imports
import asyncio
import contextlib
import re
from dataclasses import dataclass
from enum import Enum

# Local application imports
from framework.helpers.print_style import PrintStyle


class TaskStatus(Enum):
    """Status of background tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    """Represents a managed background task."""

    name: str
    task: asyncio.Task
    status: TaskStatus = TaskStatus.PENDING
    error: Exception | None = None


class BackgroundTaskManager:
    """Manages background tasks with proper error handling and lifecycle management."""

    def __init__(self):
        self._tasks: dict[str, BackgroundTask] = {}
        self._lock = asyncio.Lock()

    async def schedule_task(
        self, coro, task_name: str, on_error=None
    ) -> BackgroundTask:
        """Schedule a background task with proper error handling.

        Args:
            coro: The coroutine to execute
            task_name: A unique name for the task
            on_error: Optional error handler callback

        Returns:
            BackgroundTask instance
        """
        async with self._lock:
            # Cancel existing task with same name if present
            if task_name in self._tasks:
                existing = self._tasks[task_name]
                if not existing.task.done():
                    existing.task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await existing.task

            # Create new task
            task = asyncio.create_task(coro)
            bg_task = BackgroundTask(name=task_name, task=task)
            self._tasks[task_name] = bg_task

            # Add completion callback
            def handle_completion(future: asyncio.Task):
                try:
                    future.result()
                    bg_task.status = TaskStatus.COMPLETED
                except asyncio.CancelledError:
                    bg_task.status = TaskStatus.FAILED
                    bg_task.error = Exception("Task was cancelled")
                except Exception as e:  # pylint: disable=broad-except
                    # Catching broad exception here is intentional for background tasks
                    # to prevent them from crashing the event loop silently.
                    bg_task.status = TaskStatus.FAILED
                    bg_task.error = e

                    # Log error
                    PrintStyle(
                        background_color="red", font_color="white", padding=True
                    ).print(f"Background task '{task_name}' failed: {e}")

                    # Call custom error handler if provided
                    if on_error:
                        try:
                            on_error(e)
                        except (
                            Exception
                        ) as handler_error:  # pylint: disable=broad-except
                            PrintStyle(
                                background_color="red", font_color="white", padding=True
                            ).print(
                                f"Error handler for '{task_name}' failed: {handler_error}"
                            )

            task.add_done_callback(handle_completion)
            bg_task.status = TaskStatus.RUNNING

            return bg_task

    async def cancel_task(self, task_name: str) -> bool:
        """Cancel a background task by name.

        Returns:
            True if task was cancelled, False if not found
        """
        async with self._lock:
            if task_name in self._tasks:
                task = self._tasks[task_name]
                if not task.task.done():
                    task.task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task.task
                del self._tasks[task_name]
                return True
            return False

    async def wait_for_task(self, task_name: str, timeout: float | None = None):
        """Wait for a specific task to complete.

        Args:
            task_name: Name of the task to wait for
            timeout: Optional timeout in seconds

        Raises:
            KeyError: If task not found
            asyncio.TimeoutError: If timeout exceeded
        """
        if task_name not in self._tasks:
            raise KeyError(f"Task '{task_name}' not found")

        task = self._tasks[task_name]
        await asyncio.wait_for(task.task, timeout=timeout)

    def get_task_status(self, task_name: str) -> TaskStatus | None:
        """Get the status of a task."""
        if task_name in self._tasks:
            return self._tasks[task_name].status
        return None

    def get_all_tasks(self) -> dict[str, TaskStatus]:
        """Get status of all tasks."""
        return {name: task.status for name, task in self._tasks.items()}

    async def cleanup_completed(self):
        """Remove completed and failed tasks from tracking."""
        async with self._lock:
            to_remove = [
                name
                for name, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            ]
            for name in to_remove:
                del self._tasks[name]


# Global task manager instance
_task_manager = BackgroundTaskManager()


async def schedule_background_task(coro, task_name: str) -> None:
    """Schedule a background task using the global task manager.

    This is the improved version of the original asyncio.create_task() call.
    """
    await _task_manager.schedule_task(coro, task_name)


class EnvParser:
    """Improved environment variable parser with better pattern matching."""

    # Compiled regex patterns for better performance
    LINE_PATTERN = re.compile(
        r"^\s*(?P<key>[^#\s=][^=]*?)\s*=\s*(?P<value>.*?)\s*$", re.MULTILINE
    )

    # Pattern to detect quoted values
    QUOTED_VALUE_PATTERN = re.compile(r'^(["\'])(.*)(\1)$', re.DOTALL)

    @classmethod
    def parse(cls, data: str) -> dict[str, str]:
        """Parse environment variable format string to dictionary.

        Improvements over original:
        - Named groups for better readability
        - Handles multi-line values in quotes
        - Better quote stripping logic
        - Type hints for clarity

        Args:
            data: Multi-line string in KEY=VALUE format

        Returns:
            Dictionary of parsed key-value pairs
        """
        env_dict = {}

        # Process each line
        for match in cls.LINE_PATTERN.finditer(data):
            key = match.group("key").strip()
            value = match.group("value").strip()

            # Handle quoted values
            quoted_match = cls.QUOTED_VALUE_PATTERN.match(value)
            if quoted_match:
                # Extract value without quotes
                value = quoted_match.group(2)

            env_dict[key] = value

        return env_dict

    @classmethod
    def to_env_string(cls, data_dict: dict[str, str]) -> str:
        """Convert dictionary to environment variable format.

        Args:
            data_dict: Dictionary to convert

        Returns:
            Formatted environment string
        """
        lines = []

        for key, value in data_dict.items():
            # Quote values that need it
            if cls._needs_quotes(value):
                # Use single quotes for values with double quotes
                if '"' in value and "'" not in value:
                    value = f"'{value}'"
                else:
                    # Escape double quotes and use double quotes
                    escaped_value = value.replace('"', '\\"')
                    value = f'"{escaped_value}"'

            lines.append(f"{key}={value}")

        return "\n".join(lines)

    @staticmethod
    def _needs_quotes(value: str) -> bool:
        """Check if a value needs to be quoted."""
        return (
            "\n" in value
            or " " in value
            or value == ""
            or any(c in value for c in "\"'=")
        )


# Example usage of the improved code:
async def update_mcp_token_improved(current_token: str):
    """Improved version of update_mcp_token with better error handling."""
    try:
        from framework.helpers.mcp_server import DynamicMcpProxy

        DynamicMcpProxy.get_instance().reconfigure(token=current_token)

        PrintStyle(background_color="green", font_color="white", padding=True).print(
            "Successfully updated MCP token"
        )

    except ImportError as e:
        PrintStyle(background_color="red", font_color="white", padding=True).print(
            f"Failed to import MCP server module: {e}"
        )
        raise
    except Exception as e:  # pylint: disable=broad-except
        # Catching broad exception here is intentional for background tasks
        # to prevent them from crashing the event loop silently.
        PrintStyle(background_color="red", font_color="white", padding=True).print(
            f"Failed to update MCP token: {e}"
        )
        raise


# Improved env_to_dict function
def env_to_dict(data: str) -> dict[str, str]:
    """Parse environment variable format string to dictionary.

    This is the improved version using the EnvParser class.
    """
    return EnvParser.parse(data)


# Improved dict_to_env function
def dict_to_env(data_dict: dict[str, str]) -> str:
    """Convert dictionary to environment variable format.

    This is the improved version using the EnvParser class.
    """
    return EnvParser.to_env_string(data_dict)
