"""
Structured Logging System for Gary-Zero
Implementing comprehensive observability with correlation IDs and structured data
"""

import logging
import json
import time
import uuid
import sys
from typing import Any, Dict, Optional, List, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timezone
from contextvars import ContextVar
import traceback
import os
from pathlib import Path

# Context variables for correlation tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEvent(str, Enum):
    """Standard log event types"""
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    MODEL_REQUEST = "model.request"
    MODEL_RESPONSE = "model.response"
    MODEL_ERROR = "model.error"
    DATABASE_QUERY = "database.query"
    DATABASE_ERROR = "database.error"
    SECURITY_VIOLATION = "security.violation"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    USER_ACTION = "user.action"
    INTEGRATION_CALL = "integration.call"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_END = "workflow.end"
    ERROR_OCCURRED = "error.occurred"


class StructuredLogRecord(BaseModel):
    """Structured log record format"""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    level: LogLevel
    message: str
    event: Optional[LogEvent] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    service: str = "gary-zero"
    component: Optional[str] = None
    function: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    
    # Request/Response tracking
    request_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    
    # Error tracking
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Custom data
    data: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # Performance metrics
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        record.session_id = session_id_var.get()
        record.user_id = user_id_var.get()
        return True


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str = "gary-zero"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Build structured log record
        log_data = StructuredLogRecord(
            level=LogLevel(record.levelname),
            message=record.getMessage(),
            service=self.service_name,
            component=getattr(record, 'component', None),
            function=getattr(record, 'funcName', None),
            file=getattr(record, 'filename', None),
            line=getattr(record, 'lineno', None),
            correlation_id=getattr(record, 'correlation_id', None),
            session_id=getattr(record, 'session_id', None),
            user_id=getattr(record, 'user_id', None),
            event=getattr(record, 'event', None),
            request_id=getattr(record, 'request_id', None),
            method=getattr(record, 'method', None),
            path=getattr(record, 'path', None),
            status_code=getattr(record, 'status_code', None),
            duration_ms=getattr(record, 'duration_ms', None),
            error_type=getattr(record, 'error_type', None),
            error_code=getattr(record, 'error_code', None),
            data=getattr(record, 'extra_data', {}),
            tags=getattr(record, 'tags', [])
        )
        
        # Add exception info if present
        if record.exc_info:
            log_data.error_type = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_data.stack_trace = traceback.format_exception(*record.exc_info)
        
        # Add system metrics if available
        try:
            import psutil
            process = psutil.Process()
            log_data.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            log_data.cpu_usage = process.cpu_percent()
        except ImportError:
            pass
        
        return json.dumps(log_data.model_dump(exclude_none=True), default=str)


