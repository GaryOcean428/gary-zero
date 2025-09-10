"""Domain events for the Gary-Zero framework.

Implements the event-driven architecture pattern with an async event bus
for decoupled communication between domain components.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: str = ""
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """The type identifier for this event."""
        pass


@dataclass
class AgentCreatedEvent(DomainEvent):
    """Event raised when a new agent is created."""
    
    agent_id: str = ""
    agent_type: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def event_type(self) -> str:
        return "agent.created"


@dataclass
class MessageProcessedEvent(DomainEvent):
    """Event raised when a message is processed."""
    
    message_id: str = ""
    agent_id: str = ""
    content: str = ""
    processing_time_ms: float = 0.0
    
    @property
    def event_type(self) -> str:
        return "message.processed"


@dataclass
class ToolExecutedEvent(DomainEvent):
    """Event raised when a tool is executed."""
    
    tool_name: str = ""
    agent_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    execution_time_ms: float = 0.0
    
    @property
    def event_type(self) -> str:
        return "tool.executed"


class EventBus:
    """Async event bus for domain events using the observer pattern."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[DomainEvent], Any]]] = {}
        self._middleware: List[Callable[[DomainEvent], Any]] = []
        
    def register_handler(self, event_type: str, handler: Callable[[DomainEvent], Any]):
        """Register an event handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")
        
    def register_middleware(self, middleware: Callable[[DomainEvent], Any]):
        """Register middleware that runs for all events."""
        self._middleware.append(middleware)
        logger.debug("Registered event middleware")
        
    def unregister_handler(self, event_type: str, handler: Callable[[DomainEvent], Any]):
        """Unregister an event handler."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        try:
            # Run middleware first
            for middleware in self._middleware:
                if asyncio.iscoroutinefunction(middleware):
                    await middleware(event)
                else:
                    middleware(event)
            
            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])
            
            if handlers:
                # Execute all handlers concurrently
                tasks = []
                for handler in handlers:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(handler(event))
                    else:
                        # Wrap sync handler in coroutine
                        tasks.append(asyncio.create_task(
                            asyncio.to_thread(handler, event)
                        ))
                
                # Wait for all handlers to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.debug(f"Published event {event.event_type} to {len(handlers)} handlers")
            else:
                logger.debug(f"No handlers registered for event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"Error publishing event {event.event_type}: {e}")
            raise
    
    def get_handler_count(self, event_type: str) -> int:
        """Get the number of handlers registered for an event type."""
        return len(self._handlers.get(event_type, []))
    
    def clear_handlers(self, event_type: str = None) -> None:
        """Clear handlers for a specific event type or all handlers."""
        if event_type:
            self._handlers.pop(event_type, None)
            logger.debug(f"Cleared handlers for event type: {event_type}")
        else:
            self._handlers.clear()
            self._middleware.clear()
            logger.debug("Cleared all event handlers and middleware")


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _event_bus
    _event_bus = None