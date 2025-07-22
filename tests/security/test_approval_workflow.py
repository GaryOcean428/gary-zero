"""Tests for the approval workflow system."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

# Set path before importing
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from framework.security import (
    ApprovalWorkflow, ApprovalRequest, ActionDefinition,
    RiskLevel, ApprovalStatus, UserRole, ApprovalPolicy,
    require_approval, set_global_approval_workflow,
    AuditLogger
)


class TestApprovalWorkflow:
    """Test approval workflow functionality."""
    
    def setup_method(self):
        self.audit_logger = AuditLogger()
        self.workflow = ApprovalWorkflow(self.audit_logger)
        self.workflow.set_user_role("user123", UserRole.ADMIN)
        self.workflow.set_user_role("owner123", UserRole.OWNER)
        self.workflow.set_user_role("guest123", UserRole.GUEST)
    
    def test_initialization(self):
        """Test workflow initialization."""
        assert len(self.workflow.action_definitions) > 0
        assert "file_write" in self.workflow.action_definitions
        assert "shell_command" in self.workflow.action_definitions
        assert "computer_control" in self.workflow.action_definitions
    
    def test_user_role_management(self):
        """Test user role management."""
        self.workflow.set_user_role("test_user", UserRole.USER)
        assert self.workflow.get_user_role("test_user") == UserRole.USER
        assert self.workflow.get_user_role("unknown_user") == UserRole.USER  # Default
    
    def test_action_registration(self):
        """Test registering new action types."""
        custom_action = ActionDefinition(
            action_type="custom_action",
            risk_level=RiskLevel.HIGH,
            description="Custom test action",
            required_roles=[UserRole.OWNER],
            approval_policy=ApprovalPolicy.ALWAYS_ASK
        )
        
        self.workflow.register_action(custom_action)
        assert "custom_action" in self.workflow.action_definitions
        assert self.workflow.action_definitions["custom_action"].risk_level == RiskLevel.HIGH
    
    def test_action_configuration(self):
        """Test configuring existing action types."""
        original_timeout = self.workflow.action_definitions["file_write"].timeout_seconds
        
        self.workflow.configure_action("file_write", timeout_seconds=600)
        assert self.workflow.action_definitions["file_write"].timeout_seconds == 600
        
        # Test invalid action type
        with pytest.raises(ValueError):
            self.workflow.configure_action("nonexistent_action", timeout_seconds=300)
    
    @pytest.mark.asyncio
    async def test_never_ask_policy(self):
        """Test NEVER_ASK approval policy."""
        self.workflow.configure_action("file_write", approval_policy=ApprovalPolicy.NEVER_ASK)
        
        approved = await self.workflow.request_approval(
            user_id="user123",
            action_type="file_write",
            action_description="Test file write",
            parameters={"file": "test.txt"}
        )
        
        assert approved is True
    
    @pytest.mark.asyncio
    async def test_role_based_permission_check(self):
        """Test role-based permission checking."""
        # Guest user should not be able to execute shell commands
        approved = await self.workflow.request_approval(
            user_id="guest123",
            action_type="shell_command",
            action_description="Test shell command",
            parameters={"command": "ls"}
        )
        
        assert approved is False
    
    @pytest.mark.asyncio
    async def test_unregistered_action_rejection(self):
        """Test rejection of unregistered action types."""
        approved = await self.workflow.request_approval(
            user_id="user123",
            action_type="unknown_action",
            action_description="Unknown action",
            parameters={}
        )
        
        assert approved is False
    
    @pytest.mark.asyncio
    async def test_ask_once_policy_caching(self):
        """Test ASK_ONCE policy with caching."""
        # Configure action for ask_once policy
        self.workflow.configure_action("file_write", approval_policy=ApprovalPolicy.ASK_ONCE)
        
        # First request should use cache miss (but we'll simulate approval)
        cache_key = "user123:file_write"
        self.workflow.approval_cache[cache_key] = time.time()
        
        # Request should be auto-approved from cache
        approved = await self.workflow.request_approval(
            user_id="user123",
            action_type="file_write",
            action_description="Cached test",
            parameters={"file": "test.txt"}
        )
        
        assert approved is True
    
    @pytest.mark.asyncio
    async def test_manual_approval_flow(self):
        """Test manual approval and rejection flow."""
        # Create a task for approval request
        approval_task = asyncio.create_task(
            self.workflow.request_approval(
                user_id="user123",
                action_type="shell_command",
                action_description="Test command",
                parameters={"command": "echo test"},
                timeout_override=5  # Short timeout for test
            )
        )
        
        # Wait a bit for request to be created
        await asyncio.sleep(0.1)
        
        # Check that request is pending
        pending = self.workflow.get_pending_requests("user123")
        assert len(pending) == 1
        
        request = pending[0]
        assert request.action_type == "shell_command"
        assert request.status == ApprovalStatus.PENDING
        
        # Approve the request
        approved = await self.workflow.approve_request(
            request.request_id,
            "approver123",
            "Test approval"
        )
        assert approved is True
        
        # Check that the original task completes with approval
        result = await approval_task
        assert result is True
        
        # Verify request moved to completed
        assert len(self.workflow.get_pending_requests()) == 0
        assert request.request_id in self.workflow.completed_requests
    
    @pytest.mark.asyncio
    async def test_manual_rejection_flow(self):
        """Test manual rejection flow."""
        # Create approval request task
        approval_task = asyncio.create_task(
            self.workflow.request_approval(
                user_id="user123",
                action_type="shell_command",
                action_description="Test command",
                parameters={"command": "rm -rf /"},
                timeout_override=5
            )
        )
        
        # Wait for request creation
        await asyncio.sleep(0.1)
        
        # Get pending request
        pending = self.workflow.get_pending_requests()
        assert len(pending) == 1
        request = pending[0]
        
        # Reject the request
        rejected = await self.workflow.reject_request(
            request.request_id,
            "rejector123",
            "Dangerous command"
        )
        assert rejected is True
        
        # Check that the original task completes with rejection
        result = await approval_task
        assert result is False
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling."""
        # Create request with very short timeout
        with pytest.raises(TimeoutError):
            await self.workflow.request_approval(
                user_id="user123",
                action_type="shell_command",
                action_description="Timeout test",
                parameters={"command": "test"},
                timeout_override=0.1  # Very short timeout
            )
    
    @pytest.mark.asyncio
    async def test_request_cancellation(self):
        """Test request cancellation."""
        # Create approval request
        approval_task = asyncio.create_task(
            self.workflow.request_approval(
                user_id="user123",
                action_type="shell_command",
                action_description="Cancel test",
                parameters={"command": "test"},
                timeout_override=10
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Get and cancel request
        pending = self.workflow.get_pending_requests()
        request = pending[0]
        
        cancelled = await self.workflow.cancel_request(request.request_id, "canceller123")
        assert cancelled is True
        
        # Original task should complete with False
        result = await approval_task
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_requests(self):
        """Test cleanup of expired requests."""
        # Create request with short timeout
        await asyncio.sleep(0.1)  # Let it potentially expire
        
        # Manually add an expired request
        expired_request = ApprovalRequest(
            request_id="expired_123",
            user_id="user123",
            action_type="test_action",
            action_description="Expired test",
            parameters={},
            risk_level=RiskLevel.LOW,
            status=ApprovalStatus.PENDING,
            created_at=time.time() - 1000,
            expires_at=time.time() - 500  # Already expired
        )
        self.workflow.pending_requests["expired_123"] = expired_request
        
        # Trigger cleanup
        await self.workflow._cleanup_expired_requests()
        
        # Request should be moved to completed with expired status
        assert "expired_123" not in self.workflow.pending_requests
        assert "expired_123" in self.workflow.completed_requests
        assert self.workflow.completed_requests["expired_123"].status == ApprovalStatus.EXPIRED
    
    def test_approval_cache_management(self):
        """Test approval cache management."""
        # Add cache entries
        self.workflow.approval_cache["user1:action1"] = time.time()
        self.workflow.approval_cache["user1:action2"] = time.time()
        self.workflow.approval_cache["user2:action1"] = time.time()
        
        # Clear specific user/action
        self.workflow.clear_approval_cache("user1", "action1")
        assert "user1:action1" not in self.workflow.approval_cache
        assert "user1:action2" in self.workflow.approval_cache
        
        # Clear all for user
        self.workflow.clear_approval_cache("user1")
        assert "user1:action2" not in self.workflow.approval_cache
        assert "user2:action1" in self.workflow.approval_cache
        
        # Clear all cache
        self.workflow.clear_approval_cache()
        assert len(self.workflow.approval_cache) == 0
    
    def test_approval_statistics(self):
        """Test approval statistics generation."""
        # Add some completed requests
        approved_request = ApprovalRequest(
            request_id="approved_123",
            user_id="user123",
            action_type="file_write",
            action_description="Test write",
            parameters={},
            risk_level=RiskLevel.MEDIUM,
            status=ApprovalStatus.APPROVED,
            created_at=time.time() - 100,
            expires_at=time.time() + 100,
            approved_at=time.time() - 50
        )
        
        rejected_request = ApprovalRequest(
            request_id="rejected_123",
            user_id="user123",
            action_type="shell_command",
            action_description="Test command",
            parameters={},
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.REJECTED,
            created_at=time.time() - 100,
            expires_at=time.time() + 100
        )
        
        self.workflow.completed_requests["approved_123"] = approved_request
        self.workflow.completed_requests["rejected_123"] = rejected_request
        
        stats = self.workflow.get_approval_statistics()
        
        assert stats["total_requests"] == 2
        assert stats["approved_requests"] == 1
        assert stats["rejected_requests"] == 1
        assert stats["approval_rate"] == 0.5
        assert "file_write" in stats["requests_by_action_type"]
        assert "shell_command" in stats["requests_by_action_type"]
        assert "medium" in stats["requests_by_risk_level"]
        assert "high" in stats["requests_by_risk_level"]
    
    def test_request_serialization(self):
        """Test approval request serialization."""
        request = ApprovalRequest(
            request_id="test_123",
            user_id="user123",
            action_type="test_action",
            action_description="Test description",
            parameters={"param1": "value1"},
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.PENDING,
            created_at=time.time(),
            expires_at=time.time() + 300
        )
        
        # Test dict conversion
        request_dict = request.to_dict()
        assert request_dict["request_id"] == "test_123"
        assert request_dict["risk_level"] == "high"
        assert request_dict["status"] == "pending"
        assert "created_at_iso" in request_dict
        assert "expires_at_iso" in request_dict
        
        # Test JSON conversion
        request_json = request.to_json()
        assert isinstance(request_json, str)
        assert "test_123" in request_json


class TestApprovalDecorators:
    """Test approval decorators."""
    
    def setup_method(self):
        self.workflow = ApprovalWorkflow()
        self.workflow.set_user_role("user123", UserRole.ADMIN)
        set_global_approval_workflow(self.workflow)
        
        # Configure test action to auto-approve for testing
        self.workflow.configure_action("test_action", approval_policy=ApprovalPolicy.NEVER_ASK)
    
    @pytest.mark.asyncio
    async def test_require_approval_decorator_async(self):
        """Test require_approval decorator with async function."""
        
        @require_approval("test_action", RiskLevel.LOW, "Test async function")
        async def test_async_function(user_id: str, data: str):
            return f"Executed with {data}"
        
        result = await test_async_function("user123", "test_data")
        assert result == "Executed with test_data"
    
    def test_require_approval_decorator_sync(self):
        """Test require_approval decorator with sync function."""
        
        @require_approval("test_action", RiskLevel.LOW, "Test sync function")
        def test_sync_function(user_id: str, data: str):
            return f"Executed with {data}"
        
        result = test_sync_function("user123", "test_data")
        assert result == "Executed with test_data"
    
    @pytest.mark.asyncio
    async def test_decorator_permission_denied(self):
        """Test decorator with permission denied."""
        # Configure action to require approval and set user with insufficient role
        self.workflow.configure_action("restricted_action", 
                                      approval_policy=ApprovalPolicy.ALWAYS_ASK,
                                      required_roles=[UserRole.OWNER])
        
        @require_approval("restricted_action", RiskLevel.HIGH)
        async def restricted_function(user_id: str):
            return "Should not execute"
        
        # This should fail because user123 is ADMIN, not OWNER
        with pytest.raises(PermissionError):
            await restricted_function("user123")
    
    def test_custom_user_id_extraction(self):
        """Test custom user ID extraction function."""
        
        def extract_user_from_context(args, kwargs):
            # Extract from custom context object
            context = args[0]
            return context.user_id
        
        @require_approval("test_action", extract_user_id=extract_user_from_context)
        def function_with_context(context, data):
            return f"Executed with {data}"
        
        # Create mock context
        class Context:
            def __init__(self, user_id):
                self.user_id = user_id
        
        context = Context("user123")
        result = function_with_context(context, "test_data")
        assert result == "Executed with test_data"


@pytest.mark.asyncio
async def test_approval_integration_with_audit_logger():
    """Test integration between approval workflow and audit logger."""
    # Create mock audit logger to verify logging calls
    mock_audit_logger = AsyncMock(spec=AuditLogger)
    
    workflow = ApprovalWorkflow(mock_audit_logger)
    workflow.set_user_role("user123", UserRole.ADMIN)
    
    # Configure for auto-approval to test logging
    workflow.configure_action("file_write", approval_policy=ApprovalPolicy.NEVER_ASK)
    
    # Request approval
    approved = await workflow.request_approval(
        user_id="user123",
        action_type="file_write",
        action_description="Test file write",
        parameters={"file": "test.txt"}
    )
    
    assert approved is True
    
    # Verify audit logging was called
    assert mock_audit_logger.log_approval_decision.called


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])