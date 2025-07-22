"""Security framework for Gary-Zero.

This module provides comprehensive security features including input validation,
rate limiting, authentication, audit logging, and approval workflows.
"""

from .input_validator import InputValidator, ValidationError
from .rate_limiter import RateLimiter, RateLimitExceeded, RateLimitConfig, RateLimitStrategy
from .audit_logger import AuditLogger, AuditEvent, AuditEventType, AuditLevel
from .sanitizer import ContentSanitizer
from .approval_workflow import (
    ApprovalWorkflow, ApprovalRequest, ActionDefinition, 
    RiskLevel, ApprovalStatus, UserRole, ApprovalPolicy
)
from .approval_decorators import (
    require_approval, ApprovalRequired, approval_context,
    set_global_approval_workflow, get_global_approval_workflow,
    make_tool_approval_aware, request_batch_approval
)
from .approval_config import (
    ApprovalConfigManager, get_config_manager, setup_approval_workflow_from_config
)

__all__ = [
    'InputValidator',
    'ValidationError', 
    'RateLimiter',
    'RateLimitExceeded',
    'RateLimitConfig',
    'RateLimitStrategy',
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditLevel',
    'ContentSanitizer',
    'ApprovalWorkflow',
    'ApprovalRequest',
    'ActionDefinition',
    'RiskLevel',
    'ApprovalStatus',
    'UserRole',
    'ApprovalPolicy',
    'require_approval',
    'ApprovalRequired',
    'approval_context',
    'set_global_approval_workflow',
    'get_global_approval_workflow',
    'make_tool_approval_aware',
    'request_batch_approval',
    'ApprovalConfigManager',
    'get_config_manager',
    'setup_approval_workflow_from_config',
]