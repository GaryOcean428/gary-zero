"""
Unified logging system that consolidates different logging approaches.

This module creates a centralized event logging system that integrates:
- framework.security.audit_logger
- framework.performance.monitor  
- framework.helpers.log
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..security.audit_logger import AuditLogger, AuditEvent, AuditEventType, AuditLevel
from ..performance.monitor import PerformanceMonitor, get_performance_monitor
from ..helpers.log import Log, LogItem


class LogLevel(Enum):
    """Unified log levels."""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of events in the unified logging system."""
    # User interactions
    USER_INPUT = "user_input"
    USER_ACTION = "user_action"
    
    # System operations
    TOOL_EXECUTION = "tool_execution"
    CODE_EXECUTION = "code_execution"
    GUI_ACTION = "gui_action"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    MEMORY_OPERATION = "memory_operation"
    
    # Infrastructure
    PERFORMANCE_METRIC = "performance_metric"
    SYSTEM_EVENT = "system_event"
    CONFIG_CHANGE = "config_change"
    
    # Security and authentication
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT = "rate_limit"
    
    # Planning and scheduling
    AGENT_DECISION = "agent_decision"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Errors and diagnostics
    ERROR = "error"
    EXCEPTION = "exception"


@dataclass
class LogEvent:
    """Unified log event structure."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    event_type: EventType = EventType.SYSTEM_EVENT
    level: LogLevel = LogLevel.INFO
    message: str = ""
    
    # Context information
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Technical details
    component: Optional[str] = None
    function_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Data payloads (sanitized)
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        data['timestamp_iso'] = datetime.fromtimestamp(
            self.timestamp, tz=timezone.utc
        ).isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


class UnifiedLogger:
    """
    Unified logging system that consolidates different logging approaches.
    
    Integrates with existing audit logger, performance monitor, and log helpers
    while providing a centralized interface and enhanced capabilities.
    """
    
    def __init__(self, 
                 storage_path: Optional[str] = None,
                 max_buffer_size: int = 10000,
                 enable_performance_tracking: bool = True):
        self.storage_path = Path(storage_path) if storage_path else None
        self.max_buffer_size = max_buffer_size
        self.enable_performance_tracking = enable_performance_tracking
        
        # Event buffer for in-memory access
        self.event_buffer: List[LogEvent] = []
        self.buffer_lock = asyncio.Lock()
        
        # Integration with existing systems
        self.audit_logger = AuditLogger(
            log_file=str(self.storage_path / "audit.log") if self.storage_path else None
        )
        
        if enable_performance_tracking:
            self.performance_monitor = get_performance_monitor()
        else:
            self.performance_monitor = None
        
        # Statistics
        self.events_logged = 0
        self.events_by_type = {}
        self.events_by_level = {}
    
    async def log_event(self, event: LogEvent) -> None:
        """Log a unified event."""
        # Sanitize sensitive data
        event = self._sanitize_event(event)
        
        # Add to buffer
        async with self.buffer_lock:
            self.event_buffer.append(event)
            if len(self.event_buffer) > self.max_buffer_size:
                self.event_buffer.pop(0)  # Remove oldest event
        
        # Update statistics
        self.events_logged += 1
        self.events_by_type[event.event_type.value] = (
            self.events_by_type.get(event.event_type.value, 0) + 1
        )
        self.events_by_level[event.level.value] = (
            self.events_by_level.get(event.level.value, 0) + 1
        )
        
        # Forward to existing systems
        await self._forward_to_audit_logger(event)
        self._forward_to_performance_monitor(event)
    
    async def log_tool_execution(self,
                                tool_name: str,
                                parameters: Dict[str, Any],
                                success: bool,
                                duration_ms: Optional[float] = None,
                                user_id: Optional[str] = None,
                                agent_id: Optional[str] = None,
                                output_data: Optional[Dict[str, Any]] = None,
                                error_message: Optional[str] = None) -> str:
        """Log tool execution with standardized format."""
        event = LogEvent(
            event_type=EventType.TOOL_EXECUTION,
            level=LogLevel.INFO if success else LogLevel.WARNING,
            message=f"Tool execution {'completed' if success else 'failed'}: {tool_name}",
            tool_name=tool_name,
            user_id=user_id,
            agent_id=agent_id,
            input_data={"parameters": parameters, "success": success},
            output_data=output_data,
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        await self.log_event(event)
        return event.event_id
    
    async def log_code_execution(self,
                               code_snippet: str,
                               language: str,
                               success: bool,
                               duration_ms: Optional[float] = None,
                               output: Optional[str] = None,
                               error_message: Optional[str] = None,
                               user_id: Optional[str] = None,
                               agent_id: Optional[str] = None) -> str:
        """Log code execution event."""
        # Truncate code for logging (security)
        code_preview = code_snippet[:200] + "..." if len(code_snippet) > 200 else code_snippet
        
        event = LogEvent(
            event_type=EventType.CODE_EXECUTION,
            level=LogLevel.INFO if success else LogLevel.ERROR,
            message=f"Code execution {'completed' if success else 'failed'}: {language}",
            user_id=user_id,
            agent_id=agent_id,
            input_data={
                "language": language,
                "code_preview": code_preview,
                "success": success
            },
            output_data={"output": output[:500] if output else None},  # Limit output size
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        await self.log_event(event)
        return event.event_id
    
    async def log_gui_action(self,
                           action_type: str,
                           element: str,
                           success: bool,
                           duration_ms: Optional[float] = None,
                           page_url: Optional[str] = None,
                           error_message: Optional[str] = None,
                           user_id: Optional[str] = None,
                           agent_id: Optional[str] = None) -> str:
        """Log GUI/browser action."""
        event = LogEvent(
            event_type=EventType.GUI_ACTION,
            level=LogLevel.INFO if success else LogLevel.WARNING,
            message=f"GUI action {action_type} on {element} {'completed' if success else 'failed'}",
            user_id=user_id,
            agent_id=agent_id,
            input_data={
                "action_type": action_type,
                "element": element,
                "page_url": page_url,
                "success": success
            },
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        await self.log_event(event)
        return event.event_id
    
    async def log_knowledge_retrieval(self,
                                    query: str,
                                    results_count: int,
                                    duration_ms: Optional[float] = None,
                                    source: Optional[str] = None,
                                    user_id: Optional[str] = None,
                                    agent_id: Optional[str] = None) -> str:
        """Log knowledge retrieval operation."""
        event = LogEvent(
            event_type=EventType.KNOWLEDGE_RETRIEVAL,
            level=LogLevel.INFO,
            message=f"Knowledge retrieval: {results_count} results for query",
            user_id=user_id,
            agent_id=agent_id,
            input_data={
                "query_preview": query[:100] + "..." if len(query) > 100 else query,
                "results_count": results_count,
                "source": source
            },
            duration_ms=duration_ms
        )
        
        await self.log_event(event)
        return event.event_id
    
    async def log_memory_operation(self,
                                 operation_type: str,
                                 entity_count: int,
                                 success: bool,
                                 duration_ms: Optional[float] = None,
                                 error_message: Optional[str] = None,
                                 user_id: Optional[str] = None,
                                 agent_id: Optional[str] = None) -> str:
        """Log memory/graph operation."""
        event = LogEvent(
            event_type=EventType.MEMORY_OPERATION,
            level=LogLevel.INFO if success else LogLevel.WARNING,
            message=f"Memory operation {operation_type} {'completed' if success else 'failed'}",
            user_id=user_id,
            agent_id=agent_id,
            input_data={
                "operation_type": operation_type,
                "entity_count": entity_count,
                "success": success
            },
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        await self.log_event(event)
        return event.event_id
    
    async def get_execution_timeline(self,
                                   agent_id: Optional[str] = None,
                                   session_id: Optional[str] = None,
                                   user_id: Optional[str] = None,
                                   start_time: Optional[float] = None,
                                   end_time: Optional[float] = None) -> List[LogEvent]:
        """Get a complete execution timeline for reconstruction."""
        execution_types = {
            EventType.TOOL_EXECUTION,
            EventType.CODE_EXECUTION,
            EventType.GUI_ACTION,
            EventType.KNOWLEDGE_RETRIEVAL,
            EventType.MEMORY_OPERATION,
            EventType.AGENT_DECISION
        }
        
        async with self.buffer_lock:
            events = [e for e in self.event_buffer if e.event_type in execution_types]
        
        # Apply filters
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort chronologically
        events.sort(key=lambda e: e.timestamp)
        return events
    
    async def get_events(self,
                        event_type: Optional[EventType] = None,
                        level: Optional[LogLevel] = None,
                        user_id: Optional[str] = None,
                        agent_id: Optional[str] = None,
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None,
                        limit: int = 100) -> List[LogEvent]:
        """Retrieve events with filtering."""
        async with self.buffer_lock:
            events = list(self.event_buffer)
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if level:
            events = [e for e in events if e.level == level]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            "total_events": self.events_logged,
            "events_in_buffer": len(self.event_buffer),
            "events_by_type": self.events_by_type.copy(),
            "events_by_level": self.events_by_level.copy(),
            "buffer_utilization": len(self.event_buffer) / self.max_buffer_size
        }
    
    def _sanitize_event(self, event: LogEvent) -> LogEvent:
        """Sanitize event data to remove sensitive information."""
        # Keywords that indicate sensitive data
        sensitive_keywords = {
            'password', 'token', 'key', 'secret', 'auth', 'credential',
            'api_key', 'access_token', 'private_key', 'ssh_key'
        }
        
        def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
            if not data:
                return data
            
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(keyword in key_lower for keyword in sensitive_keywords):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = sanitize_dict(value)
                elif isinstance(value, str) and len(value) > 1000:
                    # Truncate very long strings
                    sanitized[key] = value[:1000] + "... [TRUNCATED]"
                else:
                    sanitized[key] = value
            return sanitized
        
        # Create a copy and sanitize
        sanitized_event = LogEvent(**asdict(event))
        
        if sanitized_event.input_data:
            sanitized_event.input_data = sanitize_dict(sanitized_event.input_data)
        
        if sanitized_event.output_data:
            sanitized_event.output_data = sanitize_dict(sanitized_event.output_data)
        
        if sanitized_event.metadata:
            sanitized_event.metadata = sanitize_dict(sanitized_event.metadata)
        
        return sanitized_event
    
    async def _forward_to_audit_logger(self, event: LogEvent) -> None:
        """Forward appropriate events to the existing audit logger."""
        # Convert to audit event for security-related events
        security_events = {
            EventType.AUTHENTICATION,
            EventType.AUTHORIZATION,
            EventType.SECURITY_VIOLATION,
            EventType.RATE_LIMIT,
            EventType.CONFIG_CHANGE
        }
        
        if event.event_type in security_events:
            try:
                await self.audit_logger.log_event(self._to_audit_event(event))
            except Exception as e:
                # Log conversion error but don't fail
                print(f"Error forwarding to audit logger: {e}")
    
    def _forward_to_performance_monitor(self, event: LogEvent) -> None:
        """Forward performance metrics to the existing performance monitor."""
        if not self.performance_monitor:
            return
        
        try:
            # Record duration metrics
            if event.duration_ms is not None and event.tool_name:
                self.performance_monitor.metrics.record(
                    f"tool_duration_{event.tool_name}",
                    event.duration_ms,
                    tags={"event_type": event.event_type.value},
                    unit="ms"
                )
        except Exception as e:
            # Log error but don't fail
            print(f"Error forwarding to performance monitor: {e}")
    
    def _to_audit_event(self, event: LogEvent) -> AuditEvent:
        """Convert unified event to audit event."""
        # Map event type back to audit event type
        type_mapping = {
            EventType.AUTHENTICATION: AuditEventType.AUTHENTICATION,
            EventType.AUTHORIZATION: AuditEventType.AUTHORIZATION,
            EventType.SECURITY_VIOLATION: AuditEventType.SECURITY_VIOLATION,
            EventType.RATE_LIMIT: AuditEventType.RATE_LIMIT,
            EventType.CONFIG_CHANGE: AuditEventType.CONFIG_CHANGE,
            EventType.USER_INPUT: AuditEventType.USER_INPUT,
            EventType.TOOL_EXECUTION: AuditEventType.TOOL_EXECUTION,
            EventType.ERROR: AuditEventType.ERROR,
        }
        
        # Map level back to audit level
        level_mapping = {
            LogLevel.INFO: AuditLevel.INFO,
            LogLevel.WARNING: AuditLevel.WARNING,
            LogLevel.ERROR: AuditLevel.ERROR,
            LogLevel.CRITICAL: AuditLevel.CRITICAL,
        }
        
        return AuditEvent(
            event_type=type_mapping.get(event.event_type, AuditEventType.SYSTEM_EVENT),
            level=level_mapping.get(event.level, AuditLevel.INFO),
            message=event.message,
            timestamp=event.timestamp,
            user_id=event.user_id,
            session_id=event.session_id,
            tool_name=event.tool_name,
            input_data=event.input_data,
            output_data=event.output_data,
            error_details=event.error_message,
            metadata=event.metadata
        )


# Global unified logger instance
_unified_logger = None


def get_unified_logger() -> UnifiedLogger:
    """Get the global unified logger instance."""
    global _unified_logger
    if _unified_logger is None:
        _unified_logger = UnifiedLogger(
            storage_path="./logs",
            enable_performance_tracking=True
        )
    return _unified_logger