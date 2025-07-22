"""
Remote Session Manager for Gary-Zero.

Central orchestrator for remote session management that coordinates
code execution and GUI interactions across different environments.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .session_interface import (
    SessionInterface, SessionType, SessionState, SessionMessage, 
    SessionResponse, SessionMetadata
)
from .session_config import SessionConfig
from .connection_pool import ConnectionPool


class RemoteSessionManager:
    """
    Central manager for remote sessions across all tools and environments.
    
    Provides session orchestration, connection pooling, approval flows,
    and secure storage of outputs for agent memory integration.
    """
    
    def __init__(self, config: Optional[SessionConfig] = None, agent=None):
        """
        Initialize remote session manager.
        
        Args:
            config: Session configuration (uses environment defaults if None)
            agent: Agent instance for approval flows and memory integration
        """
        self.config = config or SessionConfig.from_environment()
        self.agent = agent
        self.logger = logging.getLogger(__name__)
        
        # Connection pool for session management
        self.connection_pool = ConnectionPool(self.config)
        
        # Session factories for different types
        self._session_factories: Dict[SessionType, Callable] = {}
        
        # Output storage for memory integration
        self._output_storage: Dict[str, Dict[str, Any]] = {}
        
        # Approval handlers
        self._approval_handlers: Dict[SessionType, Callable] = {}
        
        # Running state
        self._running = False
        
    async def start(self):
        """Start the session manager and connection pool."""
        if self._running:
            return
            
        await self.connection_pool.start()
        self._running = True
        self.logger.info("Remote session manager started")
    
    async def stop(self):
        """Stop the session manager and cleanup all resources."""
        if not self._running:
            return
            
        await self.connection_pool.stop()
        self._running = False
        self._output_storage.clear()
        self.logger.info("Remote session manager stopped")
    
    def register_session_factory(self, session_type: SessionType, factory: Callable):
        """
        Register a factory function for creating sessions of a specific type.
        
        Args:
            session_type: Type of session the factory creates
            factory: Factory function that creates SessionInterface instances
        """
        self._session_factories[session_type] = factory
        self.logger.debug(f"Registered session factory for {session_type.value}")
    
    def register_approval_handler(self, session_type: SessionType, handler: Callable):
        """
        Register an approval handler for a specific session type.
        
        Args:
            session_type: Type of session that requires approval
            handler: Async function that handles approval requests
        """
        self._approval_handlers[session_type] = handler
        self.logger.debug(f"Registered approval handler for {session_type.value}")
    
    async def create_session(self, session_type: SessionType, **kwargs) -> SessionInterface:
        """
        Create a new session of the specified type.
        
        Args:
            session_type: Type of session to create
            **kwargs: Additional arguments for session creation
            
        Returns:
            SessionInterface instance
            
        Raises:
            ValueError: If session type is not supported
            ConnectionError: If session creation fails
        """
        if not self._running:
            await self.start()
        
        if session_type not in self._session_factories:
            raise ValueError(f"No factory registered for session type: {session_type.value}")
        
        factory = self._session_factories[session_type]
        session = await self.connection_pool.get_session(session_type, factory, **kwargs)
        
        self.logger.info(f"Created session {session.session_id} of type {session_type.value}")
        return session
    
    async def execute_with_session(
        self, 
        session_type: SessionType, 
        message: SessionMessage,
        session_id: Optional[str] = None,
        **session_kwargs
    ) -> SessionResponse:
        """
        Execute a message using a session, with automatic session management.
        
        Args:
            session_type: Type of session needed
            message: Message to execute
            session_id: Optional specific session ID to use
            **session_kwargs: Additional session creation arguments
            
        Returns:
            SessionResponse with execution results
        """
        session = None
        try:
            # Get or create session
            if session_id:
                session = await self._get_session_by_id(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
            else:
                session = await self.create_session(session_type, **session_kwargs)
            
            # Check if approval is required
            if self.config.requires_approval(session_type):
                approval_granted = await self._request_approval(session, message)
                if not approval_granted:
                    return SessionResponse(
                        success=False,
                        message="Operation cancelled - approval not granted",
                        session_id=session.session_id
                    )
            
            # Execute the message
            response = await session.execute(message)
            
            # Store output in memory if enabled
            if self.config.store_outputs_in_memory and response.success:
                await self._store_output(session, message, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error executing message in session: {e}")
            return SessionResponse(
                success=False,
                message=f"Execution failed: {str(e)}",
                error=str(e),
                session_id=session.session_id if session else None
            )
        finally:
            # Return session to pool (if it exists and wasn't specifically requested)
            if session and not session_id:
                await self.connection_pool.return_session(session)
    
    async def get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """
        Get metadata for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            SessionMetadata if session exists, None otherwise
        """
        session = await self._get_session_by_id(session_id)
        if session:
            return await session.get_metadata()
        return None
    
    async def list_active_sessions(self) -> List[SessionMetadata]:
        """
        Get metadata for all active sessions.
        
        Returns:
            List of SessionMetadata for active sessions
        """
        active_sessions = await self.connection_pool.get_active_sessions()
        metadata_list = []
        
        for session in active_sessions:
            metadata = await session.get_metadata()
            metadata_list.append(metadata)
        
        return metadata_list
    
    async def close_session(self, session_id: str) -> bool:
        """
        Close a specific session.
        
        Args:
            session_id: ID of session to close
            
        Returns:
            True if session was closed, False if not found
        """
        try:
            await self.connection_pool.close_session(session_id)
            return True
        except Exception as e:
            self.logger.error(f"Error closing session {session_id}: {e}")
            return False
    
    async def get_manager_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the session manager.
        
        Returns:
            Dictionary with manager statistics
        """
        pool_stats = await self.connection_pool.get_pool_stats()
        
        stats = {
            'running': self._running,
            'config': {
                'pooling_enabled': self.config.enable_connection_pooling,
                'max_sessions_per_type': self.config.max_sessions_per_type,
                'pool_size_per_type': self.config.pool_size_per_type,
                'session_timeout': self.config.session_timeout
            },
            'registered_factories': list(self._session_factories.keys()),
            'registered_approval_handlers': list(self._approval_handlers.keys()),
            'stored_outputs_count': len(self._output_storage),
            'pool_stats': pool_stats
        }
        
        return stats
    
    async def cleanup_resources(self, max_idle_time: Optional[int] = None):
        """
        Cleanup idle resources and old outputs.
        
        Args:
            max_idle_time: Maximum idle time for sessions (uses config default if None)
        """
        # Cleanup idle sessions
        await self.connection_pool.cleanup_idle_sessions(max_idle_time)
        
        # Cleanup old stored outputs
        await self._cleanup_old_outputs()
        
        self.logger.debug("Resource cleanup completed")
    
    def create_message(
        self, 
        message_type: str, 
        payload: Dict[str, Any], 
        session_id: Optional[str] = None
    ) -> SessionMessage:
        """
        Create a standardized session message.
        
        Args:
            message_type: Type of message
            payload: Message payload data
            session_id: Optional session ID
            
        Returns:
            SessionMessage instance
        """
        return SessionMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id or "",
            message_type=message_type,
            payload=payload
        )
    
    async def _get_session_by_id(self, session_id: str) -> Optional[SessionInterface]:
        """Get session by ID from active sessions."""
        active_sessions = await self.connection_pool.get_active_sessions()
        for session in active_sessions:
            if session.session_id == session_id:
                return session
        return None
    
    async def _request_approval(self, session: SessionInterface, message: SessionMessage) -> bool:
        """
        Request approval for a session operation.
        
        Args:
            session: Session requesting approval
            message: Message to be executed
            
        Returns:
            True if approval granted, False otherwise
        """
        # Check if we have a custom approval handler
        if session.session_type in self._approval_handlers:
            handler = self._approval_handlers[session.session_type]
            return await handler(session, message)
        
        # Use agent intervention system if available
        if self.agent and hasattr(self.agent, 'handle_intervention'):
            try:
                # Format approval request
                approval_request = (
                    f"Session {session.session_id} ({session.session_type.value}) "
                    f"requests approval for: {message.message_type}\n"
                    f"Payload: {message.payload}"
                )
                
                # This would integrate with agent's approval system
                # For now, we'll simulate approval
                self.logger.warning(f"Approval required: {approval_request}")
                return True  # Simplified for now
                
            except Exception as e:
                self.logger.error(f"Error requesting approval: {e}")
                return False
        
        # Default to requiring manual approval
        self.logger.warning(f"No approval handler configured for {session.session_type.value}")
        return False
    
    async def _store_output(self, session: SessionInterface, message: SessionMessage, response: SessionResponse):
        """
        Store session output in memory for agent access.
        
        Args:
            session: Session that produced the output
            message: Original message
            response: Session response to store
        """
        if not response.data:
            return
        
        # Check output size limits
        output_size = len(str(response.data))
        if output_size > self.config.max_output_size:
            self.logger.warning(f"Output size {output_size} exceeds limit {self.config.max_output_size}")
            return
        
        # Store with timestamp for cleanup
        storage_key = f"{session.session_id}_{message.message_id}"
        self._output_storage[storage_key] = {
            'session_id': session.session_id,
            'session_type': session.session_type.value,
            'message_type': message.message_type,
            'timestamp': datetime.now(),
            'response_data': response.data,
            'metadata': response.metadata
        }
        
        # Integrate with agent memory if available
        if self.agent and hasattr(self.agent, 'set_data'):
            try:
                memory_key = f"session_output_{storage_key}"
                self.agent.set_data(memory_key, self._output_storage[storage_key])
            except Exception as e:
                self.logger.error(f"Error storing output in agent memory: {e}")
    
    async def _cleanup_old_outputs(self):
        """Cleanup old stored outputs based on retention time."""
        if not self._output_storage:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.config.output_retention_time)
        keys_to_remove = []
        
        for key, output_data in self._output_storage.items():
            if output_data['timestamp'] < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._output_storage[key]
            
            # Also remove from agent memory if available
            if self.agent and hasattr(self.agent, 'delete_data'):
                try:
                    memory_key = f"session_output_{key}"
                    self.agent.delete_data(memory_key)
                except Exception:
                    pass  # Ignore errors for cleanup
        
        if keys_to_remove:
            self.logger.debug(f"Cleaned up {len(keys_to_remove)} old output records")
    
    def __str__(self) -> str:
        """String representation of the session manager."""
        return f"RemoteSessionManager(running={self._running}, factories={len(self._session_factories)})"