"""
Remote Session Management System for Gary-Zero.

This module provides unified session management for tools that require 
persistent connections across local and remote environments.
"""

from .connection_pool import ConnectionPool
from .session_config import SessionConfig
from .session_interface import SessionInterface, SessionState, SessionType
from .session_manager import RemoteSessionManager

__all__ = [
    'RemoteSessionManager',
    'SessionInterface',
    'SessionType',
    'SessionState',
    'ConnectionPool',
    'SessionConfig'
]
