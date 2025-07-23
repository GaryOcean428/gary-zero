"""Agent tracing and logging support for OpenAI Agents SDK integration.

This module provides enhanced tracing, logging, and monitoring capabilities
that integrate with both the OpenAI Agents SDK and Gary-Zero's existing
logging system.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# OpenAI Agents SDK imports
from agents import Span, Trace, set_trace_processors
from agents.tracing import TracingProcessor

# Gary-Zero imports
from framework.helpers import log as Log
from framework.helpers.print_style import PrintStyle


class TraceEventType(Enum):
    """Types of trace events."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    HANDOFF = "handoff"
    ERROR = "error"
    GUARDRAIL_VIOLATION = "guardrail_violation"


@dataclass
class TraceEvent:
    """Individual trace event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    span_id: str = ""
    event_type: TraceEventType = TraceEventType.AGENT_START
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    agent_name: str = ""
    task_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None
    success: bool = True
    error_message: str | None = None


class GaryZeroTracingProcessor(TracingProcessor):
    """Custom tracing processor for Gary-Zero integration."""

    def __init__(self, gary_logger: Log.Log | None = None):
        self.gary_logger = gary_logger
        self.trace_events: list[TraceEvent] = []
        self.active_spans: dict[str, datetime] = {}

    def on_trace_start(self, trace: Trace):
        """Handle trace start events."""
        # Optional: track trace-level events
        pass

    def on_trace_end(self, trace: Trace):
        """Handle trace end events."""
        # Optional: cleanup or final processing
        pass

    def force_flush(self):
        """Force flush any pending events."""
        # For now, we process events immediately, so no flushing needed
        pass

    def shutdown(self):
        """Shutdown the processor."""
        # Cleanup any resources
        self.trace_events.clear()
        self.active_spans.clear()

    def on_span_start(self, span: Span):
        """Handle span start events."""
        self.active_spans[span.span_id] = datetime.now(UTC)

        event = TraceEvent(
            trace_id=span.trace_id,
            span_id=span.span_id,
            event_type=self._map_span_to_event_type(span),
            agent_name=self._extract_agent_name(span),
            data=self._extract_span_data(span)
        )

        self.trace_events.append(event)
        self._log_event(event)

    def on_span_end(self, span: Span):
        """Handle span end events."""
        start_time = self.active_spans.pop(span.span_id, None)
        duration_ms = None

        if start_time:
            duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        event = TraceEvent(
            trace_id=span.trace_id,
            span_id=span.span_id,
            event_type=self._map_span_to_event_type(span, is_end=True),
            agent_name=self._extract_agent_name(span),
            data=self._extract_span_data(span),
            duration_ms=duration_ms,
            success=not span.error,
            error_message=str(span.error) if span.error else None
        )

        self.trace_events.append(event)
        self._log_event(event)

    def _map_span_to_event_type(self, span: Span, is_end: bool = False) -> TraceEventType:
        """Map SDK span to our event types."""
        span_name = getattr(span, 'name', '').lower()

        if 'agent' in span_name:
            return TraceEventType.AGENT_END if is_end else TraceEventType.AGENT_START
        elif 'task' in span_name:
            return TraceEventType.TASK_END if is_end else TraceEventType.TASK_START
        elif 'tool' in span_name:
            return TraceEventType.TOOL_CALL
        elif 'llm' in span_name or 'model' in span_name:
            return TraceEventType.LLM_CALL
        elif 'handoff' in span_name:
            return TraceEventType.HANDOFF
        else:
            return TraceEventType.AGENT_END if is_end else TraceEventType.AGENT_START

    def _extract_agent_name(self, span: Span) -> str:
        """Extract agent name from span."""
        if hasattr(span, 'data') and span.data:
            return span.data.get('agent_name', 'unknown')
        return 'unknown'

    def _extract_span_data(self, span: Span) -> dict[str, Any]:
        """Extract relevant data from span."""
        data = {}

        if hasattr(span, 'data') and span.data:
            # Convert span data to dictionary
            if hasattr(span.data, '__dict__'):
                data = span.data.__dict__.copy()
            else:
                data = dict(span.data)

        # Add span metadata
        data.update({
            'span_name': getattr(span, 'name', ''),
            'start_time': getattr(span, 'start_time', None),
            'end_time': getattr(span, 'end_time', None)
        })

        return data

    def _log_event(self, event: TraceEvent):
        """Log event to Gary-Zero logging system."""
        # Log to Gary-Zero logger if available
        if self.gary_logger:
            self.gary_logger.log(
                type="trace",
                heading=f"Trace Event: {event.event_type.value}",
                content=f"Agent: {event.agent_name}",
                kvps={
                    "trace_id": event.trace_id,
                    "span_id": event.span_id,
                    "duration_ms": event.duration_ms,
                    "success": event.success,
                    "data": event.data
                }
            )

        # Also log to console with color coding
        color = self._get_event_color(event.event_type)
        PrintStyle(font_color=color, padding=True).print(
            f"[TRACE] {event.event_type.value}: {event.agent_name} "
            f"(trace: {event.trace_id[:8]})"
        )

    def _get_event_color(self, event_type: TraceEventType) -> str:
        """Get color for event type."""
        colors = {
            TraceEventType.AGENT_START: "green",
            TraceEventType.AGENT_END: "blue",
            TraceEventType.TASK_START: "cyan",
            TraceEventType.TASK_END: "cyan",
            TraceEventType.TOOL_CALL: "yellow",
            TraceEventType.LLM_CALL: "purple",
            TraceEventType.HANDOFF: "orange",
            TraceEventType.ERROR: "red",
            TraceEventType.GUARDRAIL_VIOLATION: "red"
        }
        return colors.get(event_type, "white")

    def get_trace_events(self, trace_id: str | None = None,
                        limit: int = 100) -> list[TraceEvent]:
        """Get trace events, optionally filtered by trace ID."""
        events = self.trace_events

        if trace_id:
            events = [e for e in events if e.trace_id == trace_id]

        return events[-limit:]


class AgentTracer:
    """Enhanced tracing for agent operations."""

    def __init__(self, gary_logger: Log.Log | None = None):
        self.gary_logger = gary_logger
        self.tracing_processor = GaryZeroTracingProcessor(gary_logger)
        self.active_traces: dict[str, dict[str, Any]] = {}

        # Register our processor with the SDK
        set_trace_processors([self.tracing_processor])

    def start_agent_trace(self, agent_name: str, task_id: str | None = None) -> str:
        """Start tracing for an agent operation."""
        trace_id = str(uuid.uuid4())

        trace_data = {
            "trace_id": trace_id,
            "agent_name": agent_name,
            "task_id": task_id,
            "start_time": datetime.now(UTC),
            "events": [],
            "metadata": {}
        }

        self.active_traces[trace_id] = trace_data

        # Create trace event
        event = TraceEvent(
            trace_id=trace_id,
            event_type=TraceEventType.AGENT_START,
            agent_name=agent_name,
            task_id=task_id,
            data={"operation": "agent_start"}
        )

        trace_data["events"].append(event)
        self._log_trace_event(event)

        return trace_id

    def end_agent_trace(self, trace_id: str, success: bool = True,
                       result: str | None = None, error: str | None = None):
        """End tracing for an agent operation."""
        if trace_id not in self.active_traces:
            return

        trace_data = self.active_traces[trace_id]
        end_time = datetime.now(UTC)
        duration_ms = (end_time - trace_data["start_time"]).total_seconds() * 1000

        event = TraceEvent(
            trace_id=trace_id,
            event_type=TraceEventType.AGENT_END,
            agent_name=trace_data["agent_name"],
            task_id=trace_data["task_id"],
            duration_ms=duration_ms,
            success=success,
            error_message=error,
            data={
                "operation": "agent_end",
                "result": result,
                "total_events": len(trace_data["events"])
            }
        )

        trace_data["events"].append(event)
        trace_data["end_time"] = end_time
        trace_data["duration_ms"] = duration_ms
        trace_data["success"] = success

        self._log_trace_event(event)

        # Move to completed traces
        del self.active_traces[trace_id]

    def add_trace_event(self, trace_id: str, event_type: TraceEventType,
                       data: dict[str, Any]):
        """Add a custom trace event."""
        if trace_id not in self.active_traces:
            return

        trace_data = self.active_traces[trace_id]

        event = TraceEvent(
            trace_id=trace_id,
            event_type=event_type,
            agent_name=trace_data["agent_name"],
            task_id=trace_data["task_id"],
            data=data
        )

        trace_data["events"].append(event)
        self._log_trace_event(event)

    def _log_trace_event(self, event: TraceEvent):
        """Log trace event."""
        if self.gary_logger:
            self.gary_logger.log(
                type="trace",
                heading=f"Agent Trace: {event.event_type.value}",
                content=f"Agent: {event.agent_name}",
                kvps={
                    "trace_id": event.trace_id,
                    "task_id": event.task_id,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data
                }
            )

    def get_trace_summary(self, trace_id: str) -> dict[str, Any] | None:
        """Get summary of a trace."""
        # Check active traces
        if trace_id in self.active_traces:
            trace_data = self.active_traces[trace_id]
            return {
                "trace_id": trace_id,
                "status": "active",
                "agent_name": trace_data["agent_name"],
                "task_id": trace_data["task_id"],
                "start_time": trace_data["start_time"].isoformat(),
                "event_count": len(trace_data["events"]),
                "latest_event": trace_data["events"][-1].event_type.value if trace_data["events"] else None
            }

        # Check completed traces from processor
        events = self.tracing_processor.get_trace_events(trace_id)
        if events:
            return {
                "trace_id": trace_id,
                "status": "completed",
                "agent_name": events[0].agent_name,
                "event_count": len(events),
                "first_event": events[0].timestamp.isoformat(),
                "last_event": events[-1].timestamp.isoformat(),
                "duration_ms": events[-1].duration_ms,
                "success": events[-1].success
            }

        return None

    def get_all_active_traces(self) -> list[dict[str, Any]]:
        """Get summaries of all active traces."""
        return [
            self.get_trace_summary(trace_id)
            for trace_id in self.active_traces.keys()
        ]


class PerformanceMonitor:
    """Monitor agent performance and generate metrics."""

    def __init__(self, tracer: AgentTracer):
        self.tracer = tracer
        self.metrics: dict[str, Any] = {
            "total_operations": 0,
            "successful_operations": 0,
            "average_duration_ms": 0.0,
            "agent_statistics": {},
            "error_rate": 0.0
        }

    def update_metrics(self, trace_events: list[TraceEvent]):
        """Update performance metrics from trace events."""
        if not trace_events:
            return

        # Count operations
        agent_operations = [e for e in trace_events if e.event_type == TraceEventType.AGENT_END]

        self.metrics["total_operations"] += len(agent_operations)
        successful_ops = len([e for e in agent_operations if e.success])
        self.metrics["successful_operations"] += successful_ops

        # Calculate success rate
        if self.metrics["total_operations"] > 0:
            self.metrics["error_rate"] = 1.0 - (self.metrics["successful_operations"] / self.metrics["total_operations"])

        # Calculate average duration
        durations = [e.duration_ms for e in agent_operations if e.duration_ms is not None]
        if durations:
            avg_duration = sum(durations) / len(durations)
            # Moving average
            self.metrics["average_duration_ms"] = (
                self.metrics["average_duration_ms"] * 0.8 + avg_duration * 0.2
            )

        # Update agent-specific statistics
        for event in agent_operations:
            agent_name = event.agent_name
            if agent_name not in self.metrics["agent_statistics"]:
                self.metrics["agent_statistics"][agent_name] = {
                    "operations": 0,
                    "successes": 0,
                    "average_duration_ms": 0.0
                }

            stats = self.metrics["agent_statistics"][agent_name]
            stats["operations"] += 1
            if event.success:
                stats["successes"] += 1

            if event.duration_ms:
                stats["average_duration_ms"] = (
                    stats["average_duration_ms"] * 0.8 + event.duration_ms * 0.2
                )

    def get_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return self.metrics.copy()

    def get_agent_metrics(self, agent_name: str) -> dict[str, Any] | None:
        """Get metrics for a specific agent."""
        return self.metrics["agent_statistics"].get(agent_name)


class LoggingIntegration:
    """Integration between SDK tracing and Gary-Zero logging."""

    def __init__(self, gary_logger: Log.Log):
        self.gary_logger = gary_logger
        self.tracer = AgentTracer(gary_logger)
        self.performance_monitor = PerformanceMonitor(self.tracer)

        # Periodic metrics update
        self._metrics_update_task = None
        self._start_metrics_updates()

    def _start_metrics_updates(self):
        """Start periodic metrics updates."""
        async def update_metrics_periodically():
            while True:
                try:
                    await asyncio.sleep(30)  # Update every 30 seconds
                    recent_events = self.tracer.tracing_processor.get_trace_events(limit=100)
                    self.performance_monitor.update_metrics(recent_events)
                except Exception as e:
                    PrintStyle(font_color="red", padding=True).print(
                        f"[TRACE] Error updating metrics: {e}"
                    )

        self._metrics_update_task = asyncio.create_task(update_metrics_periodically())

    def log_agent_operation(self, agent_name: str, operation: str,
                           data: dict[str, Any]) -> str:
        """Log an agent operation and return trace ID."""
        trace_id = self.tracer.start_agent_trace(agent_name, data.get("task_id"))

        self.gary_logger.log(
            type="agent_operation",
            heading=f"Agent Operation: {operation}",
            content=f"Agent: {agent_name}",
            kvps={
                "trace_id": trace_id,
                "operation": operation,
                "data": data
            }
        )

        return trace_id

    def log_tool_execution(self, trace_id: str, tool_name: str,
                          args: dict[str, Any], result: Any):
        """Log tool execution within a trace."""
        self.tracer.add_trace_event(
            trace_id,
            TraceEventType.TOOL_CALL,
            {
                "tool_name": tool_name,
                "args": args,
                "result": str(result)[:500]  # Truncate long results
            }
        )

        self.gary_logger.log(
            type="tool_execution",
            heading=f"Tool: {tool_name}",
            content=f"Trace: {trace_id[:8]}",
            kvps={
                "tool_name": tool_name,
                "args": args,
                "trace_id": trace_id
            }
        )

    def log_handoff(self, trace_id: str, from_agent: str, to_agent: str,
                   context: dict[str, Any]):
        """Log agent handoff within a trace."""
        self.tracer.add_trace_event(
            trace_id,
            TraceEventType.HANDOFF,
            {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "context": context
            }
        )

        self.gary_logger.log(
            type="handoff",
            heading=f"Handoff: {from_agent} → {to_agent}",
            content=f"Trace: {trace_id[:8]}",
            kvps={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "context": context,
                "trace_id": trace_id
            }
        )

    def get_tracing_status(self) -> dict[str, Any]:
        """Get status of tracing system."""
        return {
            "active_traces": len(self.tracer.active_traces),
            "total_events": len(self.tracer.tracing_processor.trace_events),
            "performance_metrics": self.performance_monitor.get_metrics(),
            "logging_enabled": True
        }

    def cleanup(self):
        """Cleanup resources."""
        if self._metrics_update_task:
            self._metrics_update_task.cancel()


# Global instances
_logging_integration: LoggingIntegration | None = None
_agent_tracer: AgentTracer | None = None


def get_agent_tracer(gary_logger: Log.Log | None = None) -> AgentTracer:
    """Get the global agent tracer instance."""
    global _agent_tracer
    if _agent_tracer is None:
        _agent_tracer = AgentTracer(gary_logger)
    return _agent_tracer


def get_logging_integration(gary_logger: Log.Log) -> LoggingIntegration:
    """Get the global logging integration instance."""
    global _logging_integration
    if _logging_integration is None:
        _logging_integration = LoggingIntegration(gary_logger)
    return _logging_integration


def initialize_tracing(gary_logger: Log.Log | None = None) -> None:
    """Initialize the tracing system."""
    # Initialize tracer
    tracer = get_agent_tracer(gary_logger)

    # Initialize logging integration if logger provided
    if gary_logger:
        integration = get_logging_integration(gary_logger)

    PrintStyle(font_color="green", padding=True).print(
        "Agent tracing system initialized"
    )
