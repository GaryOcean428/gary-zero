"""Comprehensive audit logging for security events and system activities."""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AuditEventType(Enum):
    """Types of audit events."""
    USER_INPUT = "user_input"
    TOOL_EXECUTION = "tool_execution"
    CONFIG_CHANGE = "config_change"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_DECISION = "approval_decision"
    RATE_LIMIT = "rate_limit"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class AuditLevel(Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: AuditEventType
    level: AuditLevel
    message: str
    timestamp: float
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    tool_name: str | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error_details: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        data['timestamp_iso'] = datetime.fromtimestamp(
            self.timestamp, tz=UTC
        ).isoformat()
        return data

    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(self, log_file: str | None = None, max_buffer_size: int = 1000):
        self.log_file = Path(log_file) if log_file else None
        self.max_buffer_size = max_buffer_size
        self.buffer: list[AuditEvent] = []
        self.buffer_lock = asyncio.Lock()

        # Set up structured logging
        self.logger = logging.getLogger("gary_zero.audit")
        self.logger.setLevel(logging.INFO)

        # Create formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    async def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        # Add to buffer
        async with self.buffer_lock:
            self.buffer.append(event)
            if len(self.buffer) > self.max_buffer_size:
                self.buffer.pop(0)  # Remove oldest event

        # Log to structured logger
        log_message = f"{event.event_type.value}: {event.message}"
        log_data = {"audit_event": event.to_dict()}

        if event.level == AuditLevel.INFO:
            self.logger.info(log_message, extra=log_data)
        elif event.level == AuditLevel.WARNING:
            self.logger.warning(log_message, extra=log_data)
        elif event.level == AuditLevel.ERROR:
            self.logger.error(log_message, extra=log_data)
        elif event.level == AuditLevel.CRITICAL:
            self.logger.critical(log_message, extra=log_data)

    async def log_user_input(self, user_id: str, content: str,
                           content_type: str = "text", **kwargs) -> None:
        """Log user input event."""
        event = AuditEvent(
            event_type=AuditEventType.USER_INPUT,
            level=AuditLevel.INFO,
            message=f"User input received: {content_type}",
            timestamp=time.time(),
            user_id=user_id,
            input_data={
                "content_length": len(content),
                "content_type": content_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_tool_execution(self, user_id: str, tool_name: str,
                               parameters: dict[str, Any], success: bool,
                               execution_time: float, **kwargs) -> None:
        """Log tool execution event."""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        message = f"Tool execution {'completed' if success else 'failed'}: {tool_name}"

        event = AuditEvent(
            event_type=AuditEventType.TOOL_EXECUTION,
            level=level,
            message=message,
            timestamp=time.time(),
            user_id=user_id,
            tool_name=tool_name,
            input_data={
                "parameters": parameters,
                "execution_time": execution_time,
                "success": success
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_config_change(self, user_id: str, key: str, old_value: Any,
                              new_value: Any, **kwargs) -> None:
        """Log configuration change event."""
        event = AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE,
            level=AuditLevel.INFO,
            message=f"Configuration changed: {key}",
            timestamp=time.time(),
            user_id=user_id,
            input_data={
                "key": key,
                "old_value": str(old_value)[:200],  # Truncate for security
                "new_value": str(new_value)[:200],
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_security_violation(self, event_details: str, severity: AuditLevel,
                                   user_id: str | None = None, **kwargs) -> None:
        """Log security violation event."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            level=severity,
            message=f"Security violation: {event_details}",
            timestamp=time.time(),
            user_id=user_id,
            **kwargs
        )
        await self.log_event(event)

    async def log_rate_limit(self, endpoint: str, identifier: str,
                           limit_type: str, **kwargs) -> None:
        """Log rate limit exceeded event."""
        event = AuditEvent(
            event_type=AuditEventType.RATE_LIMIT,
            level=AuditLevel.WARNING,
            message=f"Rate limit exceeded: {endpoint}",
            timestamp=time.time(),
            endpoint=endpoint,
            input_data={
                "identifier": identifier,
                "limit_type": limit_type
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_authentication(self, user_id: str, success: bool,
                               method: str, **kwargs) -> None:
        """Log authentication event."""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        message = f"Authentication {'successful' if success else 'failed'}: {method}"

        event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            level=level,
            message=message,
            timestamp=time.time(),
            user_id=user_id,
            input_data={
                "method": method,
                "success": success
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_error(self, error_message: str, error_type: str,
                       user_id: str | None = None, **kwargs) -> None:
        """Log error event."""
        event = AuditEvent(
            event_type=AuditEventType.ERROR,
            level=AuditLevel.ERROR,
            message=f"Error occurred: {error_type}",
            timestamp=time.time(),
            user_id=user_id,
            error_details=error_message,
            **kwargs
        )
        await self.log_event(event)

    async def log_approval_request(self, user_id: str, action_type: str,
                                 risk_level: str, request_id: str, **kwargs) -> None:
        """Log approval request event."""
        event = AuditEvent(
            event_type=AuditEventType.APPROVAL_REQUEST,
            level=AuditLevel.INFO,
            message=f"Approval requested for {action_type}",
            timestamp=time.time(),
            user_id=user_id,
            input_data={
                "action_type": action_type,
                "risk_level": risk_level,
                "request_id": request_id
            },
            **kwargs
        )
        await self.log_event(event)

    async def log_approval_decision(self, user_id: str, action_type: str,
                                  approved: bool, approver_id: str,
                                  request_id: str, reason: str | None = None, **kwargs) -> None:
        """Log approval decision event."""
        level = AuditLevel.INFO if approved else AuditLevel.WARNING
        message = f"Action {action_type} {'approved' if approved else 'denied'}"

        event = AuditEvent(
            event_type=AuditEventType.APPROVAL_DECISION,
            level=level,
            message=message,
            timestamp=time.time(),
            user_id=user_id,
            input_data={
                "action_type": action_type,
                "approved": approved,
                "approver_id": approver_id,
                "request_id": request_id,
                "reason": reason
            },
            **kwargs
        )
        await self.log_event(event)

    async def get_events(self, event_type: AuditEventType | None = None,
                        user_id: str | None = None,
                        start_time: float | None = None,
                        end_time: float | None = None,
                        limit: int = 100) -> list[AuditEvent]:
        """Retrieve audit events with filtering."""
        async with self.buffer_lock:
            events = list(self.buffer)

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_security_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get security summary for the last N hours."""
        start_time = time.time() - (hours * 3600)
        events = await self.get_events(start_time=start_time)

        summary = {
            "total_events": len(events),
            "security_violations": 0,
            "rate_limit_exceeded": 0,
            "authentication_failures": 0,
            "errors": 0,
            "events_by_type": {},
            "events_by_level": {},
            "hours_analyzed": hours
        }

        for event in events:
            # Count by type
            event_type = event.event_type.value
            summary["events_by_type"][event_type] = summary["events_by_type"].get(event_type, 0) + 1

            # Count by level
            level = event.level.value
            summary["events_by_level"][level] = summary["events_by_level"].get(level, 0) + 1

            # Count specific security events
            if event.event_type == AuditEventType.SECURITY_VIOLATION:
                summary["security_violations"] += 1
            elif event.event_type == AuditEventType.RATE_LIMIT:
                summary["rate_limit_exceeded"] += 1
            elif (event.event_type == AuditEventType.AUTHENTICATION and
                  event.input_data and not event.input_data.get("success", True)):
                summary["authentication_failures"] += 1
            elif event.event_type == AuditEventType.ERROR:
                summary["errors"] += 1

        return summary

    async def export_events(self, file_path: str,
                          event_type: AuditEventType | None = None,
                          start_time: float | None = None,
                          end_time: float | None = None) -> int:
        """Export audit events to a file."""
        events = await self.get_events(event_type, None, start_time, end_time, limit=10000)

        export_path = Path(file_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, 'w') as f:
            for event in events:
                f.write(event.to_json() + '\n')

        return len(events)

    def clear_buffer(self) -> None:
        """Clear the audit event buffer."""
        asyncio.create_task(self._clear_buffer_async())

    async def _clear_buffer_async(self) -> None:
        """Async method to clear buffer."""
        async with self.buffer_lock:
            self.buffer.clear()
