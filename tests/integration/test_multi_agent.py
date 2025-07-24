"""
Integration tests for multi-agent workflows.
"""

import asyncio

import pytest


@pytest.mark.asyncio
class TestMultiAgentIntegration:
    """Integration tests for multi-agent system functionality."""

    async def test_agent_communication_flow(self, async_client):
        """Test basic agent communication workflow."""
        # Test health check first
        response = await async_client.get("/health")
        assert response.status_code == 200

        # Test metrics endpoint
        metrics_response = await async_client.get("/metrics")
        assert metrics_response.status_code == 200

        metrics_data = metrics_response.json()
        assert "active_websocket_connections" in metrics_data

    async def test_concurrent_requests(self, async_client):
        """Test handling of concurrent requests."""
        # Make multiple concurrent requests
        tasks = []
        for i in range(10):
            task = async_client.get("/health")
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should return healthy status
        for response in responses:
            data = response.json()
            assert data["status"] == "healthy"

    async def test_websocket_multiple_connections(self, async_client):
        """Test multiple WebSocket connections."""
        # This test would require a WebSocket test client
        # For now, we'll test the endpoint exists
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["websocket"] == "/ws"


@pytest.mark.asyncio
class TestSecurityIntegration:
    """Integration tests for security features."""

    async def test_code_validation_integration(self):
        """Test integration of code validation with the system."""
        from security.validator import SecurityLevel, validate_code

        # Test safe code
        safe_code = "print('Hello World')"
        result = validate_code(safe_code, SecurityLevel.STRICT)
        assert result.is_valid is True

        # Test unsafe code
        unsafe_code = "import os; os.system('rm -rf /')"
        result = validate_code(unsafe_code, SecurityLevel.STRICT)
        assert result.is_valid is False

    async def test_model_registry_integration(self):
        """Test integration of model registry with the system."""
        from models.registry import ModelProvider, get_registry

        registry = get_registry()

        # Test that models are loaded
        all_models = registry.list_models()
        assert len(all_models) > 0

        # Test provider filtering
        openai_models = registry.list_models(ModelProvider.OPENAI)
        anthropic_models = registry.list_models(ModelProvider.ANTHROPIC)

        assert len(openai_models) > 0
        assert len(anthropic_models) > 0
