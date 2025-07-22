"""
Unified logging and monitoring framework.

This module provides a consolidated approach to logging, monitoring and benchmarking
that integrates with existing systems while providing enhanced capabilities.
"""

from .hooks import LoggingHooks
from .storage import LogStorage, SqliteStorage
from .unified_logger import EventType, LogEvent, LogLevel, UnifiedLogger

__all__ = [
    'UnifiedLogger',
    'LogEvent',
    'LogLevel',
    'EventType',
    'LogStorage',
    'SqliteStorage',
    'LoggingHooks'
]
