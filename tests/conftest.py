"""
Test configuration and fixtures for Gary-Zero test suite.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app
from models.registry import get_registry
from security.validator import SecureCodeValidator

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def model_registry():
    """Get the model registry for testing."""
    return get_registry()

@pytest.fixture
def code_validator():
    """Create a code validator for testing."""
    return SecureCodeValidator()

@pytest.fixture
def sample_safe_code():
    """Sample safe code for testing."""
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
    """Sample unsafe code for testing."""
    return '''
import os
import subprocess

# Dangerous operations
os.system("rm -rf /")
subprocess.call(["curl", "http://malicious-site.com"])
exec("malicious_code")
eval("dangerous_expression")
'''

@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message for testing."""
    return {
        "message": "Hello, AI agent!",
        "agent_id": "test-agent-001",
        "context": {"task": "test", "priority": "high"}
    }