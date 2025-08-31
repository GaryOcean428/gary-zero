"""
Approval workflow system for high-risk actions in Gary Zero.

This module provides a comprehensive approval framework that requires explicit user
confirmation for sensitive or irreversible operations while maintaining detailed
audit logs and role-based controls.
"""

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .audit_logger import AuditLevel, AuditLogger


class RiskLevel(Enum):
    """Risk levels for actions requiring approval."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(Enum):
    """Status of approval requests."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class UserRole(Enum):
    """User roles for role-based access control."""

    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SUBORDINATE_AGENT = "subordinate_agent"


class ApprovalPolicy(Enum):
    """Approval policies for different scenarios."""

    ALWAYS_ASK = "always_ask"
    ASK_ONCE = "ask_once"
    NEVER_ASK = "never_ask"
    ROLE_BASED = "role_based"


@dataclass
class ActionDefinition:
    """Definition of an action that may require approval."""

    action_type: str
    risk_level: RiskLevel
    description: str
    required_roles: list[UserRole]
    approval_policy: ApprovalPolicy = ApprovalPolicy.ALWAYS_ASK
    timeout_seconds: int = 300  # 5 minutes default
    metadata: dict[str, Any] | None = None


@dataclass
class ApprovalRequest:
    """A request for user approval of a high-risk action."""

    request_id: str
    user_id: str
    action_type: str
    action_description: str
    parameters: dict[str, Any]
    risk_level: RiskLevel
    status: ApprovalStatus
    created_at: float
    expires_at: float
    approved_at: float | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert approval request to dictionary."""
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        data["status"] = self.status.value
        data["created_at_iso"] = datetime.fromtimestamp(
            self.created_at, tz=UTC
        ).isoformat()
        data["expires_at_iso"] = datetime.fromtimestamp(
            self.expires_at, tz=UTC
        ).isoformat()
        if self.approved_at:
            data["approved_at_iso"] = datetime.fromtimestamp(
                self.approved_at, tz=UTC
            ).isoformat()
        return data

    def to_json(self) -> str:
        """Convert approval request to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class ApprovalWorkflow:
    """Main approval workflow system for high-risk actions."""

    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit_logger = audit_logger or AuditLogger()

        # Storage for requests and configurations
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.completed_requests: dict[str, ApprovalRequest] = {}
        self.action_definitions: dict[str, ActionDefinition] = {}
        self.user_roles: dict[str, UserRole] = {}
        self.approval_cache: dict[str, dict[str, float]] = (
            {}
        )  # user_id -> {action_type: timestamp}

        # Configuration
        self.global_timeout = 300  # 5 minutes default
        self.max_pending_requests = 100
        self.cache_duration = 3600  # 1 hour for ask_once policy

        # Callbacks for UI integration
        self.approval_request_callback: Callable | None = None
        self.approval_response_callback: Callable | None = None

        # Initialize default high-risk actions
        self._initialize_default_actions()

    def _initialize_default_actions(self):
        """Initialize default high-risk action definitions."""
        default_actions = [
            ActionDefinition(
                action_type="file_write",
                risk_level=RiskLevel.MEDIUM,
                description="Write or modify files",
                required_roles=[UserRole.OWNER, UserRole.ADMIN, UserRole.USER],
                approval_policy=ApprovalPolicy.ASK_ONCE,
                timeout_seconds=120,
            ),
            ActionDefinition(
                action_type="file_delete",
                risk_level=RiskLevel.HIGH,
                description="Delete files or directories",
                required_roles=[UserRole.OWNER, UserRole.ADMIN],
                approval_policy=ApprovalPolicy.ALWAYS_ASK,
                timeout_seconds=300,
            ),
            ActionDefinition(
                action_type="shell_command",
                risk_level=RiskLevel.HIGH,
                description="Execute shell commands",
                required_roles=[UserRole.OWNER, UserRole.ADMIN],
                approval_policy=ApprovalPolicy.ALWAYS_ASK,
                timeout_seconds=180,
            ),
            ActionDefinition(
                action_type="external_api_call",
                risk_level=RiskLevel.MEDIUM,
                description="Make external API calls",
                required_roles=[UserRole.OWNER, UserRole.ADMIN, UserRole.USER],
                approval_policy=ApprovalPolicy.ASK_ONCE,
                timeout_seconds=120,
            ),
            ActionDefinition(
                action_type="computer_control",
                risk_level=RiskLevel.CRITICAL,
                description="Control desktop/GUI automation",
                required_roles=[UserRole.OWNER],
                approval_policy=ApprovalPolicy.ALWAYS_ASK,
                timeout_seconds=300,
            ),
            ActionDefinition(
                action_type="code_execution",
                risk_level=RiskLevel.HIGH,
                description="Execute code in containers or environments",
                required_roles=[UserRole.OWNER, UserRole.ADMIN],
                approval_policy=ApprovalPolicy.ALWAYS_ASK,
                timeout_seconds=240,
            ),
            ActionDefinition(
                action_type="payment_transaction",
                risk_level=RiskLevel.CRITICAL,
                description="Process financial transactions",
                required_roles=[UserRole.OWNER],
                approval_policy=ApprovalPolicy.ALWAYS_ASK,
                timeout_seconds=600,
            ),
            ActionDefinition(
                action_type="config_change",
                risk_level=RiskLevel.MEDIUM,
                description="Modify system configuration",
                required_roles=[UserRole.OWNER, UserRole.ADMIN],
                approval_policy=ApprovalPolicy.ASK_ONCE,
                timeout_seconds=180,
            ),
        ]

        for action in default_actions:
            self.action_definitions[action.action_type] = action

    def set_user_role(self, user_id: str, role: UserRole) -> None:
        """Set the role for a user."""
        self.user_roles[user_id] = role

    def get_user_role(self, user_id: str) -> UserRole:
        """Get the role for a user, defaulting to USER."""
        return self.user_roles.get(user_id, UserRole.USER)

    def register_action(self, action_definition: ActionDefinition) -> None:
        """Register a new action type that may require approval."""
        self.action_definitions[action_definition.action_type] = action_definition

    def configure_action(self, action_type: str, **kwargs) -> None:
        """Update configuration for an existing action type."""
        if action_type not in self.action_definitions:
            raise ValueError(f"Action type '{action_type}' not registered")

        action = self.action_definitions[action_type]
        for key, value in kwargs.items():
            if hasattr(action, key):
                setattr(action, key, value)

    def set_approval_callback(
        self, callback: Callable[[ApprovalRequest], None]
    ) -> None:
        """Set callback for when approval is requested."""
        self.approval_request_callback = callback

    def set_response_callback(
        self, callback: Callable[[ApprovalRequest, bool], None]
    ) -> None:
        """Set callback for when approval response is received."""
        self.approval_response_callback = callback

    async def request_approval(
        self,
        user_id: str,
        action_type: str,
        action_description: str,
        parameters: dict[str, Any],
        timeout_override: int | None = None,
    ) -> bool:
        """
        Request approval for a high-risk action.

        Returns True if approved, False if rejected, raises TimeoutError if expired.
        """
        # Check if action is registered
        if action_type not in self.action_definitions:
            await self.audit_logger.log_security_violation(
                f"Attempted approval request for unregistered action: {action_type}",
                AuditLevel.WARNING,
                user_id=user_id,
            )
            return False

        action_def = self.action_definitions[action_type]
        user_role = self.get_user_role(user_id)

        # Check role-based permissions
        if user_role not in action_def.required_roles:
            await self.audit_logger.log_security_violation(
                f"User {user_id} (role: {user_role.value}) not authorized for action: {action_type}",
                AuditLevel.WARNING,
                user_id=user_id,
            )
            return False

        # Check approval policy
        if action_def.approval_policy == ApprovalPolicy.NEVER_ASK:
            await self._log_approval_decision(
                user_id,
                action_type,
                True,
                "system",
                "auto-approved",
                "Auto-approved by policy",
            )
            return True

        # Check ask_once cache
        if action_def.approval_policy == ApprovalPolicy.ASK_ONCE:
            cache_key = f"{user_id}:{action_type}"
            if cache_key in self.approval_cache:
                last_approval = self.approval_cache[cache_key]
                if time.time() - last_approval < self.cache_duration:
                    await self._log_approval_decision(
                        user_id,
                        action_type,
                        True,
                        "system",
                        "cached",
                        "Cached approval",
                    )
                    return True

        # Create approval request
        request_id = str(uuid.uuid4())
        timeout = timeout_override or action_def.timeout_seconds

        request = ApprovalRequest(
            request_id=request_id,
            user_id=user_id,
            action_type=action_type,
            action_description=action_description,
            parameters=parameters,
            risk_level=action_def.risk_level,
            status=ApprovalStatus.PENDING,
            created_at=time.time(),
            expires_at=time.time() + timeout,
            metadata={"timeout": timeout},
        )

        self.pending_requests[request_id] = request

        # Clean up old requests
        await self._cleanup_expired_requests()

        # Log approval request
        await self.audit_logger.log_approval_request(
            user_id=user_id,
            action_type=action_type,
            risk_level=action_def.risk_level.value,
            request_id=request_id,
            metadata={"timeout": timeout},
        )

        # Trigger callback if set
        if self.approval_request_callback:
            try:
                self.approval_request_callback(request)
            except Exception as e:
                await self.audit_logger.log_error(
                    f"Approval callback error: {e}", "callback_error", user_id=user_id
                )

        # Wait for approval or timeout
        return await self._wait_for_approval(request_id)

    async def approve_request(
        self, request_id: str, approver_id: str, approval_note: str | None = None
    ) -> bool:
        """Approve a pending request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]

        # Check if request expired
        if time.time() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return False

        # Update request
        request.status = ApprovalStatus.APPROVED
        request.approved_at = time.time()
        request.approved_by = approver_id
        if approval_note:
            request.metadata = request.metadata or {}
            request.metadata["approval_note"] = approval_note

        # Move to completed requests
        self.completed_requests[request_id] = request
        del self.pending_requests[request_id]

        # Update cache for ask_once policy
        action_def = self.action_definitions.get(request.action_type)
        if action_def and action_def.approval_policy == ApprovalPolicy.ASK_ONCE:
            cache_key = f"{request.user_id}:{request.action_type}"
            self.approval_cache[cache_key] = time.time()

        # Log approval decision
        await self._log_approval_decision(
            request.user_id,
            request.action_type,
            True,
            approver_id,
            request_id,
            approval_note,
        )

        # Trigger callback if set
        if self.approval_response_callback:
            try:
                self.approval_response_callback(request, True)
            except Exception as e:
                await self.audit_logger.log_error(
                    f"Approval response callback error: {e}",
                    "callback_error",
                    user_id=request.user_id,
                )

        return True

    async def reject_request(
        self, request_id: str, rejector_id: str, rejection_reason: str | None = None
    ) -> bool:
        """Reject a pending request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]

        # Update request
        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejector_id
        request.rejection_reason = rejection_reason or "No reason provided"

        # Move to completed requests
        self.completed_requests[request_id] = request
        del self.pending_requests[request_id]

        # Log rejection decision
        await self._log_approval_decision(
            request.user_id,
            request.action_type,
            False,
            rejector_id,
            request_id,
            rejection_reason,
        )

        # Trigger callback if set
        if self.approval_response_callback:
            try:
                self.approval_response_callback(request, False)
            except Exception as e:
                await self.audit_logger.log_error(
                    f"Approval response callback error: {e}",
                    "callback_error",
                    user_id=request.user_id,
                )

        return True

    async def _wait_for_approval(self, request_id: str) -> bool:
        """Wait for approval decision or timeout."""
        while request_id in self.pending_requests:
            request = self.pending_requests[request_id]

            # Check for timeout
            if time.time() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                self.completed_requests[request_id] = request
                del self.pending_requests[request_id]

                await self._log_approval_decision(
                    request.user_id,
                    request.action_type,
                    False,
                    "system",
                    request_id,
                    "Request expired",
                )

                raise TimeoutError(f"Approval request {request_id} expired")

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

        # Request was completed, check if it was approved
        if request_id in self.completed_requests:
            request = self.completed_requests[request_id]
            return request.status == ApprovalStatus.APPROVED

        return False

    async def _cleanup_expired_requests(self):
        """Clean up expired pending requests."""
        current_time = time.time()
        expired_ids = []

        for request_id, request in self.pending_requests.items():
            if current_time > request.expires_at:
                expired_ids.append(request_id)

        for request_id in expired_ids:
            request = self.pending_requests[request_id]
            request.status = ApprovalStatus.EXPIRED
            self.completed_requests[request_id] = request
            del self.pending_requests[request_id]

            await self._log_approval_decision(
                request.user_id,
                request.action_type,
                False,
                "system",
                request_id,
                "Request expired during cleanup",
            )

    async def _log_approval_decision(
        self,
        user_id: str,
        action_type: str,
        approved: bool,
        approver_id: str,
        request_id: str,
        reason: str | None = None,
    ):
        """Log approval decision to audit log."""
        await self.audit_logger.log_approval_decision(
            user_id=user_id,
            action_type=action_type,
            approved=approved,
            approver_id=approver_id,
            request_id=request_id,
            reason=reason,
        )

    def get_pending_requests(self, user_id: str | None = None) -> list[ApprovalRequest]:
        """Get pending approval requests, optionally filtered by user."""
        requests = list(self.pending_requests.values())
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        return sorted(requests, key=lambda r: r.created_at)

    def get_request_by_id(self, request_id: str) -> ApprovalRequest | None:
        """Get a specific approval request by ID."""
        return self.pending_requests.get(request_id) or self.completed_requests.get(
            request_id
        )

    async def cancel_request(self, request_id: str, canceller_id: str) -> bool:
        """Cancel a pending approval request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]
        request.status = ApprovalStatus.CANCELLED
        request.approved_by = canceller_id

        self.completed_requests[request_id] = request
        del self.pending_requests[request_id]

        await self._log_approval_decision(
            request.user_id,
            request.action_type,
            False,
            canceller_id,
            request_id,
            "Request cancelled",
        )

        return True

    def clear_approval_cache(
        self, user_id: str | None = None, action_type: str | None = None
    ):
        """Clear approval cache entries."""
        if user_id and action_type:
            cache_key = f"{user_id}:{action_type}"
            self.approval_cache.pop(cache_key, None)
        elif user_id:
            # Clear all entries for user
            keys_to_remove = [
                k for k in self.approval_cache.keys() if k.startswith(f"{user_id}:")
            ]
            for key in keys_to_remove:
                del self.approval_cache[key]
        else:
            # Clear all cache
            self.approval_cache.clear()

    def get_approval_statistics(self) -> dict[str, Any]:
        """Get statistics about approval requests."""
        completed = list(self.completed_requests.values())
        pending = list(self.pending_requests.values())

        stats = {
            "total_requests": len(completed) + len(pending),
            "pending_requests": len(pending),
            "completed_requests": len(completed),
            "approved_requests": len(
                [r for r in completed if r.status == ApprovalStatus.APPROVED]
            ),
            "rejected_requests": len(
                [r for r in completed if r.status == ApprovalStatus.REJECTED]
            ),
            "expired_requests": len(
                [r for r in completed if r.status == ApprovalStatus.EXPIRED]
            ),
            "cancelled_requests": len(
                [r for r in completed if r.status == ApprovalStatus.CANCELLED]
            ),
            "approval_rate": 0.0,
            "average_response_time": 0.0,
            "requests_by_action_type": {},
            "requests_by_risk_level": {},
        }

        # Calculate approval rate
        approved = stats["approved_requests"]
        total_decided = (
            approved + stats["rejected_requests"] + stats["expired_requests"]
        )
        if total_decided > 0:
            stats["approval_rate"] = approved / total_decided

        # Calculate average response time
        response_times = []
        for request in completed:
            if request.approved_at and request.status == ApprovalStatus.APPROVED:
                response_times.append(request.approved_at - request.created_at)

        if response_times:
            stats["average_response_time"] = sum(response_times) / len(response_times)

        # Group by action type and risk level
        all_requests = completed + pending
        for request in all_requests:
            # By action type
            action_type = request.action_type
            if action_type not in stats["requests_by_action_type"]:
                stats["requests_by_action_type"][action_type] = 0
            stats["requests_by_action_type"][action_type] += 1

            # By risk level
            risk_level = request.risk_level.value
            if risk_level not in stats["requests_by_risk_level"]:
                stats["requests_by_risk_level"][risk_level] = 0
            stats["requests_by_risk_level"][risk_level] += 1

        return stats
