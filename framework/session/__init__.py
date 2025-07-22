"""
Remote Session Management System for Gary-Zero.

This module provides unified session management for tools that require 
persistent connections across local and remote environments.
"""

from .session_manager import RemoteSessionManager
from .session_interface import SessionInterface, SessionType, SessionState
from .connection_pool import ConnectionPool
from .session_config import SessionConfig

__all__ = [
    'RemoteSessionManager',
    'SessionInterface', 
    'SessionType',
    'SessionState',
    'ConnectionPool',
    'SessionConfig'
]