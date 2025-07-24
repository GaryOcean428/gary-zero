"""
Real-time AI Action Streaming Service.

This module provides WebSocket-based real-time streaming of AI actions
for immediate visualization and transparency. It handles action broadcasting,
client management, and real-time updates.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

try:
    import websockets
    from websockets.server import WebSocketServerProtocol

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None

from framework.helpers.ai_action_interceptor import AIAction
from framework.helpers.log import Log


class ActionStreamMessage:
    """Message format for action streaming."""

    def __init__(
        self, message_type: str, data: Any = None, timestamp: datetime | None = None
    ):
        self.message_id = str(uuid.uuid4())
        self.message_type = message_type
        self.data = data or {}
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class ActionStreamClient:
    """Represents a connected WebSocket client."""

    def __init__(self, websocket: WebSocketServerProtocol, client_id: str = None):
        self.websocket = websocket
        self.client_id = client_id or str(uuid.uuid4())
        self.connected_at = datetime.now(UTC)
        self.subscriptions: set[str] = set()
        self.filters: dict[str, Any] = {}
        self.active = True

    async def send_message(self, message: ActionStreamMessage):
        """Send a message to this client."""
        if not self.active:
            return

        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            Log.log().error(f"Failed to send message to client {self.client_id}: {e}")
            self.active = False

    def add_subscription(self, subscription: str):
        """Add a subscription filter."""
        self.subscriptions.add(subscription)

    def remove_subscription(self, subscription: str):
        """Remove a subscription filter."""
        self.subscriptions.discard(subscription)

    def set_filter(self, filter_name: str, filter_value: Any):
        """Set a filter value."""
        self.filters[filter_name] = filter_value

    def matches_filters(self, action: AIAction) -> bool:
        """Check if action matches client filters."""
        # Check provider filter
        if "provider" in self.filters:
            if action.provider.value not in self.filters["provider"]:
                return False

        # Check action type filter
        if "action_type" in self.filters:
            if action.action_type.value not in self.filters["action_type"]:
                return False

        # Check subscription filters
        if self.subscriptions:
            action_categories = {
                action.provider.value,
                action.action_type.value,
                f"{action.provider.value}.{action.action_type.value}",
                action.session_id,
                "all",
            }
            if not action_categories.intersection(self.subscriptions):
                return False

        return True


class AIActionStreamingService:
    """WebSocket-based streaming service for AI actions."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.clients: dict[str, ActionStreamClient] = {}
        self.running = False
        self.message_history: list[ActionStreamMessage] = []
        self.max_history_size = 1000

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "actions_streamed": 0,
            "started_at": None,
        }

    async def start_server(self):
        """Start the WebSocket streaming server."""
        if not WEBSOCKETS_AVAILABLE:
            Log.log().error(
                "WebSockets not available. Install websockets package for streaming."
            )
            return

        if self.running:
            return

        Log.log().info(
            f"🌐 Starting AI Action Streaming Server on {self.host}:{self.port}"
        )

        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
            )

            self.running = True
            self.stats["started_at"] = datetime.now(UTC)

            Log.log().info(
                f"✅ AI Action Streaming Server started on ws://{self.host}:{self.port}"
            )

            # Keep server running
            await self.server.wait_closed()

        except Exception as e:
            Log.log().error(f"Failed to start streaming server: {e}")
            self.running = False

    async def stop_server(self):
        """Stop the WebSocket streaming server."""
        if not self.running or not self.server:
            return

        Log.log().info("🛑 Stopping AI Action Streaming Server")

        # Close all client connections
        for client in list(self.clients.values()):
            await self.disconnect_client(client.client_id)

        self.server.close()
        await self.server.wait_closed()
        self.running = False

        Log.log().info("✅ AI Action Streaming Server stopped")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new WebSocket client connection."""
        client = ActionStreamClient(websocket)
        self.clients[client.client_id] = client
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1

        Log.log().info(f"🔗 Client connected: {client.client_id}")

        # Send welcome message
        welcome_msg = ActionStreamMessage(
            "connection",
            {
                "status": "connected",
                "client_id": client.client_id,
                "server_info": {
                    "version": "1.0.0",
                    "capabilities": ["action_streaming", "filtering", "subscriptions"],
                },
            },
        )
        await client.send_message(welcome_msg)

        # Send recent action history
        await self.send_action_history(client.client_id)

        try:
            async for message in websocket:
                await self.handle_client_message(client.client_id, message)

        except websockets.exceptions.ConnectionClosed:
            Log.log().info(f"📤 Client disconnected: {client.client_id}")
        except Exception as e:
            Log.log().error(f"Client error {client.client_id}: {e}")
        finally:
            await self.disconnect_client(client.client_id)

    async def handle_client_message(self, client_id: str, message: str):
        """Handle a message from a client."""
        client = self.clients.get(client_id)
        if not client:
            return

        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            if message_type == "subscribe":
                # Handle subscription request
                subscriptions = data.get("subscriptions", [])
                for sub in subscriptions:
                    client.add_subscription(sub)

                response = ActionStreamMessage(
                    "subscription_updated",
                    {"subscriptions": list(client.subscriptions)},
                )
                await client.send_message(response)

            elif message_type == "unsubscribe":
                # Handle unsubscription request
                subscriptions = data.get("subscriptions", [])
                for sub in subscriptions:
                    client.remove_subscription(sub)

                response = ActionStreamMessage(
                    "subscription_updated",
                    {"subscriptions": list(client.subscriptions)},
                )
                await client.send_message(response)

            elif message_type == "set_filter":
                # Handle filter setting
                filters = data.get("filters", {})
                for filter_name, filter_value in filters.items():
                    client.set_filter(filter_name, filter_value)

                response = ActionStreamMessage(
                    "filters_updated", {"filters": client.filters}
                )
                await client.send_message(response)

            elif message_type == "get_stats":
                # Send server statistics
                response = ActionStreamMessage("server_stats", self.get_server_stats())
                await client.send_message(response)

            elif message_type == "ping":
                # Handle ping
                response = ActionStreamMessage(
                    "pong", {"timestamp": datetime.now(UTC).isoformat()}
                )
                await client.send_message(response)

        except json.JSONDecodeError:
            error_msg = ActionStreamMessage(
                "error", {"message": "Invalid JSON message"}
            )
            await client.send_message(error_msg)
        except Exception as e:
            error_msg = ActionStreamMessage(
                "error", {"message": f"Message handling error: {str(e)}"}
            )
            await client.send_message(error_msg)

    async def disconnect_client(self, client_id: str):
        """Disconnect a client."""
        client = self.clients.pop(client_id, None)
        if client:
            client.active = False
            self.stats["active_connections"] -= 1
            try:
                await client.websocket.close()
            except:
                pass

    async def broadcast_action(self, action: AIAction):
        """Broadcast an action to all subscribed clients."""
        if not self.running or not self.clients:
            return

        # Create action message
        action_data = {
            "action_id": action.action_id,
            "timestamp": action.timestamp.isoformat(),
            "provider": action.provider.value,
            "action_type": action.action_type.value,
            "description": action.description,
            "parameters": action.parameters,
            "metadata": action.metadata,
            "session_id": action.session_id,
            "agent_name": action.agent_name,
            "status": action.status,
            "execution_time": action.execution_time,
            "result": action.result,
            "ui_url": action.ui_url,
            "screenshot_path": action.screenshot_path,
        }

        message = ActionStreamMessage("ai_action", action_data)

        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history.pop(0)

        # Send to matching clients
        disconnected_clients = []
        for client_id, client in self.clients.items():
            if client.matches_filters(action):
                try:
                    await client.send_message(message)
                    self.stats["messages_sent"] += 1
                except Exception as e:
                    Log.log().error(f"Failed to send to client {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)

        self.stats["actions_streamed"] += 1

    async def send_action_history(self, client_id: str, limit: int = 50):
        """Send recent action history to a client."""
        client = self.clients.get(client_id)
        if not client:
            return

        # Send recent messages
        recent_messages = self.message_history[-limit:]
        for message in recent_messages:
            await client.send_message(message)

    def get_server_stats(self) -> dict[str, Any]:
        """Get server statistics."""
        uptime = None
        if self.stats["started_at"]:
            uptime = (datetime.now(UTC) - self.stats["started_at"]).total_seconds()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "running": self.running,
            "client_count": len(self.clients),
            "message_history_size": len(self.message_history),
        }

    async def send_system_message(
        self, message_type: str, data: Any = None, target_client: str = None
    ):
        """Send a system message to clients."""
        message = ActionStreamMessage(message_type, data)

        if target_client:
            client = self.clients.get(target_client)
            if client:
                await client.send_message(message)
        else:
            # Broadcast to all clients
            for client in self.clients.values():
                try:
                    await client.send_message(message)
                    self.stats["messages_sent"] += 1
                except Exception as e:
                    Log.log().error(f"Failed to send system message: {e}")


# Global streaming service instance
_streaming_service = None


def get_streaming_service() -> AIActionStreamingService:
    """Get the global streaming service."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = AIActionStreamingService()
    return _streaming_service


async def start_action_streaming(host: str = "localhost", port: int = 8765):
    """Start the action streaming service."""
    service = get_streaming_service()
    service.host = host
    service.port = port
    await service.start_server()


async def stop_action_streaming():
    """Stop the action streaming service."""
    service = get_streaming_service()
    await service.stop_server()


async def broadcast_action(action: AIAction):
    """Broadcast an action to the streaming service."""
    service = get_streaming_service()
    await service.broadcast_action(action)
