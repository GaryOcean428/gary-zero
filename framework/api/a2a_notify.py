"""
A2A API Handler for Push Notifications endpoint

Handles push notifications between A2A agents.
"""

from typing import Any

from pydantic import ValidationError

from framework.a2a.communication import A2AMessage, MessageType


class A2aNotify:
    """API handler for A2A push notifications endpoint"""

    async def process(self, input_data: dict[str, Any], request) -> dict[str, Any]:
        """
        Handle A2A push notification
        
        Args:
            input_data: Request input containing notification data
            request: HTTP request object
            
        Returns:
            Notification response with acknowledgment
        """
        try:
            # Validate required fields
            recipient_id = input_data.get("recipient_id")
            notification_type = input_data.get("notification_type")

            if not recipient_id:
                return {
                    "success": False,
                    "error": "recipient_id is required"
                }

            if not notification_type:
                return {
                    "success": False,
                    "error": "notification_type is required"
                }

            # Create notification message
            import uuid
            from datetime import datetime

            notification_message = A2AMessage(
                id=str(uuid.uuid4()),
                session_id=input_data.get("session_id", "notification"),
                sender_id=input_data.get("sender_id", "gary-zero"),
                recipient_id=recipient_id,
                type=MessageType.NOTIFICATION,
                content={
                    "notification_type": notification_type,
                    "title": input_data.get("title", ""),
                    "message": input_data.get("message", ""),
                    "data": input_data.get("data", {}),
                    "priority": input_data.get("priority", "normal")
                },
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

            # For now, just acknowledge receipt (streaming service would be used in full implementation)
            return {
                "success": True,
                "message_id": notification_message.id,
                "delivery_method": "queued",
                "timestamp": notification_message.timestamp
            }

        except ValidationError as e:
            return {
                "success": False,
                "error": f"Invalid notification format: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Notification delivery failed: {str(e)}"
            }
