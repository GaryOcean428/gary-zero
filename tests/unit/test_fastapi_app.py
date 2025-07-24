"""
Unit tests for FastAPI main application.
"""

import pytest


class TestFastAPIApp:
    """Test cases for the main FastAPI application."""

    def test_health_endpoint(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data

    def test_ready_endpoint(self, test_client):
        """Test the readiness check endpoint."""
        response = test_client.get("/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "gary-zero"
        assert "timestamp" in data

    def test_metrics_endpoint(self, test_client):
        """Test the metrics endpoint."""
        response = test_client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "active_websocket_connections" in data
        assert "uptime_seconds" in data
        assert "memory_usage_percent" in data
        assert "cpu_usage_percent" in data
        assert "version" in data
        assert "environment" in data

    def test_root_endpoint(self, test_client):
        """Test the root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Gary-Zero AI Agent Framework"
        assert data["version"] == "0.9.0"
        assert "docs" in data
        assert "health" in data
        assert "websocket" in data

    def test_404_handler(self, test_client):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data


class TestWebSocketEndpoint:
    """Test cases for WebSocket functionality."""

    def test_websocket_connection(self, test_client, sample_websocket_message):
        """Test WebSocket connection and message handling."""
        with test_client.websocket_connect("/ws") as websocket:
            # Send a test message
            websocket.send_json(sample_websocket_message)

            # Receive response
            data = websocket.receive_json()

            assert "status" in data
            assert "response" in data
            assert "timestamp" in data


class TestPydanticModels:
    """Test Pydantic models for request/response validation."""

    def test_health_response_model(self):
        """Test HealthResponse model."""
        from main import HealthResponse

        response = HealthResponse()
        assert response.status == "healthy"
        assert response.version == "0.9.0"
        assert response.timestamp > 0

    def test_message_request_model(self):
        """Test MessageRequest model validation."""
        from main import MessageRequest

        # Valid message
        valid_message = MessageRequest(
            message="Test message", agent_id="test-agent", context={"key": "value"}
        )
        assert valid_message.message == "Test message"

        # Test validation - empty message should fail
        with pytest.raises(ValueError):
            MessageRequest(message="")

    def test_message_response_model(self):
        """Test MessageResponse model."""
        from main import MessageResponse

        response = MessageResponse(
            status="success", response="Test response", agent_id="test-agent"
        )
        assert response.status == "success"
        assert response.response == "Test response"
        assert response.timestamp > 0
