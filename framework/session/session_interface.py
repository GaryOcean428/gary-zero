"""
Session Interface and Base Classes for Remote Session Management.

Defines the abstract interface and common types used by all session types.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SessionType(Enum):
    """Types of remote sessions supported."""
    HTTP = "http"
    SSH = "ssh"
    GUI = "gui"
    CLI = "cli"
    TERMINAL = "terminal"
    WEBSOCKET = "websocket"


class SessionState(Enum):
    """Session lifecycle states."""
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    ACTIVE = "active"
    IDLE = "idle"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class SessionMetadata:
    """Metadata about a session."""
    session_id: str
    session_type: SessionType
    state: SessionState = SessionState.INITIALIZING
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    connection_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    tags: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMessage:
    """Standard message format for session communication."""
    message_id: str
    session_id: str
    message_type: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionResponse:
    """Standard response format from session operations."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionInterface(ABC):
    """Abstract interface for all session types."""

    def __init__(self, session_id: str, session_type: SessionType, config: dict[str, Any]):
        """
        Initialize session interface.
        
        Args:
            session_id: Unique identifier for the session
            session_type: Type of session
            config: Session configuration
        """
        self.session_id = session_id
        self.session_type = session_type
        self.config = config
        self.metadata = SessionMetadata(
            session_id=session_id,
            session_type=session_type
        )
        self._connection_lock = asyncio.Lock()

    @abstractmethod
    async def connect(self) -> SessionResponse:
        """
        Establish connection to the remote service.
        
        Returns:
            SessionResponse indicating success or failure
        """
        pass

    @abstractmethod
    async def disconnect(self) -> SessionResponse:
        """
        Close connection to the remote service.
        
        Returns:
            SessionResponse indicating success or failure
        """
        pass

    @abstractmethod
    async def execute(self, message: SessionMessage) -> SessionResponse:
        """
        Execute a command or operation in the session.
        
        Args:
            message: The message containing the operation to execute
            
        Returns:
            SessionResponse with operation results
        """
        pass

    @abstractmethod
    async def health_check(self) -> SessionResponse:
        """
        Check if the session is healthy and responsive.
        
        Returns:
            SessionResponse indicating session health
        """
        pass

    async def is_connected(self) -> bool:
        """
        Check if session is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.metadata.state in [SessionState.CONNECTED, SessionState.ACTIVE, SessionState.IDLE]

    async def update_state(self, new_state: SessionState, error: str | None = None):
        """
        Update session state and metadata.
        
        Args:
            new_state: New state to set
            error: Optional error message if state is ERROR
        """
        async with self._connection_lock:
            self.metadata.state = new_state
            self.metadata.last_used = datetime.now()

            if error:
                self.metadata.error_count += 1
                self.metadata.last_error = error

    async def get_metadata(self) -> SessionMetadata:
        """
        Get current session metadata.
        
        Returns:
            Current session metadata
        """
        return self.metadata

    def __str__(self) -> str:
        """String representation of the session."""
        return f"{self.__class__.__name__}({self.session_id}, {self.session_type.value}, {self.metadata.state.value})"


class SessionPool(ABC):
    """Abstract interface for session pooling."""

    @abstractmethod
    async def get_session(self, session_type: SessionType, config: dict[str, Any]) -> SessionInterface:
        """
        Get a session from the pool or create a new one.
        
        Args:
            session_type: Type of session needed
            config: Configuration for the session
            
        Returns:
            SessionInterface instance
        """
        pass

    @abstractmethod
    async def return_session(self, session: SessionInterface):
        """
        Return a session to the pool for reuse.
        
        Args:
            session: Session to return to pool
        """
        pass

    @abstractmethod
    async def cleanup_sessions(self, max_idle_time: int = 300):
        """
        Clean up idle or disconnected sessions.
        
        Args:
            max_idle_time: Maximum idle time in seconds before cleanup
        """
        pass
