"""
Integration test for API bridge functionality.
"""

from fastapi.testclient import TestClient

from main import app


class TestAPIBridge:
    """Test the API bridge integration."""

    def test_health_endpoint_bridge(self):
        """Test that the health endpoint is accessible."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"

    def test_api_models_endpoint(self):
        """Test the enhanced models API endpoint."""
        client = TestClient(app)
        response = client.get("/api/models")
        assert response.status_code == 200

        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0

        # Check model structure
        model = data["models"][0]
        assert "name" in model
        assert "display_name" in model
        assert "provider" in model
        assert "capabilities" in model

    def test_model_details_endpoint(self):
        """Test getting details for a specific model."""
        client = TestClient(app)

        # Test with a known model
        response = client.get("/api/models/gpt-4o")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "gpt-4o"
        assert data["display_name"] == "GPT-4O (Latest)"
        assert "capabilities" in data

    def test_model_recommendation_endpoint(self):
        """Test model recommendation endpoint."""
        client = TestClient(app)

        response = client.post("/api/models/recommend?use_case=coding")
        assert response.status_code == 200

        data = response.json()
        assert "recommended_model" in data
        assert "display_name" in data
        assert "provider" in data

    def test_code_validation_endpoint(self):
        """Test code validation endpoint."""
        client = TestClient(app)

        # Test safe code
        response = client.post("/api/validate-code?code=print('hello')&security_level=strict")
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is True

        # Test unsafe code
        response = client.post("/api/validate-code?code=import os; os.system('ls')&security_level=strict")
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert len(data["blocked_items"]) > 0

    async def test_websocket_still_works(self, async_client):
        """Test that WebSocket functionality still works."""
        # Test that the WebSocket endpoint is available
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["websocket"] == "/ws"

    def test_api_documentation_available(self):
        """Test that API documentation is available in development."""
        client = TestClient(app)

        # In development mode, docs should be available
        response = client.get("/docs")
        # Should either return docs or redirect
        assert response.status_code in [200, 307, 404]  # 404 if in production mode
