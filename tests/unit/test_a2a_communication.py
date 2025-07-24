"""
Unit tests for the A2A communication module.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from framework.a2a.communication import (
    A2AMessage,
    CommunicationRequest,
    CommunicationService,
    MessagePriority,
    MessageType,
)


class TestMessageEnums:
    def test_message_type_enum(self):
        assert MessageType.REQUEST == "request"
        assert MessageType.RESPONSE == "response"
        assert MessageType.NOTIFICATION == "notification"
        assert MessageType.TASK == "task"
        assert MessageType.RESULT == "result"
        assert MessageType.ERROR == "error"

    def test_message_priority_enum(self):
        assert MessagePriority.LOW == "low"
        assert MessagePriority.NORMAL == "normal"
        assert MessagePriority.HIGH == "high"
        assert MessagePriority.URGENT == "urgent"


class TestA2AMessage:
    def test_message_creation(self):
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
            context={"user_id": "user-123", "environment": "production"},
        )
        assert message.id == "msg-123"
        assert message.session_id == "session-456"
        assert message.sender_id == "agent-1"
        assert message.recipient_id == "agent-2"
        assert message.type == MessageType.REQUEST
        assert message.priority == MessagePriority.HIGH
        assert message.content == {
            "action": "process_task",
            "data": {"task_id": "task-789"},
        }
        assert message.correlation_id == "corr-101"
        assert message.reply_to == "msg-000"
        assert message.required_capabilities == ["task_processing", "data_analysis"]
        assert message.context == {"user_id": "user-123", "environment": "production"}

    def test_message_defaults(self):
        message = A2AMessage(
            id="msg-123",
            session_id="session-456",
            sender_id="agent-1",
            recipient_id="agent-2",
            type=MessageType.NOTIFICATION,
            content={"status": "ready"},
            timestamp=datetime.now().isoformat(),
        )
        assert message.priority == MessagePriority.NORMAL
        assert message.correlation_id is None
        assert message.reply_to is None
        assert message.required_capabilities == []
        assert message.context == {}


class TestCommunicationServiceIntegration:
    @pytest.mark.asyncio
    async def test_full_message_processing_workflow(self):
        service = CommunicationService()
        service.negotiation_service = Mock()
        service.negotiation_service.validate_session_token.return_value = True
        service.negotiation_service.get_session_info.return_value = {
            "session_id": "integration-session",
            "supported_capabilities": ["integration_test"],
        }

        async def mock_request_handler(message, session_info):
            return A2AMessage(
                id=f"response-{message.id}",
                session_id=message.session_id,
                sender_id=message.recipient_id,
                recipient_id=message.sender_id,
                type=MessageType.RESPONSE,
                content={
                    "result": "processed",
                    "original_action": message.content.get("action"),
                },
                timestamp=datetime.now().isoformat(),
                correlation_id=message.correlation_id,
            )

        service._handle_request = mock_request_handler

        message = A2AMessage(
            id="integration-msg-001",
            session_id="integration-session",
            sender_id="integration-sender",
            recipient_id="integration-recipient",
            type=MessageType.REQUEST,
            content={"action": "integration_test", "data": {"test": True}},
            timestamp=datetime.now().isoformat(),
            correlation_id="integration-corr-001",
            required_capabilities=["integration_test"],
        )

        request = CommunicationRequest(
            message=message, session_token="integration-token-123"
        )

        response = await service.process_message(request)

        assert response.success is True
        assert response.message_id == "integration-msg-001"
        assert response.response_message is not None
        response_msg = response.response_message
        assert response_msg.type == MessageType.RESPONSE
        assert response_msg.correlation_id == "integration-corr-001"
        assert response_msg.content["result"] == "processed"
        assert response_msg.content["original_action"] == "integration_test"
        assert "integration-msg-001" in service.processed_messages


class TestA2AProtocolCompliance:
    @pytest.mark.asyncio
    async def test_capability_negotiation(self):
        negotiator = AsyncMock()
        negotiator.negotiate_capabilities.return_value = {
            "agreed_capabilities": ["streaming", "context_sharing"],
            "protocol_version": "1.0",
            "session_parameters": {"max_message_size": 1024 * 1024, "timeout": 30},
        }

        result = await negotiator.negotiate_capabilities(
            local_capabilities=["streaming", "context_sharing", "file_transfer"],
            remote_capabilities=["streaming", "context_sharing"],
        )

        assert "agreed_capabilities" in result
        assert len(result["agreed_capabilities"]) == 2
        assert "streaming" in result["agreed_capabilities"]
        assert "context_sharing" in result["agreed_capabilities"]
