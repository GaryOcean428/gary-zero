"""
Distributed Tracing and Observability System

Provides comprehensive distributed tracing capabilities:
- Automatic trace context propagation
- Span lifecycle management
- Custom attributes and events
- Integration with external tracing systems
- Performance correlation with metrics
"""

import time
import uuid
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json


class SpanKind(Enum):
    """Types of spans in distributed tracing"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Status codes for spans"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanEvent:
    """An event within a span"""
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Represents a single operation in a distributed trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    kind: SpanKind = SpanKind.INTERNAL
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.span_id:
            self.span_id = str(uuid.uuid4())
            
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute"""
        self.attributes[key] = value
        
    def set_tag(self, key: str, value: str) -> None:
        """Set a span tag"""
        self.tags[key] = value
        
    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        """Add an event to the span"""
        event = SpanEvent(name=name, attributes=attributes or {})
        self.events.append(event)
        
    def set_status(self, status: SpanStatus, description: str = None) -> None:
        """Set the span status"""
        self.status = status
        if description:
            self.attributes["status_description"] = description
            
    def finish(self) -> None:
        """Mark the span as finished"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status.value,
            "kind": self.kind.value,
            "attributes": self.attributes,
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp,
                    "attributes": event.attributes
                }
                for event in self.events
            ],
            "tags": self.tags
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Span':
        """Create span from dictionary"""
        span = cls(
            trace_id=data["trace_id"],
            span_id=data["span_id"],
            parent_span_id=data.get("parent_span_id"),
            operation_name=data["operation_name"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            duration=data.get("duration"),
            status=SpanStatus(data.get("status", "ok")),
            kind=SpanKind(data.get("kind", "internal")),
            attributes=data.get("attributes", {}),
            tags=data.get("tags", {})
        )
        
        # Restore events
        for event_data in data.get("events", []):
            event = SpanEvent(
                name=event_data["name"],
                timestamp=event_data["timestamp"],
                attributes=event_data.get("attributes", {})
            )
            span.events.append(event)
            
        return span


class TraceContext:
    """Thread-local trace context management"""
    
    def __init__(self):
        self._local = threading.local()
        
    def get_current_span(self) -> Optional[Span]:
        """Get the current active span"""
        return getattr(self._local, "current_span", None)
        
    def set_current_span(self, span: Optional[Span]) -> None:
        """Set the current active span"""
        self._local.current_span = span
        
    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID"""
        span = self.get_current_span()
        return span.trace_id if span else None
        
    def get_span_id(self) -> Optional[str]:
        """Get the current span ID"""
        span = self.get_current_span()
        return span.span_id if span else None
        
    def clear(self) -> None:
        """Clear the current trace context"""
        self._local.current_span = None


