"""Core interfaces for the Gary-Zero framework.

This module defines the abstract base classes and protocols that provide
clear contracts for framework components, enabling dependency injection
and proper separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Service(Protocol):
    """Protocol defining the interface for framework services."""

    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        ...

    async def shutdown(self) -> None:
        """Clean shutdown of the service."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        ...


@runtime_checkable
class Repository(Protocol):
    """Protocol for data access repositories."""

    async def connect(self) -> None:
        """Establish connection to data source."""
        ...

    async def disconnect(self) -> None:
        """Close connection to data source."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if repository is connected."""
        ...


@runtime_checkable
class ToolInterface(Protocol):
    """Protocol for framework tools."""

    @property
    def name(self) -> str:
        """Tool name."""
        ...

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with given parameters."""
        ...


@runtime_checkable
class MessageBus(Protocol):
    """Protocol for message bus implementations."""

    async def publish(self, topic: str, message: Any) -> None:
        """Publish a message to a topic."""
        ...

    async def subscribe(self, topic: str, handler: Any) -> None:
        """Subscribe to messages on a topic."""
        ...

    async def unsubscribe(self, topic: str, handler: Any) -> None:
        """Unsubscribe from messages on a topic."""
        ...


class BaseService(ABC):
    """Abstract base class for framework services with lifecycle management."""

    def __init__(self) -> None:
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service. Must be implemented by subclasses."""
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    async def _set_initialized(self) -> None:
        """Mark service as initialized. Called by subclass after successful init."""
        self._initialized = True

    async def _set_shutdown(self) -> None:
        """Mark service as shutdown. Called by subclass during shutdown."""
        self._initialized = False


class ConfigurationError(Exception):
    """Raised when there are configuration issues."""
    pass


class ServiceError(Exception):
    """Raised when there are service-related errors."""
    pass


class DependencyError(Exception):
    """Raised when there are dependency injection issues."""
    pass
