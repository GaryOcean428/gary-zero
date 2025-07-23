"""
Logging hooks for integrating with core components.

This module provides decorators and context managers to automatically
add logging to critical system components.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from .unified_logger import EventType, LogEvent, LogLevel, get_unified_logger


class LoggingHooks:
    """Provides hooks for automatic logging integration."""

    def __init__(self, logger=None):
        self.logger = logger or get_unified_logger()

    def log_tool_execution(self,
                          tool_name: str | None = None,
                          user_id: str | None = None,
                          agent_id: str | None = None):
        """Decorator to automatically log tool execution."""
        def decorator(func: Callable) -> Callable:
            actual_tool_name = tool_name or func.__name__

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = False
                    error_message = None
                    output_data = None

                    try:
                        result = await func(*args, **kwargs)
                        success = True
                        output_data = {"result_type": str(type(result).__name__)}
                        return result
                    except Exception as e:
                        error_message = str(e)
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        await self.logger.log_tool_execution(
                            tool_name=actual_tool_name,
                            parameters={"args_count": len(args), "kwargs": list(kwargs.keys())},
                            success=success,
                            duration_ms=duration_ms,
                            user_id=user_id,
                            agent_id=agent_id,
                            output_data=output_data,
                            error_message=error_message
                        )

                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = False
                    error_message = None
                    output_data = None

                    try:
                        result = func(*args, **kwargs)
                        success = True
                        output_data = {"result_type": str(type(result).__name__)}
                        return result
                    except Exception as e:
                        error_message = str(e)
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        # Use asyncio to run the async log method
                        asyncio.create_task(self.logger.log_tool_execution(
                            tool_name=actual_tool_name,
                            parameters={"args_count": len(args), "kwargs": list(kwargs.keys())},
                            success=success,
                            duration_ms=duration_ms,
                            user_id=user_id,
                            agent_id=agent_id,
                            output_data=output_data,
                            error_message=error_message
                        ))

                return sync_wrapper

        return decorator

    def log_code_execution(self,
                          language: str = "python",
                          user_id: str | None = None,
                          agent_id: str | None = None):
        """Decorator to automatically log code execution."""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = False
                    error_message = None
                    output = None
                    code_snippet = ""

                    # Try to extract code from arguments
                    if args and isinstance(args[0], str):
                        code_snippet = args[0]
                    elif 'code' in kwargs:
                        code_snippet = kwargs['code']

                    try:
                        result = await func(*args, **kwargs)
                        success = True
                        output = str(result)[:500] if result else None
                        return result
                    except Exception as e:
                        error_message = str(e)
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        event_id = await self.logger.log_code_execution(
                            code_snippet=code_snippet,
                            language=language,
                            success=success,
                            duration_ms=duration_ms,
                            output=output,
                            error_message=error_message,
                            user_id=user_id,
                            agent_id=agent_id
                        )

                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = False
                    error_message = None
                    output = None
                    code_snippet = ""

                    # Try to extract code from arguments
                    if args and isinstance(args[0], str):
                        code_snippet = args[0]
                    elif 'code' in kwargs:
                        code_snippet = kwargs['code']

                    try:
                        result = func(*args, **kwargs)
                        success = True
                        output = str(result)[:500] if result else None
                        return result
                    except Exception as e:
                        error_message = str(e)
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        asyncio.create_task(self.logger.log_code_execution(
                            code_snippet=code_snippet,
                            language=language,
                            success=success,
                            duration_ms=duration_ms,
                            output=output,
                            error_message=error_message,
                            user_id=user_id,
                            agent_id=agent_id
                        ))

                return sync_wrapper

        return decorator

    @asynccontextmanager
    async def log_operation(self,
                           operation_type: str,
                           event_type: EventType = EventType.SYSTEM_EVENT,
                           user_id: str | None = None,
                           agent_id: str | None = None,
                           metadata: dict[str, Any] | None = None):
        """Context manager to log arbitrary operations."""
        start_time = time.time()
        success = False
        error_message = None

        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            event = LogEvent(
                event_type=event_type,
                level=LogLevel.INFO if success else LogLevel.ERROR,
                message=f"Operation {operation_type} {'completed' if success else 'failed'}",
                user_id=user_id,
                agent_id=agent_id,
                duration_ms=duration_ms,
                error_message=error_message,
                metadata={
                    "operation_type": operation_type,
                    "success": success,
                    **(metadata or {})
                }
            )

            await self.logger.log_event(event)


# Global hooks instance
_logging_hooks = None


def get_logging_hooks() -> LoggingHooks:
    """Get the global logging hooks instance."""
    global _logging_hooks
    if _logging_hooks is None:
        _logging_hooks = LoggingHooks()
    return _logging_hooks


# Convenience decorators using global hooks
def log_tool_execution(tool_name: str | None = None,
                      user_id: str | None = None,
                      agent_id: str | None = None):
    """Convenience decorator for tool execution logging."""
    return get_logging_hooks().log_tool_execution(tool_name, user_id, agent_id)


def log_code_execution(language: str = "python",
                      user_id: str | None = None,
                      agent_id: str | None = None):
    """Convenience decorator for code execution logging."""
    return get_logging_hooks().log_code_execution(language, user_id, agent_id)


def log_operation(operation_type: str,
                 event_type: EventType = EventType.SYSTEM_EVENT,
                 user_id: str | None = None,
                 agent_id: str | None = None,
                 metadata: dict[str, Any] | None = None):
    """Convenience context manager for operation logging."""
    return get_logging_hooks().log_operation(operation_type, event_type, user_id, agent_id, metadata)
