"""
A2A Streaming Service

Handles WebSocket-based streaming communication for real-time agent interaction.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum
import asyncio

from .negotiation import NegotiationService
from .communication import A2AMessage, MessageType, MessagePriority


class StreamEventType(str, Enum):
    """Stream event types"""
    MESSAGE = "message"
    STATUS = "status"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CLOSE = "close"


class StreamEvent(BaseModel):
    """Stream event model"""
    type: StreamEventType = Field(description="Event type")
    data: Dict[str, Any] = Field(description="Event data")
    timestamp: str = Field(description="Event timestamp")
    sequence: int = Field(description="Event sequence number")


class StreamConnection(BaseModel):
    """Active stream connection"""
    connection_id: str = Field(description="Unique connection ID")
    agent_id: str = Field(description="Connected agent ID")
    session_id: str = Field(description="Session ID")
    websocket: Any = Field(description="WebSocket connection object")
    created_at: str = Field(description="Connection creation time")
    last_heartbeat: str = Field(description="Last heartbeat time")
    sequence_number: int = Field(description="Current sequence number", default=0)


class StreamingService:
    """A2A Streaming Service Implementation"""
    
    def __init__(self):
        self.negotiation_service = NegotiationService()
        self.active_connections: Dict[str, StreamConnection] = {}
        self.agent_connections: Dict[str, Set[str]] = {}  # agent_id -> set of connection_ids
        self.heartbeat_interval = 30  # seconds
        self._running = False
    
    async def start_service(self):
        """Start the streaming service"""
        self._running = True
        # Start heartbeat task
        asyncio.create_task(self._heartbeat_task())
    
    async def stop_service(self):
        """Stop the streaming service"""
        self._running = False
        # Close all connections
        for connection in list(self.active_connections.values()):
            await self.disconnect(connection.connection_id)
    
    async def connect(self, websocket, agent_id: str, session_id: str, session_token: Optional[str] = None) -> str:
        """
        Handle new WebSocket connection
        
        Args:
            websocket: WebSocket connection object
            agent_id: ID of the connecting agent
            session_id: Session ID for the connection
            session_token: Optional session authentication token
            
        Returns:
            Connection ID if successful
            
        Raises:
            ValueError: If connection is not authorized
        """
        # Validate session if token provided
        if session_token:
            if not self.negotiation_service.validate_session_token(session_id, session_token):
                raise ValueError("Invalid session token")
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Create connection object
        connection = StreamConnection(
            connection_id=connection_id,
            agent_id=agent_id,
            session_id=session_id,
            websocket=websocket,
            created_at=self._get_current_timestamp(),
            last_heartbeat=self._get_current_timestamp()
        )
        
        # Store connection
        self.active_connections[connection_id] = connection
        
        # Track by agent ID
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = set()
        self.agent_connections[agent_id].add(connection_id)
        
        # Send welcome message
        await self._send_event(connection, StreamEventType.STATUS, {
            "status": "connected",
            "connection_id": connection_id,
            "message": "WebSocket connection established"
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect a WebSocket connection
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return
        
        # Send close event
        try:
            await self._send_event(connection, StreamEventType.CLOSE, {
                "reason": "disconnect_requested"
            })
        except:
            pass  # Connection might already be closed
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except:
            pass
        
        # Remove from tracking
        self.active_connections.pop(connection_id, None)
        if connection.agent_id in self.agent_connections:
            self.agent_connections[connection.agent_id].discard(connection_id)
            if not self.agent_connections[connection.agent_id]:
                del self.agent_connections[connection.agent_id]
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming WebSocket message
        
        Args:
            connection_id: ID of the connection
            message_data: Received message data
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return
        
        try:
            # Update heartbeat
            connection.last_heartbeat = self._get_current_timestamp()
            
            # Handle different message types
            message_type = message_data.get("type")
            
            if message_type == "heartbeat":
                await self._handle_heartbeat(connection, message_data)
            elif message_type == "a2a_message":
                await self._handle_a2a_message(connection, message_data)
            elif message_type == "status_request":
                await self._handle_status_request(connection, message_data)
            else:
                await self._send_event(connection, StreamEventType.ERROR, {
                    "error": f"Unknown message type: {message_type}"
                })
        
        except Exception as e:
            await self._send_event(connection, StreamEventType.ERROR, {
                "error": f"Message handling failed: {str(e)}"
            })
    
    async def broadcast_to_agent(self, agent_id: str, event_type: StreamEventType, data: Dict[str, Any]) -> None:
        """
        Broadcast an event to all connections of a specific agent
        
        Args:
            agent_id: Target agent ID
            event_type: Type of event to send
            data: Event data
        """
        if agent_id not in self.agent_connections:
            return
        
        # Send to all connections of this agent
        connection_ids = list(self.agent_connections[agent_id])
        for connection_id in connection_ids:
            connection = self.active_connections.get(connection_id)
            if connection:
                try:
                    await self._send_event(connection, event_type, data)
                except:
                    # Connection might be dead, remove it
                    await self.disconnect(connection_id)
    
    async def send_a2a_message(self, recipient_agent_id: str, message: A2AMessage) -> bool:
        """
        Send an A2A message via streaming to a connected agent
        
        Args:
            recipient_agent_id: ID of the recipient agent
            message: A2A message to send
            
        Returns:
            True if message was sent successfully
        """
        if recipient_agent_id not in self.agent_connections:
            return False
        
        await self.broadcast_to_agent(recipient_agent_id, StreamEventType.MESSAGE, {
            "a2a_message": message.dict()
        })
        
        return True
    
    async def _handle_heartbeat(self, connection: StreamConnection, message_data: Dict[str, Any]) -> None:
        """Handle heartbeat message"""
        await self._send_event(connection, StreamEventType.HEARTBEAT, {
            "response": "pong",
            "server_time": self._get_current_timestamp()
        })
    
    async def _handle_a2a_message(self, connection: StreamConnection, message_data: Dict[str, Any]) -> None:
        """Handle A2A message received via WebSocket"""
        # Extract A2A message
        a2a_message_data = message_data.get("data", {})
        
        # Process through communication service
        from .communication import CommunicationService, CommunicationRequest
        
        try:
            a2a_message = A2AMessage(**a2a_message_data)
            comm_service = CommunicationService()
            
            request = CommunicationRequest(
                message=a2a_message,
                session_token=message_data.get("session_token")
            )
            
            response = await comm_service.process_message(request)
            
            # Send response back via WebSocket
            await self._send_event(connection, StreamEventType.MESSAGE, {
                "response": response.dict()
            })
            
        except Exception as e:
            await self._send_event(connection, StreamEventType.ERROR, {
                "error": f"A2A message processing failed: {str(e)}"
            })
    
    async def _handle_status_request(self, connection: StreamConnection, message_data: Dict[str, Any]) -> None:
        """Handle status request"""
        status_data = {
            "connection_id": connection.connection_id,
            "agent_id": connection.agent_id,
            "connected_at": connection.created_at,
            "active_connections": len(self.active_connections),
            "server_status": "healthy"
        }
        
        await self._send_event(connection, StreamEventType.STATUS, status_data)
    
    async def _send_event(self, connection: StreamConnection, event_type: StreamEventType, data: Dict[str, Any]) -> None:
        """Send an event to a WebSocket connection"""
        connection.sequence_number += 1
        
        event = StreamEvent(
            type=event_type,
            data=data,
            timestamp=self._get_current_timestamp(),
            sequence=connection.sequence_number
        )
        
        try:
            await connection.websocket.send_text(json.dumps(event.dict()))
        except Exception as e:
            # Connection is probably dead, disconnect it
            await self.disconnect(connection.connection_id)
            raise e
    
    async def _heartbeat_task(self) -> None:
        """Background task to send heartbeats and clean up dead connections"""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check all connections for heartbeat timeout
                current_time = self._get_current_timestamp()
                dead_connections = []
                
                for connection in self.active_connections.values():
                    # Check if connection is still alive (simplified - in real implementation check actual timeout)
                    try:
                        await self._send_event(connection, StreamEventType.HEARTBEAT, {
                            "ping": current_time
                        })
                    except:
                        dead_connections.append(connection.connection_id)
                
                # Clean up dead connections
                for connection_id in dead_connections:
                    await self.disconnect(connection_id)
                
            except Exception as e:
                print(f"Heartbeat task error: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connection"""
        connection = self.active_connections.get(connection_id)
        if not connection:
            return None
        
        return {
            "connection_id": connection.connection_id,
            "agent_id": connection.agent_id,
            "session_id": connection.session_id,
            "created_at": connection.created_at,
            "last_heartbeat": connection.last_heartbeat,
            "sequence_number": connection.sequence_number
        }
    
    def get_agent_connections(self, agent_id: str) -> List[str]:
        """Get all connection IDs for an agent"""
        return list(self.agent_connections.get(agent_id, set()))