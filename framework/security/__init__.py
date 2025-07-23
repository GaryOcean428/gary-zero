"""Security framework for Gary-Zero.

This module provides comprehensive security features including input validation,
rate limiting, authentication, audit logging, and approval workflows.
"""

from .approval_config import (
    ApprovalConfigManager,
    get_config_manager,
    setup_approval_workflow_from_config,
)
from .approval_decorators import (
    ApprovalRequired,
    approval_context,
    get_global_approval_workflow,
    make_tool_approval_aware,
    request_batch_approval,
    require_approval,
    set_global_approval_workflow,
)
from .approval_workflow import (
    ActionDefinition,
    ApprovalPolicy,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalWorkflow,
    RiskLevel,
    UserRole,
)
from .audit_logger import AuditEvent, AuditEventType, AuditLevel, AuditLogger
from .input_validator import InputValidator, ValidationError
from .rate_limiter import RateLimitConfig, RateLimiter, RateLimitExceeded, RateLimitStrategy
from .sanitizer import ContentSanitizer

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
