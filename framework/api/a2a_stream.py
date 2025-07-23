"""
A2A API Handler for Streaming WebSocket endpoint

Handles WebSocket connections for real-time A2A communication.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Any

from framework.a2a.streaming import StreamingService

# Global streaming service instance
_streaming_service = None


def get_streaming_service() -> StreamingService:
    """Get or create the global streaming service instance"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service


class A2aStream:
    """API handler for A2A streaming WebSocket endpoint"""

    def __init__(self):
        self.streaming_service = get_streaming_service()

    async def process(self, input_data: dict[str, Any], request) -> dict[str, Any]:
        """
        This handler doesn't process regular HTTP requests
        WebSocket connections are handled separately
        """
        return {
            "success": False,
            "error": "Use WebSocket connection for streaming endpoint"
        }


async def handle_websocket_connection(websocket: WebSocket, agent_id: str, session_id: str, session_token: str = None):
    """
    Handle WebSocket connection for A2A streaming
    
    This function should be called from the FastAPI WebSocket endpoint
    """
    streaming_service = get_streaming_service()

    try:
        # Accept the WebSocket connection
        await websocket.accept()

        # Establish the A2A streaming connection
        connection_id = await streaming_service.connect(
            websocket=websocket,
            agent_id=agent_id,
            session_id=session_id,
            session_token=session_token
        )

        # Handle incoming messages
        while True:
            try:
                # Receive message from WebSocket
                data = await websocket.receive_json()

                # Process the message
                await streaming_service.handle_message(connection_id, data)

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Send error message and continue
                try:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"error": str(e)}
                    })
                except:
                    break

    except ValueError as e:
        # Connection not authorized
        await websocket.close(code=4001, reason=str(e))

    except Exception as e:
        # Other connection errors
        await websocket.close(code=4000, reason=f"Connection error: {str(e)}")

    finally:
        # Clean up connection
        if 'connection_id' in locals():
            await streaming_service.disconnect(connection_id)
