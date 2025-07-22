"""
Connection Pool for Remote Session Management.

Manages connection pooling and reuse for different session types to reduce
latency and resource consumption while ensuring isolation.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta

from .session_interface import SessionInterface, SessionType, SessionState, SessionResponse
from .session_config import SessionConfig


class ConnectionPool:
    """
    Connection pool manager for remote sessions.
    
    Handles connection pooling, reuse, and cleanup for different session types
    while ensuring proper isolation between concurrent sessions.
    """
    
    def __init__(self, config: SessionConfig):
        """
        Initialize connection pool.
        
        Args:
            config: Session configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pool storage: session_type -> deque of available sessions
        self._pools: Dict[SessionType, deque] = defaultdict(deque)
        
        # Active sessions: session_id -> session
        self._active_sessions: Dict[str, SessionInterface] = {}
        
        # Session usage tracking
        self._session_usage: Dict[str, datetime] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        
        # Pool management
        self._pool_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start the connection pool and background cleanup task."""
        if self._running:
            return
            
        self._running = True
        
        if self.config.enable_connection_pooling:
            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            self.logger.info("Connection pool started with background cleanup")
        else:
            self.logger.info("Connection pool started without pooling (disabled)")
    
    async def stop(self):
        """Stop the connection pool and cleanup all sessions."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all sessions
        await self._close_all_sessions()
        self.logger.info("Connection pool stopped")
    
    async def get_session(self, session_type: SessionType, session_factory, **kwargs) -> SessionInterface:
        """
        Get a session from the pool or create a new one.
        
        Args:
            session_type: Type of session needed
            session_factory: Factory function to create new sessions
            **kwargs: Additional arguments for session creation
            
        Returns:
            SessionInterface instance
        """
        if not self._running:
            await self.start()
        
        async with self._pool_lock:
            # Try to get from pool first if pooling is enabled
            if self.config.enable_connection_pooling and self._pools[session_type]:
                session = self._pools[session_type].popleft()
                
                # Check if session is still healthy
                health_response = await session.health_check()
                if health_response.success:
                    # Session is healthy, mark as active
                    self._active_sessions[session.session_id] = session
                    self._session_usage[session.session_id] = datetime.now()
                    await session.update_state(SessionState.ACTIVE)
                    
                    self.logger.debug(f"Reused session {session.session_id} from pool")
                    return session
                else:
                    # Session is unhealthy, disconnect and create new one
                    await session.disconnect()
                    self.logger.debug(f"Discarded unhealthy session {session.session_id}")
            
            # Create new session
            session = await session_factory(**kwargs)
            
            # Connect the session
            connect_response = await session.connect()
            if not connect_response.success:
                raise ConnectionError(f"Failed to connect session: {connect_response.error}")
            
            # Track as active session
            self._active_sessions[session.session_id] = session
            self._session_usage[session.session_id] = datetime.now()
            self._session_locks[session.session_id] = asyncio.Lock()
            
            self.logger.debug(f"Created new session {session.session_id}")
            return session
    
    async def return_session(self, session: SessionInterface, force_close: bool = False):
        """
        Return a session to the pool for reuse or close it.
        
        Args:
            session: Session to return
            force_close: If True, close session instead of pooling
        """
        if not session or session.session_id not in self._active_sessions:
            return
        
        async with self._pool_lock:
            # Remove from active sessions
            self._active_sessions.pop(session.session_id, None)
            self._session_usage.pop(session.session_id, None)
            self._session_locks.pop(session.session_id, None)
            
            # Check if we should pool or close the session
            should_pool = (
                self.config.enable_connection_pooling and
                not force_close and
                await session.is_connected() and
                len(self._pools[session.session_type]) < self.config.pool_size_per_type
            )
            
            if should_pool:
                # Return to pool
                await session.update_state(SessionState.IDLE)
                self._pools[session.session_type].append(session)
                self.logger.debug(f"Returned session {session.session_id} to pool")
            else:
                # Close the session
                await session.disconnect()
                self.logger.debug(f"Closed session {session.session_id}")
    
    async def get_active_sessions(self) -> List[SessionInterface]:
        """
        Get list of all active sessions.
        
        Returns:
            List of active sessions
        """
        return list(self._active_sessions.values())
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        async with self._pool_lock:
            stats = {
                'total_active_sessions': len(self._active_sessions),
                'pooled_sessions_by_type': {
                    session_type.value: len(sessions) 
                    for session_type, sessions in self._pools.items()
                },
                'total_pooled_sessions': sum(len(sessions) for sessions in self._pools.values()),
                'session_types_in_use': list(set(s.session_type for s in self._active_sessions.values())),
                'oldest_session_age': None,
                'pool_enabled': self.config.enable_connection_pooling
            }
            
            # Calculate oldest session age
            if self._session_usage:
                oldest_time = min(self._session_usage.values())
                stats['oldest_session_age'] = (datetime.now() - oldest_time).total_seconds()
            
            return stats
    
    async def cleanup_idle_sessions(self, max_idle_time: Optional[int] = None):
        """
        Clean up idle sessions that exceed the maximum idle time.
        
        Args:
            max_idle_time: Maximum idle time in seconds (uses config default if None)
        """
        if max_idle_time is None:
            max_idle_time = self.config.max_idle_time
        
        cutoff_time = datetime.now() - timedelta(seconds=max_idle_time)
        
        async with self._pool_lock:
            # Clean up pooled sessions
            for session_type in list(self._pools.keys()):
                pool = self._pools[session_type]
                sessions_to_remove = []
                
                for session in pool:
                    if session.metadata.last_used < cutoff_time:
                        sessions_to_remove.append(session)
                
                # Remove and close idle sessions
                for session in sessions_to_remove:
                    pool.remove(session)
                    await session.disconnect()
                    self.logger.debug(f"Cleaned up idle session {session.session_id}")
            
            # Clean up active sessions that are idle
            sessions_to_close = []
            for session_id, last_used in self._session_usage.items():
                if last_used < cutoff_time:
                    session = self._active_sessions.get(session_id)
                    if session:
                        sessions_to_close.append(session)
            
            # Close idle active sessions
            for session in sessions_to_close:
                await self.return_session(session, force_close=True)
                self.logger.debug(f"Cleaned up idle active session {session.session_id}")
    
    async def close_session(self, session_id: str):
        """
        Force close a specific session.
        
        Args:
            session_id: ID of session to close
        """
        session = self._active_sessions.get(session_id)
        if session:
            await self.return_session(session, force_close=True)
    
    async def _close_all_sessions(self):
        """Close all active and pooled sessions."""
        # Close active sessions
        active_sessions = list(self._active_sessions.values())
        for session in active_sessions:
            await self.return_session(session, force_close=True)
        
        # Close pooled sessions
        for session_type in list(self._pools.keys()):
            pool = self._pools[session_type]
            while pool:
                session = pool.popleft()
                await session.disconnect()
        
        self._active_sessions.clear()
        self._session_usage.clear()
        self._session_locks.clear()
        self._pools.clear()
    
    async def _cleanup_worker(self):
        """Background worker for periodic cleanup of idle sessions."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                if self._running:
                    await self.cleanup_idle_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
    
    def __str__(self) -> str:
        """String representation of the connection pool."""
        active_count = len(self._active_sessions)
        pooled_count = sum(len(sessions) for sessions in self._pools.values())
        return f"ConnectionPool(active={active_count}, pooled={pooled_count}, running={self._running})"