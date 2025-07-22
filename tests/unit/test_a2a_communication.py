"""
Unit tests for the A2A communication module.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from framework.a2a.communication import (
    MessageType,
    MessagePriority,
    A2AMessage,
    CommunicationRequest,
    CommunicationResponse,
    CommunicationService
)


class TestMessageEnums:
    """Test cases for message enums."""
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        assert MessageType.REQUEST == "request"
        assert MessageType.RESPONSE == "response"
        assert MessageType.NOTIFICATION == "notification"
        assert MessageType.TASK == "task"
        assert MessageType.RESULT == "result"
        assert MessageType.ERROR == "error"
    
    def test_message_priority_enum(self):
        """Test MessagePriority enum values."""
        assert MessagePriority.LOW == "low"
        assert MessagePriority.NORMAL == "normal"
        assert MessagePriority.HIGH == "high"
        assert MessagePriority.URGENT == "urgent"


class TestA2AMessage:
    """Test cases for A2AMessage model."""
    
    def test_message_creation(self):
        """Test creating an A2A message."""
        message = A2AMessage(
            id="msg-123",
            session_id="session-456",
            sender_id="agent-1",
            recipient_id="agent-2",
            type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
            content={"action": "process_task", "data": {"task_id": "task-789"}},
            timestamp=datetime.now().isoformat(),
            correlation_id="corr-101",
            reply_to="msg-000",
            required_capabilities=["task_processing", "data_analysis"],
            context={"user_id": "user-123", "environment": "production"}
        )
        
        assert message.id == "msg-123"
        assert message.session_id == "session-456"
        assert message.sender_id == "agent-1"
        assert message.recipient_id == "agent-2"
        assert message.type == MessageType.REQUEST
        assert message.priority == MessagePriority.HIGH
        assert message.content == {"action": "process_task", "data": {"task_id": "task-789"}}
        assert message.correlation_id == "corr-101"
        assert message.reply_to == "msg-000"
        assert message.required_capabilities == ["task_processing", "data_analysis"]
        assert message.context == {"user_id": "user-123", "environment": "production"}
    
    def test_message_defaults(self):
        """Test A2A message with default values."""
        message = A2AMessage(
            id="msg-123",
            session_id="session-456",
            sender_id="agent-1",
            recipient_id="agent-2",
            type=MessageType.NOTIFICATION,
            content={"status": "ready"},
            timestamp=datetime.now().isoformat()
        )
        
        # Test default values
        assert message.priority == MessagePriority.NORMAL
        assert message.correlation_id is None
        assert message.reply_to is None
        assert message.required_capabilities == []
        assert message.context == {}


class TestCommunicationRequest:
    """Test cases for CommunicationRequest model."""
    
    def test_communication_request_creation(self):
        """Test creating a communication request."""
        message = A2AMessage(
            id="msg-123",
            session_id="session-456",
            sender_id="agent-1",
            recipient_id="agent-2",
            type=MessageType.REQUEST,
            content={"action": "ping"},
            timestamp=datetime.now().isoformat()
        )
        
        request = CommunicationRequest(
            message=message,
            session_token="token-abc123"
        )
        
        assert request.message == message
        assert request.session_token == "token-abc123"
    
    def test_communication_request_no_token(self):
        """Test communication request without session token."""
        message = A2AMessage(
            id="msg-123",
            session_id="session-456", 
            sender_id="agent-1",
            recipient_id="agent-2",
            type=MessageType.NOTIFICATION,
            content={"status": "completed"},
            timestamp=datetime.now().isoformat()
        )
        
        request = CommunicationRequest(message=message)
        
        assert request.message == message
        assert request.session_token is None


class TestCommunicationResponse:
    """Test cases for CommunicationResponse model."""
    
    def test_successful_response(self):
        """Test creating a successful communication response."""
        response_message = A2AMessage(
            id="msg-response-123",
            session_id="session-456",
            sender_id="agent-2", 
            recipient_id="agent-1",
            type=MessageType.RESPONSE,
            content={"result": "success", "data": {"processed": True}},
            timestamp=datetime.now().isoformat(),
            correlation_id="corr-101"
        )
        
        response = CommunicationResponse(
            success=True,
            message_id="msg-123",
            response_message=response_message
        )
        
        assert response.success is True
        assert response.message_id == "msg-123"
        assert response.response_message == response_message
        assert response.error is None
    
    def test_error_response(self):
        """Test creating an error communication response."""
        response = CommunicationResponse(
            success=False,
            message_id="msg-123",
            error="Invalid message format"
        )
        
        assert response.success is False
        assert response.message_id == "msg-123"
        assert response.response_message is None
        assert response.error == "Invalid message format"


class TestCommunicationService:
    """Test cases for CommunicationService class."""
    
    @pytest.fixture
    def service(self):
        """Create a communication service for testing."""
        return CommunicationService()
    
    @pytest.fixture
    def mock_negotiation_service(self, service):
        """Mock the negotiation service."""
        service.negotiation_service = Mock()
        return service.negotiation_service
    
    @pytest.fixture
    def sample_message(self):
        """Create a sample A2A message for testing."""
        return A2AMessage(
            id="msg-test-123",
            session_id="session-test-456", 
            sender_id="test-agent-1",
            recipient_id="test-agent-2",
            type=MessageType.REQUEST,
            content={"action": "test_action", "data": {"key": "value"}},
            timestamp=datetime.now().isoformat(),
            correlation_id="corr-test-101"
        )
    
    def test_service_initialization(self, service):
        """Test communication service initialization."""
        assert service.negotiation_service is not None
        assert len(service.message_handlers) == 3
        assert MessageType.REQUEST in service.message_handlers
        assert MessageType.TASK in service.message_handlers
        assert MessageType.NOTIFICATION in service.message_handlers
        assert len(service.processed_messages) == 0
    
    @pytest.mark.asyncio
    async def test_process_message_success_no_token(self, service, sample_message):
        """Test processing message successfully without session token."""
        # Mock handlers
        service._handle_request = AsyncMock(return_value=None)
        
        request = CommunicationRequest(message=sample_message)
        response = await service.process_message(request)
        
        assert response.success is True
        assert response.message_id == sample_message.id
        assert response.error is None
        assert sample_message.id in service.processed_messages
    
    @pytest.mark.asyncio
    async def test_process_message_with_valid_token(self, service, mock_negotiation_service, sample_message):
        """Test processing message with valid session token."""
        # Setup mocks
        mock_negotiation_service.validate_session_token.return_value = True
        mock_negotiation_service.get_session_info.return_value = {
            "session_id": "session-test-456",
            "supported_capabilities": ["test_capability"]
        }
        service._handle_request = AsyncMock(return_value=None)
        
        request = CommunicationRequest(
            message=sample_message,
            session_token="valid-token-123"
        )
        
        response = await service.process_message(request)
        
        assert response.success is True
        assert response.message_id == sample_message.id
        assert response.error is None
        
        # Verify token validation was called
        mock_negotiation_service.validate_session_token.assert_called_once_with(
            "session-test-456", "valid-token-123"
        )
    
    @pytest.mark.asyncio
    async def test_process_message_invalid_token(self, service, mock_negotiation_service, sample_message):
        """Test processing message with invalid session token."""
        # Setup mocks
        mock_negotiation_service.validate_session_token.return_value = False
        
        request = CommunicationRequest(
            message=sample_message,
            session_token="invalid-token"
        )
        
        response = await service.process_message(request)
        
        assert response.success is False
        assert response.message_id == sample_message.id
        assert response.error == "Invalid session token"
        assert sample_message.id not in service.processed_messages
    
    @pytest.mark.asyncio
    async def test_process_message_session_not_found(self, service, mock_negotiation_service, sample_message):
        """Test processing message when session is not found."""
        # Setup mocks
        mock_negotiation_service.validate_session_token.return_value = True
        mock_negotiation_service.get_session_info.return_value = None
        
        request = CommunicationRequest(
            message=sample_message,
            session_token="valid-token-123"
        )
        
        response = await service.process_message(request)
        
        assert response.success is False
        assert response.message_id == sample_message.id
        assert response.error == "Session not found"
    
    @pytest.mark.asyncio
    async def test_process_message_missing_capability(self, service, mock_negotiation_service):
        """Test processing message with missing required capability."""
        # Create message with required capability
        message = A2AMessage(
            id="msg-capability-test",
            session_id="session-test-456",
            sender_id="test-agent-1",
            recipient_id="test-agent-2",
            type=MessageType.REQUEST,
            content={"action": "specialized_task"},
            timestamp=datetime.now().isoformat(),
            required_capabilities=["specialized_capability"]
        )
        
        # Setup mocks - session exists but doesn't support required capability
        mock_negotiation_service.validate_session_token.return_value = True
        mock_negotiation_service.get_session_info.return_value = {
            "session_id": "session-test-456",
            "supported_capabilities": ["basic_capability"]  # Missing specialized_capability
        }
        
        request = CommunicationRequest(
            message=message,
            session_token="valid-token-123"
        )
        
        response = await service.process_message(request)
        
        assert response.success is False
        assert response.message_id == message.id
        assert "Required capability not supported: specialized_capability" in response.error
    
    @pytest.mark.asyncio
    async def test_process_message_unsupported_type(self, service, mock_negotiation_service):
        """Test processing message with unsupported message type."""
        # Create message with unsupported type (RESPONSE type doesn't have a handler)
        message = A2AMessage(
            id="msg-unsupported-type",
            session_id="session-test-456",
            sender_id="test-agent-1",
            recipient_id="test-agent-2",
            type=MessageType.RESPONSE,  # No handler for RESPONSE type
            content={"result": "test"},
            timestamp=datetime.now().isoformat()
        )
        
        request = CommunicationRequest(message=message)
        response = await service.process_message(request)
        
        assert response.success is False
        assert response.message_id == message.id
        assert "Unsupported message type: response" in response.error
    
    @pytest.mark.asyncio
    async def test_process_message_idempotency(self, service, sample_message):
        """Test message idempotency - same message processed twice."""
        # Mock handler
        service._handle_request = AsyncMock(return_value=None)
        
        request = CommunicationRequest(message=sample_message)
        
        # Process message first time
        response1 = await service.process_message(request)
        assert response1.success is True
        
        # Process same message again
        response2 = await service.process_message(request)
        assert response2.success is True
        assert response2.message_id == sample_message.id
        
        # Handler should only be called once
        service._handle_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_message(self, service):
        """Test handling REQUEST type message."""
        message = A2AMessage(
            id="msg-request-test",
            session_id="session-test",
            sender_id="sender-agent",
            recipient_id="recipient-agent",
            type=MessageType.REQUEST,
            content={"action": "ping", "data": {}},
            timestamp=datetime.now().isoformat()
        )
        
        # Call the handler directly
        result = await service._handle_request(message, {})
        
        # For now, handlers just return None (placeholder implementation)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_task_message(self, service):
        """Test handling TASK type message."""
        message = A2AMessage(
            id="msg-task-test",
            session_id="session-test",
            sender_id="sender-agent",
            recipient_id="recipient-agent",
            type=MessageType.TASK,
            content={"task_id": "task-123", "parameters": {"key": "value"}},
            timestamp=datetime.now().isoformat()
        )
        
        # Call the handler directly
        result = await service._handle_task(message, {})
        
        # For now, handlers just return None (placeholder implementation)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_notification_message(self, service):
        """Test handling NOTIFICATION type message."""
        message = A2AMessage(
            id="msg-notification-test",
            session_id="session-test",
            sender_id="sender-agent",
            recipient_id="recipient-agent",
            type=MessageType.NOTIFICATION,
            content={"event": "task_completed", "details": {"task_id": "task-123"}},
            timestamp=datetime.now().isoformat()
        )
        
        # Call the handler directly
        result = await service._handle_notification(message, {})
        
        # For now, handlers just return None (placeholder implementation)
        assert result is None


@pytest.mark.integration
class TestCommunicationServiceIntegration:
    """Integration tests for CommunicationService."""
    
    @pytest.mark.asyncio
    async def test_full_message_processing_workflow(self):
        """Test complete message processing workflow."""
        service = CommunicationService()
        
        # Mock the negotiation service for this test
        service.negotiation_service = Mock()
        service.negotiation_service.validate_session_token.return_value = True
        service.negotiation_service.get_session_info.return_value = {
            "session_id": "integration-session",
            "supported_capabilities": ["integration_test"]
        }
        
        # Mock handlers to return response messages
        async def mock_request_handler(message, session_info):
            return A2AMessage(
                id=f"response-{message.id}",
                session_id=message.session_id,
                sender_id=message.recipient_id,
                recipient_id=message.sender_id,
                type=MessageType.RESPONSE,
                content={"result": "processed", "original_action": message.content.get("action")},
                timestamp=datetime.now().isoformat(),
                correlation_id=message.correlation_id
            )
        
        service._handle_request = mock_request_handler
        
        # Create integration test message
        message = A2AMessage(
            id="integration-msg-001",
            session_id="integration-session",
            sender_id="integration-sender",
            recipient_id="integration-recipient",
            type=MessageType.REQUEST,
            content={"action": "integration_test", "data": {"test": True}},
            timestamp=datetime.now().isoformat(),
            correlation_id="integration-corr-001",
            required_capabilities=["integration_test"]
        )
        
        request = CommunicationRequest(
            message=message,
            session_token="integration-token-123"
        )
        
        # Process the message
        response = await service.process_message(request)
        
        # Verify successful processing
        assert response.success is True
        assert response.message_id == "integration-msg-001"
        assert response.error is None
        assert response.response_message is not None
        
        # Verify response message details
        response_msg = response.response_message
        assert response_msg.type == MessageType.RESPONSE
        assert response_msg.correlation_id == "integration-corr-001"
        assert response_msg.content["result"] == "processed"
        assert response_msg.content["original_action"] == "integration_test"
        
        # Verify message was stored for idempotency
        assert "integration-msg-001" in service.processed_messages
    
    @pytest.mark.asyncio
    async def test_message_processing_error_handling(self):
        """Test error handling in message processing."""
        service = CommunicationService()
        
        # Mock negotiation service to raise an exception
        service.negotiation_service = Mock()
        service.negotiation_service.validate_session_token.side_effect = Exception("Database error")
        
        message = A2AMessage(
            id="error-test-msg",
            session_id="error-session",
            sender_id="error-sender",
            recipient_id="error-recipient",
            type=MessageType.REQUEST,
            content={"action": "test"},
            timestamp=datetime.now().isoformat()
        )
        
        request = CommunicationRequest(
            message=message,
            session_token="error-token"
        )
        
        # Process message should handle the exception gracefully
        with pytest.raises(Exception):
            # The exception should propagate in this case since it's in the validation logic
            await service.process_message(request)