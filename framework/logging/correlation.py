"""
Correlation ID Management for Structured Logging

Provides correlation ID generation, propagation, and context management
for tracking requests across the Gary-Zero system.
"""

import uuid
import threading
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime

# Context variables for correlation tracking
correlation_context: ContextVar[Optional['CorrelationContext']] = ContextVar('correlation_context', default=None)


@dataclass
class CorrelationContext:
    """Context information for correlating logs and traces"""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        result = {
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat()
        }
        
        # Add optional fields if present
        for field_name in ['session_id', 'user_id', 'trace_id', 'span_id', 
                          'parent_span_id', 'operation', 'component']:
            value = getattr(self, field_name)
            if value:
                result[field_name] = value
        
        # Add metadata
        if self.metadata:
            result['metadata'] = self.metadata
            
        return result

    def child_span(self, operation: str, component: Optional[str] = None) -> 'CorrelationContext':
        """Create a child span context"""
        return CorrelationContext(
            request_id=self.request_id,
            session_id=self.session_id,
            user_id=self.user_id,
            trace_id=self.trace_id or str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            operation=operation,
            component=component or self.component,
            metadata=self.metadata.copy()
        )


class CorrelationManager:
    """Manages correlation contexts and IDs throughout the application"""
    
    def __init__(self):
        self._local = threading.local()
        
    def get_current_context(self) -> Optional[CorrelationContext]:
        """Get the current correlation context"""
        return correlation_context.get()
    
    def set_context(self, context: CorrelationContext) -> None:
        """Set the correlation context"""
        correlation_context.set(context)
    
    def clear_context(self) -> None:
        """Clear the correlation context"""
        correlation_context.set(None)
    
    def create_context(
        self,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        **metadata
    ) -> CorrelationContext:
        """Create a new correlation context"""
        return CorrelationContext(
            request_id=request_id or str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            operation=operation,
            component=component,
            metadata=metadata
        )
    
    def get_correlation_data(self) -> Dict[str, Any]:
        """Get correlation data for logging"""
        context = self.get_current_context()
        return context.to_dict() if context else {}
    
    def with_context(self, context: CorrelationContext):
        """Context manager for setting correlation context"""
        return CorrelationContextManager(self, context)


class CorrelationContextManager:
    """Context manager for correlation contexts"""
    
    def __init__(self, manager: CorrelationManager, context: CorrelationContext):
        self.manager = manager
        self.context = context
        self.previous_context = None
    
    def __enter__(self) -> CorrelationContext:
        self.previous_context = self.manager.get_current_context()
        self.manager.set_context(self.context)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.set_context(self.previous_context)


# Global correlation manager instance
correlation_manager = CorrelationManager()


def get_correlation_manager() -> CorrelationManager:
    """Get the global correlation manager"""
    return correlation_manager


def get_current_context() -> Optional[CorrelationContext]:
    """Get the current correlation context"""
    return correlation_manager.get_current_context()


def create_context(**kwargs) -> CorrelationContext:
    """Create a new correlation context"""
    return correlation_manager.create_context(**kwargs)


def with_correlation(
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    operation: Optional[str] = None,
    component: Optional[str] = None,
    **metadata
):
    """Decorator for functions that need correlation context"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = correlation_manager.create_context(
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
                operation=operation or func.__name__,
                component=component,
                **metadata
            )
            
            with correlation_manager.with_context(context):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def ensure_correlation_context(
    operation: Optional[str] = None,
    component: Optional[str] = None
) -> CorrelationContext:
    """Ensure there's a correlation context, creating one if necessary"""
    context = get_current_context()
    
    if not context:
        context = create_context(
            operation=operation,
            component=component
        )
        correlation_manager.set_context(context)
    
    return context


def add_correlation_metadata(**metadata):
    """Add metadata to the current correlation context"""
    context = get_current_context()
    if context:
        context.metadata.update(metadata)


def get_correlation_headers() -> Dict[str, str]:
    """Get HTTP headers for correlation tracking"""
    context = get_current_context()
    if not context:
        return {}
    
    headers = {
        'X-Request-ID': context.request_id,
    }
    
    if context.trace_id:
        headers['X-Trace-ID'] = context.trace_id
    
    if context.span_id:
        headers['X-Span-ID'] = context.span_id
        
    if context.session_id:
        headers['X-Session-ID'] = context.session_id
    
    return headers


def extract_correlation_from_headers(headers: Dict[str, str]) -> Optional[CorrelationContext]:
    """Extract correlation context from HTTP headers"""
    request_id = headers.get('X-Request-ID') or headers.get('x-request-id')
    if not request_id:
        return None
    
    return CorrelationContext(
        request_id=request_id,
        trace_id=headers.get('X-Trace-ID') or headers.get('x-trace-id'),
        span_id=headers.get('X-Span-ID') or headers.get('x-span-id'),
        session_id=headers.get('X-Session-ID') or headers.get('x-session-id'),
    )


# Integration helpers for common frameworks
def fastapi_correlation_middleware():
    """FastAPI middleware for correlation context"""
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class CorrelationMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Extract or create correlation context
            context = extract_correlation_from_headers(dict(request.headers))
            if not context:
                context = create_context(
                    operation=f"{request.method} {request.url.path}",
                    component="api"
                )
            
            # Set context for the request
            with correlation_manager.with_context(context):
                response = await call_next(request)
                
                # Add correlation headers to response
                for key, value in get_correlation_headers().items():
                    response.headers[key] = value
                
                return response
    
    return CorrelationMiddleware


def flask_correlation_middleware():
    """Flask middleware for correlation context"""
    from flask import request, g
    
    def before_request():
        context = extract_correlation_from_headers(dict(request.headers))
        if not context:
            context = create_context(
                operation=f"{request.method} {request.path}",
                component="api"
            )
        
        g.correlation_context = context
        correlation_manager.set_context(context)
    
    def after_request(response):
        # Add correlation headers to response
        for key, value in get_correlation_headers().items():
            response.headers[key] = value
        return response
    
    return before_request, after_request