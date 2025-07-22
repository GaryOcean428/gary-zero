"""
Decorator for requiring approval for high-risk tool operations.

This module provides decorators and utilities to integrate approval workflows
with existing tools and functions.
"""

import asyncio
import functools
import inspect
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from .approval_workflow import ApprovalWorkflow, RiskLevel


# Global approval workflow instance
_global_workflow: Optional[ApprovalWorkflow] = None


def set_global_approval_workflow(workflow: ApprovalWorkflow) -> None:
    """Set the global approval workflow instance."""
    global _global_workflow
    _global_workflow = workflow


def get_global_approval_workflow() -> Optional[ApprovalWorkflow]:
    """Get the global approval workflow instance."""
    return _global_workflow


def require_approval(
    action_type: str,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    description: Optional[str] = None,
    timeout: Optional[int] = None,
    extract_user_id: Optional[Callable] = None
):
    """
    Decorator to require approval for function execution.
    
    Args:
        action_type: Type of action being performed
        risk_level: Risk level of the action
        description: Description of the action (uses function name if None)
        timeout: Approval timeout in seconds
        extract_user_id: Function to extract user_id from function args/kwargs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            workflow = get_global_approval_workflow()
            if not workflow:
                # No approval workflow configured, allow execution
                return await func(*args, **kwargs)
            
            # Extract user ID
            user_id = _extract_user_id(extract_user_id, args, kwargs)
            if not user_id:
                raise ValueError("Could not determine user_id for approval request")
            
            # Create action description
            action_desc = description or f"Execute {func.__name__}"
            
            # Extract parameters for approval request
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Filter out sensitive parameters
            filtered_params = {}
            for name, value in bound_args.arguments.items():
                if not _is_sensitive_param(name, value):
                    filtered_params[name] = str(value)[:200]  # Truncate for security
            
            # Request approval
            try:
                approved = await workflow.request_approval(
                    user_id=user_id,
                    action_type=action_type,
                    action_description=action_desc,
                    parameters=filtered_params,
                    timeout_override=timeout
                )
                
                if not approved:
                    raise PermissionError(f"Approval denied for {action_type}")
                
                # Execute the function
                return await func(*args, **kwargs)
                
            except TimeoutError:
                raise TimeoutError(f"Approval request for {action_type} timed out")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert sync function to async
            async def async_func():
                return func(*args, **kwargs)
            
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _extract_user_id(extract_func: Optional[Callable], args: tuple, kwargs: dict) -> Optional[str]:
    """Extract user ID from function arguments."""
    if extract_func:
        return extract_func(args, kwargs)
    
    # Default extraction strategies
    
    # Look for user_id in kwargs
    if 'user_id' in kwargs:
        return kwargs['user_id']
    
    # Look for user_id in first few args (common pattern)
    for arg in args[:3]:
        if isinstance(arg, str) and len(arg) > 3:
            return arg
    
    # Look for objects with user_id attribute
    for arg in args:
        if hasattr(arg, 'user_id'):
            return getattr(arg, 'user_id')
        if hasattr(arg, 'id'):
            return getattr(arg, 'id')
    
    return None


def _is_sensitive_param(name: str, value: Any) -> bool:
    """Check if a parameter contains sensitive information."""
    sensitive_names = ['password', 'secret', 'key', 'token', 'credential', 'auth']
    name_lower = name.lower()
    
    if any(sensitive in name_lower for sensitive in sensitive_names):
        return True
    
    # Check if value looks like a secret (long string without spaces)
    if isinstance(value, str) and len(value) > 20 and ' ' not in value:
        return True
    
    return False


class ApprovalRequired:
    """Class-based decorator for methods that require approval."""
    
    def __init__(
        self,
        action_type: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        description: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.action_type = action_type
        self.risk_level = risk_level
        self.description = description
        self.timeout = timeout
    
    def __call__(self, func: Callable) -> Callable:
        return require_approval(
            action_type=self.action_type,
            risk_level=self.risk_level,
            description=self.description,
            timeout=self.timeout
        )(func)


def approval_context(user_id: str, workflow: Optional[ApprovalWorkflow] = None):
    """
    Context manager for setting approval context.
    
    Usage:
        async with approval_context("user123"):
            await some_function_that_requires_approval()
    """
    return ApprovalContext(user_id, workflow)


class ApprovalContext:
    """Context manager for approval operations."""
    
    def __init__(self, user_id: str, workflow: Optional[ApprovalWorkflow] = None):
        self.user_id = user_id
        self.workflow = workflow
        self.previous_workflow = None
    
    async def __aenter__(self):
        if self.workflow:
            global _global_workflow
            self.previous_workflow = _global_workflow
            _global_workflow = self.workflow
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.workflow and self.previous_workflow is not None:
            global _global_workflow
            _global_workflow = self.previous_workflow


# Tool integration helpers

def make_tool_approval_aware(
    tool_class,
    action_type: str,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    method_name: str = "execute"
):
    """
    Make an existing tool class approval-aware by wrapping its execute method.
    
    Args:
        tool_class: The tool class to modify
        action_type: Action type for approval requests
        risk_level: Risk level for the action
        method_name: Name of the method to wrap (default: "execute")
    """
    original_method = getattr(tool_class, method_name)
    
    wrapped_method = require_approval(
        action_type=action_type,
        risk_level=risk_level,
        description=f"Execute {tool_class.__name__}"
    )(original_method)
    
    setattr(tool_class, method_name, wrapped_method)
    return tool_class


async def request_batch_approval(
    user_id: str,
    actions: list[dict],
    workflow: Optional[ApprovalWorkflow] = None
) -> dict[str, bool]:
    """
    Request approval for multiple actions at once.
    
    Args:
        user_id: User requesting approval
        actions: List of action dictionaries with keys: action_type, description, parameters
        workflow: Approval workflow to use (uses global if None)
    
    Returns:
        Dictionary mapping action indices to approval results
    """
    if not workflow:
        workflow = get_global_approval_workflow()
        if not workflow:
            raise ValueError("No approval workflow available")
    
    # Submit all approval requests
    tasks = []
    for i, action in enumerate(actions):
        task = workflow.request_approval(
            user_id=user_id,
            action_type=action['action_type'],
            action_description=action['description'],
            parameters=action.get('parameters', {})
        )
        tasks.append((i, task))
    
    # Wait for all approvals
    results = {}
    for i, task in tasks:
        try:
            approved = await task
            results[str(i)] = approved
        except (TimeoutError, PermissionError):
            results[str(i)] = False
    
    return results


def create_approval_middleware(workflow: ApprovalWorkflow):
    """
    Create middleware function for web frameworks that require approval.
    
    This can be used with FastAPI, Flask, etc. to require approval for certain endpoints.
    """
    async def approval_middleware(request, call_next):
        # Extract user from request (implementation depends on auth system)
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            return {"error": "No user context for approval"}
        
        # Check if this endpoint requires approval
        endpoint_path = request.url.path
        if _endpoint_requires_approval(endpoint_path):
            try:
                approved = await workflow.request_approval(
                    user_id=user_id,
                    action_type="api_endpoint",
                    action_description=f"Access {endpoint_path}",
                    parameters={"path": endpoint_path, "method": request.method}
                )
                
                if not approved:
                    return {"error": "API access denied"}
                    
            except TimeoutError:
                return {"error": "Approval request timed out"}
        
        response = await call_next(request)
        return response
    
    return approval_middleware


def _endpoint_requires_approval(path: str) -> bool:
    """Check if an API endpoint requires approval."""
    high_risk_patterns = [
        '/admin/',
        '/execute/',
        '/delete/',
        '/upload/',
        '/system/'
    ]
    
    return any(pattern in path for pattern in high_risk_patterns)