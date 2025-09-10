"""Domain entities for the Gary-Zero framework.

Implements domain entity patterns with unique identity, lifecycle management,
and domain events integration.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from .events import DomainEvent

logger = logging.getLogger(__name__)


@dataclass(eq=False)
class DomainEntity(ABC):
    """Base class for all domain entities with identity and event support."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = field(default=1)
    
    # Events raised by this entity
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Initialize entity after creation."""
        if not self.id:
            self.id = str(uuid4())
        
    @property
    @abstractmethod
    def entity_type(self) -> str:
        """The type identifier for this entity."""
        pass
    
    def raise_event(self, event: DomainEvent) -> None:
        """Raise a domain event for this entity."""
        event.aggregate_id = self.id
        self._domain_events.append(event)
        logger.debug(f"Entity {self.id} raised event: {event.event_type}")
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get all uncommitted domain events."""
        return self._domain_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Clear all domain events (called after persistence)."""
        self._domain_events.clear()
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp and increment version."""
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def __eq__(self, other: object) -> bool:
        """Compare entities by ID."""
        if not isinstance(other, DomainEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash entities by ID."""
        return hash(self.id)


@dataclass(eq=False)
class Agent(DomainEntity):
    """Domain entity representing an AI agent."""
    
    name: str = ""
    agent_type: str = "generic"
    configuration: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"  # created, active, paused, stopped
    
    @property
    def entity_type(self) -> str:
        return "agent"
    
    def activate(self) -> None:
        """Activate the agent."""
        if self.status != "active":
            self.status = "active"
            self.update_timestamp()
            
            from .events import AgentCreatedEvent
            self.raise_event(AgentCreatedEvent(
                agent_id=self.id,
                agent_type=self.agent_type,
                configuration=self.configuration
            ))
    
    def pause(self) -> None:
        """Pause the agent."""
        if self.status == "active":
            self.status = "paused"
            self.update_timestamp()
    
    def stop(self) -> None:
        """Stop the agent."""
        if self.status in ["active", "paused"]:
            self.status = "stopped"
            self.update_timestamp()


@dataclass(eq=False)
class Message(DomainEntity):
    """Domain entity representing a message."""
    
    content: str = ""
    sender_id: str = ""
    recipient_id: str = ""
    message_type: str = "text"  # text, image, file, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    
    @property
    def entity_type(self) -> str:
        return "message"
    
    def mark_as_processed(self, processing_time_ms: float = 0.0) -> None:
        """Mark the message as processed."""
        if not self.processed:
            self.processed = True
            self.update_timestamp()
            
            from .events import MessageProcessedEvent
            self.raise_event(MessageProcessedEvent(
                message_id=self.id,
                agent_id=self.recipient_id,
                content=self.content,
                processing_time_ms=processing_time_ms
            ))


@dataclass(eq=False) 
class Tool(DomainEntity):
    """Domain entity representing a tool that can be executed."""
    
    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    @property
    def entity_type(self) -> str:
        return "tool"
    
    def execute(self, agent_id: str, parameters: Dict[str, Any], result: Any = None, 
                execution_time_ms: float = 0.0) -> None:
        """Record tool execution."""
        self.update_timestamp()
        
        from .events import ToolExecutedEvent
        self.raise_event(ToolExecutedEvent(
            tool_name=self.name,
            agent_id=agent_id,
            parameters=parameters,
            result=result,
            execution_time_ms=execution_time_ms
        ))


@dataclass(eq=False)
class Session(DomainEntity):
    """Domain entity representing a user or agent session."""
    
    user_id: str = ""
    session_type: str = "user"  # user, agent, system
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    status: str = "active"  # active, ended, timeout
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_type(self) -> str:
        return "session"
    
    def end_session(self) -> None:
        """End the session."""
        if self.status == "active":
            self.status = "ended"
            self.end_time = datetime.utcnow()
            self.update_timestamp()
    
    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()