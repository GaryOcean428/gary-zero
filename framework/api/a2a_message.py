"""
A2A API Handler for Message endpoint

Handles agent-to-agent communication messages.
"""

from typing import Any

from pydantic import ValidationError

from framework.a2a.communication import A2AMessage, CommunicationRequest, CommunicationService


class A2aMessage:
    """API handler for A2A message endpoint"""

    def __init__(self):
        self.communication_service = CommunicationService()

    async def process(self, input_data: dict[str, Any], request) -> dict[str, Any]:
        """
        Handle A2A message communication
        
        Args:
            input_data: Request input containing the A2A message
            request: HTTP request object
            
        Returns:
            Communication response with result or error
        """
        try:
            # Validate required message fields
            message_data = input_data.get("message")
            if not message_data:
                return {
                    "success": False,
                    "error": "message is required"
                }

            # Create A2A message object
            a2a_message = A2AMessage(**message_data)

            # Create communication request
            comm_request = CommunicationRequest(
                message=a2a_message,
                session_token=input_data.get("session_token")
            )

            # Process the message
            response = await self.communication_service.process_message(comm_request)

            return response.dict()

        except ValidationError as e:
            return {
                "success": False,
                "error": f"Invalid message format: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Message processing failed: {str(e)}"
            }
