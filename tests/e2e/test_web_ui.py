"""
End-to-end tests for web UI workflows.
"""

import pytest
from playwright.async_api import async_playwright
import asyncio

@pytest.mark.asyncio
@pytest.mark.e2e
class TestWebUIWorkflows:
    """E2E tests for web UI functionality."""
    
    async def test_health_endpoint_accessibility(self):
        """Test that health endpoint is accessible."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Test health endpoint (would need actual server running)
                # For now, we'll test the endpoint structure
                from main import app
                from fastapi.testclient import TestClient
                
                client = TestClient(app)
                response = client.get("/health")
                assert response.status_code == 200
                
            finally:
                await browser.close()
    
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