class StructuredLogger:
    """
    Enhanced structured logger for Gary-Zero
    """
    
    def __init__(self, name: str, service_name: str = "gary-zero"):
        self.name = name
        self.service_name = service_name
        self.logger = logging.getLogger(name)
        
        # Set up structured logging if not already configured
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup structured logging configuration"""
        
        # Create formatter
        formatter = StructuredFormatter(self.service_name)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(CorrelationIdFilter())
        
        # Create file handler if log directory exists
        log_dir = Path("logs")
        if log_dir.exists() or os.getenv("CREATE_LOG_FILES", "false").lower() == "true":
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_dir / f"{self.service_name}.log")
            file_handler.setFormatter(formatter)
            file_handler.addFilter(CorrelationIdFilter())
            self.logger.addHandler(file_handler)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
    
    def _log(self, level: LogLevel, message: str, event: Optional[LogEvent] = None, **kwargs):
        """Internal logging method"""
        
        # Extract special kwargs
        extra_data = kwargs.pop('data', {})
        tags = kwargs.pop('tags', [])
        error_code = kwargs.pop('error_code', None)
        component = kwargs.pop('component', None)
        
        # Create extra dict for logger
        extra = {
            'event': event,
            'extra_data': {**extra_data, **kwargs},
            'tags': tags,
            'error_code': error_code,
            'component': component
        }
        
        # Log with appropriate level
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def debug(self, message: str, event: Optional[LogEvent] = None, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, event, **kwargs)
    
    def info(self, message: str, event: Optional[LogEvent] = None, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, event, **kwargs)
    
    def warning(self, message: str, event: Optional[LogEvent] = None, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, event, **kwargs)
    
    def error(self, message: str, event: Optional[LogEvent] = None, 
              error: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        
        self._log(LogLevel.ERROR, message, event, **kwargs)
        
        if error:
            self.logger.error(message, exc_info=error, extra={
                'event': event,
                'extra_data': kwargs,
                'error_code': kwargs.get('error_code')
            })
    
    def critical(self, message: str, event: Optional[LogEvent] = None, 
                 error: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        
        self._log(LogLevel.CRITICAL, message, event, **kwargs)
        
        if error:
            self.logger.critical(message, exc_info=error, extra={
                'event': event,
                'extra_data': kwargs
            })
    
    # Convenience methods for common events
    def log_api_request(self, method: str, path: str, request_id: Optional[str] = None, **data):
        """Log API request"""
        self.info(
            f"{method} {path}",
            event=LogEvent.API_REQUEST,
            method=method,
            path=path,
            request_id=request_id,
            data=data
        )
    
    def log_api_response(self, method: str, path: str, status_code: int, 
                        duration_ms: float, request_id: Optional[str] = None, **data):
        """Log API response"""
        self.info(
            f"{method} {path} {status_code} ({duration_ms:.2f}ms)",
            event=LogEvent.API_RESPONSE,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            data=data
        )
    
    def log_model_request(self, model: str, provider: str, **data):
        """Log model request"""
        self.info(
            f"Model request: {provider}/{model}",
            event=LogEvent.MODEL_REQUEST,
            model=model,
            provider=provider,
            data=data
        )
    
    def log_model_response(self, model: str, provider: str, duration_ms: float, 
                          tokens_used: Optional[int] = None, **data):
        """Log model response"""
        self.info(
            f"Model response: {provider}/{model} ({duration_ms:.2f}ms)",
            event=LogEvent.MODEL_RESPONSE,
            model=model,
            provider=provider,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            data=data
        )
    
    def log_auth_event(self, event_type: str, user_email: Optional[str] = None, 
                      success: bool = True, **data):
        """Log authentication event"""
        event = LogEvent.AUTH_LOGIN if success else LogEvent.AUTH_FAILED
        level = LogLevel.INFO if success else LogLevel.WARNING
        
        self._log(
            level,
            f"Authentication {event_type}: {user_email}" if user_email else f"Authentication {event_type}",
            event=event,
            user_email=user_email,
            success=success,
            data=data
        )
    
    def log_security_violation(self, violation_type: str, details: str, **data):
        """Log security violation"""
        self.warning(
            f"Security violation: {violation_type} - {details}",
            event=LogEvent.SECURITY_VIOLATION,
            violation_type=violation_type,
            data=data
        )
    
    def log_workflow_start(self, workflow_name: str, **data):
        """Log workflow start"""
        self.info(
            f"Workflow started: {workflow_name}",
            event=LogEvent.WORKFLOW_START,
            workflow_name=workflow_name,
            data=data
        )
    
    def log_workflow_end(self, workflow_name: str, duration_ms: float, 
                        success: bool = True, **data):
        """Log workflow end"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "completed" if success else "failed"
        
        self._log(
            level,
            f"Workflow {status}: {workflow_name} ({duration_ms:.2f}ms)",
            event=LogEvent.WORKFLOW_END,
            workflow_name=workflow_name,
            duration_ms=duration_ms,
            success=success,
            data=data
        )


# Context managers for correlation tracking
class CorrelationContext:
    """Context manager for correlation ID tracking"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.token = None
    
    def __enter__(self):
        self.token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        correlation_id_var.reset(self.token)


class UserContext:
    """Context manager for user tracking"""
    
    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.user_token = None
        self.session_token = None
    
    def __enter__(self):
        self.user_token = user_id_var.set(self.user_id)
        if self.session_id:
            self.session_token = session_id_var.set(self.session_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        user_id_var.reset(self.user_token)
        if self.session_token:
            session_id_var.reset(self.session_token)


# Performance monitoring decorator
def log_performance(logger: StructuredLogger, operation_name: str):
    """Decorator to log performance metrics"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    event=LogEvent.WORKFLOW_END,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Operation failed: {operation_name}",
                    event=LogEvent.ERROR_OCCURRED,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    error=e
                )
                
                raise
        
        return wrapper
    return decorator


# Global logger factory
_loggers: Dict[str, StructuredLogger] = {}

def get_logger(name: str, service_name: str = "gary-zero") -> StructuredLogger:
    """Get or create a structured logger"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, service_name)
    return _loggers[name]


# Configure root logging
def configure_logging(level: str = "INFO", service_name: str = "gary-zero"):
    """Configure global logging settings"""
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Create default structured logger
    default_logger = get_logger("gary-zero", service_name)
    
    return default_logger


# Convenience functions
def with_correlation_id(correlation_id: Optional[str] = None):
    """Context manager for correlation ID"""
    return CorrelationContext(correlation_id)


def with_user_context(user_id: str, session_id: Optional[str] = None):
    """Context manager for user context"""
    return UserContext(user_id, session_id)


# Example usage and configuration
if __name__ == "__main__":
    # Configure logging
    logger = configure_logging("INFO", "gary-zero")
    
    # Example usage
    with with_correlation_id() as corr_id:
        logger.info("System starting up", event=LogEvent.SYSTEM_STARTUP)
        
        with with_user_context("user123", "session456"):
            logger.log_api_request("GET", "/api/health", request_id="req789")
            logger.log_api_response("GET", "/api/health", 200, 15.5, request_id="req789")
            
            try:
                raise ValueError("Example error")
            except Exception as e:
                logger.error("An error occurred", event=LogEvent.ERROR_OCCURRED, error=e)