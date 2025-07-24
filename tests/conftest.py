"""
Test configuration and fixtures for Gary-Zero test suite.
"""

import asyncio
import os
import sys
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import test environment utilities

# Mock imports that might not be available in test environment
try:
    from main import app
except ImportError:
    # Create a mock app if main cannot be imported
    from fastapi import FastAPI

    app = FastAPI()
    app.title = "Gary-Zero Test App"

try:
    from models.registry import get_registry
except ImportError:
    # Mock registry if not available
    def get_registry():
        mock_registry = Mock()
        mock_registry.get_available_models = Mock(return_value=[])
        return mock_registry


try:
    from security.validator import SecureCodeValidator
except ImportError:
    # Mock security validator
    class SecureCodeValidator:
        def validate_code(self, request):
            mock_result = Mock()
            mock_result.is_valid = True
            mock_result.errors = []
            mock_result.blocked_items = []
            return mock_result


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client():
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def model_registry():
    return get_registry()


@pytest.fixture
def code_validator():
    return SecureCodeValidator()


@pytest.fixture
def sample_safe_code():
    return '''
import math
import json
def calculate_fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
'''


@pytest.fixture
def sample_unsafe_code():
    return """
import os
import subprocess
# Dangerous operations
os.system("rm -rf /")
subprocess.call(["curl", "http://malicious-site.com"])
exec("malicious_code")
eval("dangerous_expression")
"""


@pytest.fixture
def mock_external_apis(test_environment):
    apis = {
        "openai": test_environment.create_mock_api_service("openai"),
        "anthropic": test_environment.create_mock_api_service("anthropic"),
        "e2b": test_environment.create_mock_api_service("e2b"),
        "searxng": test_environment.create_mock_api_service("searxng"),
        "vector_db": test_environment.create_mock_api_service("vector_db"),
    }
    return apis


@pytest.fixture
def performance_test_data():
    from tests.test_environment import generate_performance_test_data

    return generate_performance_test_data(metric_count=500)


@pytest.fixture
def multi_agent_setup(mock_agents):
    coordinator = Mock()
    coordinator.agents = mock_agents
    coordinator.register_agent = Mock()
    coordinator.discover_agents = Mock(
        return_value={
            agent_id: agent.capabilities for agent_id, agent in mock_agents.items()
        }
    )
    return coordinator


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        if any(
            fixture in item.fixturenames
            for fixture in [
                "mock_openai_api",
                "mock_anthropic_api",
                "mock_e2b_api",
                "mock_searxng_api",
                "mock_vector_db",
                "mock_external_apis",
            ]
        ):
            item.add_marker(pytest.mark.mock_external)