class DistributedTracer:
    """Main distributed tracing system"""
    
    def __init__(self, 
                 service_name: str = "gary-zero",
                 sample_rate: float = 1.0,
                 max_spans_per_trace: int = 1000,
                 export_timeout: float = 30.0):
        self.service_name = service_name
        self.sample_rate = sample_rate
        self.max_spans_per_trace = max_spans_per_trace
        self.export_timeout = export_timeout
        
        # Context management
        self.context = TraceContext()
        
        # Span storage and management
        self._active_traces: Dict[str, List[Span]] = {}
        self._completed_spans: List[Span] = []
        self._lock = threading.RLock()
        
        # Export configuration
        self._exporters: List[Callable[[List[Span]], None]] = []
        self._running = False
        self._export_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tracer")
        
        # Sampling
        self._sample_counter = 0
        
    def start(self) -> None:
        """Start the tracing system"""
        if self._running:
            return
            
        self._running = True
        
        # Start export thread
        self._export_thread = threading.Thread(
            target=self._export_worker,
            name="trace-export",
            daemon=True
        )
        self._export_thread.start()
        
    def stop(self) -> None:
        """Stop the tracing system"""
        self._running = False
        
        if self._export_thread:
            self._export_thread.join(timeout=5.0)
            
        self._executor.shutdown(wait=True)
        
        # Final export
        self._export_spans()
        
    def start_span(self, 
                   operation_name: str,
                   parent_span: Optional[Span] = None,
                   kind: SpanKind = SpanKind.INTERNAL,
                   attributes: Dict[str, Any] = None,
                   tags: Dict[str, str] = None) -> Span:
        """Start a new span"""
        
        # Check sampling
        if not self._should_sample():
            return self._create_no_op_span(operation_name)
            
        # Determine parent
        if parent_span is None:
            parent_span = self.context.get_current_span()
            
        # Create trace ID
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None
            
        # Create span
        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            kind=kind,
            attributes=attributes or {},
            tags=tags or {}
        )
        
        # Add service information
        span.set_attribute("service.name", self.service_name)
        span.set_attribute("service.version", "0.9.0")
        
        # Store span
        with self._lock:
            if trace_id not in self._active_traces:
                self._active_traces[trace_id] = []
            self._active_traces[trace_id].append(span)
            
            # Limit spans per trace
            if len(self._active_traces[trace_id]) > self.max_spans_per_trace:
                oldest_span = self._active_traces[trace_id].pop(0)
                oldest_span.finish()
                self._completed_spans.append(oldest_span)
                
        return span
        
    def finish_span(self, span: Span) -> None:
        """Finish a span and move it to completed spans"""
        if span is None:
            return
            
        span.finish()
        
        with self._lock:
            # Move from active to completed
            if span.trace_id in self._active_traces:
                try:
                    self._active_traces[span.trace_id].remove(span)
                    if not self._active_traces[span.trace_id]:
                        del self._active_traces[span.trace_id]
                except ValueError:
                    pass  # Span not in active list
                    
            self._completed_spans.append(span)
            
    @contextmanager
    def span(self, 
             operation_name: str,
             kind: SpanKind = SpanKind.INTERNAL,
             attributes: Dict[str, Any] = None,
             tags: Dict[str, str] = None):
        """Context manager for automatic span lifecycle management"""
        span = self.start_span(operation_name, kind=kind, attributes=attributes, tags=tags)
        
        # Set as current span
        previous_span = self.context.get_current_span()
        self.context.set_current_span(span)
        
        try:
            yield span
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.type", type(e).__name__)
            raise
        finally:
            self.finish_span(span)
            self.context.set_current_span(previous_span)
            
    def add_exporter(self, exporter: Callable[[List[Span]], None]) -> None:
        """Add a span exporter"""
        self._exporters.append(exporter)
        
    def get_active_traces(self) -> Dict[str, List[Span]]:
        """Get all active traces"""
        with self._lock:
            return dict(self._active_traces)
            
    def get_completed_spans(self, limit: int = None) -> List[Span]:
        """Get completed spans"""
        with self._lock:
            if limit:
                return self._completed_spans[-limit:]
            return list(self._completed_spans)
            
    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject trace context into a carrier (e.g., HTTP headers)"""
        current_span = self.context.get_current_span()
        if current_span:
            carrier["x-trace-id"] = current_span.trace_id
            carrier["x-span-id"] = current_span.span_id
            
    def extract_context(self, carrier: Dict[str, str]) -> Optional[Span]:
        """Extract trace context from a carrier"""
        trace_id = carrier.get("x-trace-id")
        span_id = carrier.get("x-span-id")
        
        if trace_id and span_id:
            # Create a dummy span to represent the parent context
            return Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=None,
                operation_name="extracted_context"
            )
        return None
        
    def _should_sample(self) -> bool:
        """Determine if this trace should be sampled"""
        if self.sample_rate >= 1.0:
            return True
        if self.sample_rate <= 0.0:
            return False
            
        self._sample_counter += 1
        return (self._sample_counter % int(1.0 / self.sample_rate)) == 0
        
    def _create_no_op_span(self, operation_name: str) -> Span:
        """Create a no-op span for unsampled traces"""
        return Span(
            trace_id="",
            span_id="",
            parent_span_id=None,
            operation_name=operation_name
        )
        
    def _export_worker(self) -> None:
        """Background worker for span export"""
        while self._running:
            time.sleep(self.export_timeout)
            if self._running:
                self._export_spans()
                
    def _export_spans(self) -> None:
        """Export completed spans to configured exporters"""
        if not self._exporters:
            return
            
        with self._lock:
            if not self._completed_spans:
                return
                
            spans_to_export = list(self._completed_spans)
            self._completed_spans.clear()
            
        for exporter in self._exporters:
            try:
                exporter(spans_to_export)
            except Exception as e:
                print(f"Error in span exporter: {e}")


# Convenience decorators
def trace(operation_name: str = None, 
          kind: SpanKind = SpanKind.INTERNAL,
          attributes: Dict[str, Any] = None,
          tags: Dict[str, str] = None):
    """Decorator for automatic function tracing"""
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__qualname__}"
            
        def wrapper(*args, **kwargs):
            # Get the global tracer (would be injected via DI in real usage)
            tracer = get_global_tracer()
            if not tracer:
                return func(*args, **kwargs)
                
            with tracer.span(operation_name, kind=kind, attributes=attributes, tags=tags) as span:
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                span.set_attribute("function.args_count", len(args))
                span.set_attribute("function.kwargs_count", len(kwargs))
                
                result = func(*args, **kwargs)
                
                # Add result info if not sensitive
                if hasattr(result, "__len__") and not isinstance(result, str):
                    span.set_attribute("result.length", len(result))
                    
                return result
                
        return wrapper
    return decorator


# Global tracer instance (would be managed by DI container in production)
_global_tracer: Optional[DistributedTracer] = None


def get_global_tracer() -> Optional[DistributedTracer]:
    """Get the global tracer instance"""
    return _global_tracer


def set_global_tracer(tracer: DistributedTracer) -> None:
    """Set the global tracer instance"""
    global _global_tracer
    _global_tracer = tracer