"""
A2A Communication Service

Handles agent-to-agent messaging and communication coordination.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .negotiation import NegotiationService


class MessageType(str, Enum):
    """A2A message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    TASK = "task"
    RESULT = "result"
    ERROR = "error"


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class A2AMessage(BaseModel):
    """A2A message model"""
    id: str = Field(description="Unique message ID")
    session_id: str = Field(description="Session ID")
    sender_id: str = Field(description="Sender agent ID")
    recipient_id: str = Field(description="Recipient agent ID")

    # Message content
    type: MessageType = Field(description="Message type")
    priority: MessagePriority = Field(description="Message priority", default=MessagePriority.NORMAL)
    content: dict[str, Any] = Field(description="Message content")

    # Metadata
    timestamp: str = Field(description="Message timestamp")
    correlation_id: str | None = Field(description="Correlation ID for request/response", default=None)
    reply_to: str | None = Field(description="Reply-to message ID", default=None)

    # Capabilities and context
    required_capabilities: list[str] = Field(description="Required capabilities to process", default=[])
    context: dict[str, Any] = Field(description="Message context", default={})


class CommunicationRequest(BaseModel):
    """Communication request from external agent"""
    message: A2AMessage = Field(description="The A2A message")
    session_token: str | None = Field(description="Session authentication token", default=None)


class CommunicationResponse(BaseModel):
    """Communication response"""
    success: bool = Field(description="Whether communication was successful")
    message_id: str = Field(description="Original message ID")
    response_message: A2AMessage | None = Field(description="Response message", default=None)
    error: str | None = Field(description="Error message if failed", default=None)


class CommunicationService:
    """A2A Communication Service Implementation"""

    def __init__(self):
        self.negotiation_service = NegotiationService()
        self.message_handlers: dict[MessageType, callable] = {
            MessageType.REQUEST: self._handle_request,
            MessageType.TASK: self._handle_task,
            MessageType.NOTIFICATION: self._handle_notification
        }
        self.processed_messages: dict[str, A2AMessage] = {}

    async def process_message(self, request: CommunicationRequest) -> CommunicationResponse:
        """
        Process an incoming A2A message
        
        Args:
            request: Communication request with message and session info
            
        Returns:
            Communication response with result or error
        """
        try:
            message = request.message

            # Validate session if token provided
            if request.session_token:
                if not self.negotiation_service.validate_session_token(message.session_id, request.session_token):
                    return CommunicationResponse(
                        success=False,
                        message_id=message.id,
                        error="Invalid session token"
                    )

            # Check if message already processed (idempotency)
            if message.id in self.processed_messages:
                return CommunicationResponse(
                    success=True,
                    message_id=message.id,
                    response_message=None  # Already processed
                )

            # Get session info
            session_info = self.negotiation_service.get_session_info(message.session_id)
            if not session_info and request.session_token:
                return CommunicationResponse(
                    success=False,
                    message_id=message.id,
                    error="Session not found"
                )

            # Check required capabilities
            if session_info:
                supported_capabilities = session_info.get("supported_capabilities", [])
                for required_cap in message.required_capabilities:
                    if required_cap not in supported_capabilities:
                        return CommunicationResponse(
                            success=False,
                            message_id=message.id,
                            error=f"Required capability not supported: {required_cap}"
                        )

            # Route to appropriate handler
            handler = self.message_handlers.get(message.type)
            if not handler:
                return CommunicationResponse(
                    success=False,
                    message_id=message.id,
                    error=f"Unsupported message type: {message.type}"
                )

            # Process message
            response_message = await handler(message, session_info)

            # Store processed message
            self.processed_messages[message.id] = message

            return CommunicationResponse(
                success=True,
                message_id=message.id,
                response_message=response_message
            )

        except Exception as e:
            return CommunicationResponse(
                success=False,
                message_id=request.message.id,
                error=f"Communication failed: {str(e)}"
            )

    async def _handle_request(self, message: A2AMessage, session_info: dict[str, Any] | None) -> A2AMessage | None:
        """Handle a request message"""
        content = message.content
        request_type = content.get("request_type")

        response_content = {}

        if request_type == "capabilities":
            # Return agent capabilities
            from .agent_card import get_agent_card
            agent_card = get_agent_card()
            response_content = {
                "capabilities": [cap.dict() for cap in agent_card.capabilities if cap.enabled],
                "endpoints": [ep.dict() for ep in agent_card.endpoints]
            }

        elif request_type == "status":
            # Return agent status
            response_content = {
                "status": "active",
                "load": "normal",
                "available_capabilities": session_info.get("supported_capabilities", []) if session_info else []
            }

        elif request_type == "execute_task":
            # Execute a task (delegate to agent)
            task_content = content.get("task", {})
            response_content = await self._execute_agent_task(task_content, message.sender_id)

        else:
            response_content = {"error": f"Unknown request type: {request_type}"}

        # Create response message
        return A2AMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender_id=message.recipient_id,
            recipient_id=message.sender_id,
            type=MessageType.RESPONSE,
            content=response_content,
            timestamp=self._get_current_timestamp(),
            correlation_id=message.id,
            reply_to=message.id
        )

    async def _handle_task(self, message: A2AMessage, session_info: dict[str, Any] | None) -> A2AMessage | None:
        """Handle a task message"""
        task_content = message.content

        # Execute the task using Gary-Zero's agent system
        result = await self._execute_agent_task(task_content, message.sender_id)

        # Create result message
        return A2AMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender_id=message.recipient_id,
            recipient_id=message.sender_id,
            type=MessageType.RESULT,
            content=result,
            timestamp=self._get_current_timestamp(),
            correlation_id=message.id,
            reply_to=message.id
        )

    async def _handle_notification(self, message: A2AMessage, session_info: dict[str, Any] | None) -> A2AMessage | None:
        """Handle a notification message"""
        # Notifications don't require responses, just log/process
        notification_type = message.content.get("notification_type")

        # Log the notification
        print(f"A2A Notification from {message.sender_id}: {notification_type}")

        # Could trigger events or update internal state here

        return None  # No response for notifications

    async def _execute_agent_task(self, task_content: dict[str, Any], requester_id: str) -> dict[str, Any]:
        """
        Execute a task using Gary-Zero's agent system
        
        Args:
            task_content: Task description and parameters
            requester_id: ID of the requesting agent
            
        Returns:
            Task execution result
        """
        try:
            # Extract task information
            task_description = task_content.get("description", "")
            task_type = task_content.get("type", "general")
            parameters = task_content.get("parameters", {})

            # Create a simple agent context for the external request
            # In a real implementation, you might want to create a separate agent instance

            # For now, return a simple acknowledgment
            # This could be enhanced to actually delegate to the agent system

            return {
                "status": "completed",
                "result": f"Task '{task_description}' received from agent {requester_id}",
                "task_id": str(uuid.uuid4()),
                "timestamp": self._get_current_timestamp()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"

    def send_message_to_agent(self, recipient_id: str, message_type: MessageType, content: dict[str, Any]) -> str:
        """
        Send a message to another agent (for outbound communication)
        
        Args:
            recipient_id: Target agent ID
            message_type: Type of message to send
            content: Message content
            
        Returns:
            Message ID
        """
        # This would implement outbound A2A communication
        # For now, just return a placeholder
        message_id = str(uuid.uuid4())

        # In a real implementation, this would:
        # 1. Look up the recipient agent's endpoint
        # 2. Create and send the A2A message
        # 3. Handle the response

        return message_id
