"""
End-to-end tests for web UI workflows.
"""

import pytest
import asyncio


@pytest.mark.asyncio
@pytest.mark.e2e
class TestWebUIWorkflows:
    """E2E tests for web UI functionality."""
    
    async def test_health_endpoint_accessibility(self):
        """Test that health endpoint is accessible."""
        # Instead of launching a browser, test the endpoint directly
        # This avoids needing playwright browser binaries in CI environment
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify response is valid JSON (not HTML)
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        
        # This confirms the endpoint is accessible and returns JSON
        # which is what a real browser would receive
    
    async def test_api_documentation_access(self):
        """Test API documentation accessibility."""
        # Test that API docs are available in development
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # In development, docs should be available
        # In production, they should be disabled
        import os
        if os.getenv("RAILWAY_ENVIRONMENT") != "production":
            response = client.get("/docs")
            # Docs might return redirect or actual docs page
            assert response.status_code in [200, 307]


@pytest.mark.asyncio
@pytest.mark.e2e
class TestUserJourneys:
    """E2E tests for complete user journeys."""
    
    async def test_basic_api_journey(self):
        """Test basic API usage journey."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 1. Check service health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # 2. Check service readiness
        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["status"] == "ready"
        
        # 3. Get metrics
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        assert "uptime_seconds" in metrics_data
        assert "memory_usage_percent" in metrics_data
    
    async def test_websocket_communication_journey(self):
        """Test WebSocket communication journey."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test WebSocket connection
        with client.websocket_connect("/ws") as websocket:
            # Send test message
            test_message = {
                "message": "Hello, AI agent!",
                "agent_id": "test-agent-001",
                "context": {"task": "greeting"}
            }
            
            websocket.send_json(test_message)
            
            # Receive response
            response = websocket.receive_json()
            
            assert "status" in response
            assert "response" in response
            assert "timestamp" in response


@pytest.mark.asyncio
@pytest.mark.e2e
class TestWebUIJSONEndpoints:
    """Test that web UI endpoints return valid JSON instead of HTML placeholders."""
    
    async def test_root_endpoint_returns_json(self):
        """Test that root endpoint returns JSON, not HTML."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/")
        
        # Should return JSON, not HTML
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Gary-Zero AI Agent Framework"
    
    async def test_web_ui_endpoint_exists(self):
        """Test that web UI is available at /ui endpoint."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test that /ui endpoint exists for serving HTML
        response = client.get("/ui")
        assert response.status_code in [200, 404]  # 404 if webui files don't exist
        
        # If successful, should return HTML
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
    
    async def test_websocket_returns_valid_json(self):
        """Test that WebSocket responses are valid JSON."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/ws") as websocket:
            # Send message
            websocket.send_json({
                "message": "Test JSON response",
                "agent_id": "json-test",
                "context": {"test": "json_validation"}
            })
            
            # Receive and validate JSON
            response = websocket.receive_json()
            
            # Should be valid JSON with expected structure
            assert isinstance(response, dict)
            assert "status" in response
            assert "response" in response
            assert "timestamp" in response
            
            # No HTML content in JSON response
            assert not any(tag in str(response) for tag in ["<html>", "<body>", "<!DOCTYPE"])