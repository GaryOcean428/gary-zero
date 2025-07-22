"""
Test configuration and fixtures for Gary-Zero test suite.
"""

import pytest
import asyncio
import sys
import os
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test environment utilities
from tests.test_environment import (
    get_test_environment, 
    mock_openai_api,
    mock_anthropic_api, 
    mock_e2b_api,
    mock_searxng_api,
    mock_vector_db,
    mock_database_session,
    temp_test_files,
    mock_performance_metrics,
    mock_agents,
    performance_tracker,
    security_test_helper
)

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
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
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


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment automatically for all tests."""
    test_env = get_test_environment()
    
    # Patch external dependencies that might not be available
    with patch.dict(os.environ, test_env.test_config):
        yield test_env
    
    # Cleanup after all tests
    test_env.cleanup()


@pytest.fixture
def mock_external_apis(test_environment):
    """Mock all external APIs for testing."""
    apis = {
        'openai': test_environment.create_mock_api_service('openai'),
        'anthropic': test_environment.create_mock_api_service('anthropic'),
        'e2b': test_environment.create_mock_api_service('e2b'),
        'searxng': test_environment.create_mock_api_service('searxng'),
        'vector_db': test_environment.create_mock_api_service('vector_db')
    }
    return apis


@pytest.fixture
def isolated_test_environment(test_environment):
    """Create an isolated test environment for tests that modify state."""
    # Create a copy of the test environment for isolation
    isolated_env = get_test_environment()
    yield isolated_env
    # Reset any changes after the test
    isolated_env.cleanup()


# Performance testing fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for benchmark tests."""
    return {
        "min_rounds": 5,
        "max_time": 10.0,
        "warmup_rounds": 2,
        "disable_gc": False,
        "timer": "time.perf_counter"
    }


# Security testing fixtures  
@pytest.fixture
def malicious_code_samples(security_test_helper):
    """Get malicious code samples for security testing."""
    return security_test_helper.create_malicious_code_samples()


@pytest.fixture
def safe_code_samples(security_test_helper):
    """Get safe code samples for security testing."""
    return security_test_helper.create_safe_code_samples()


# Data generation fixtures
@pytest.fixture
def test_message_data():
    """Generate test message data."""
    from tests.test_environment import generate_test_message_data
    return generate_test_message_data(count=20)


@pytest.fixture
def performance_test_data():
    """Generate performance test data."""
    from tests.test_environment import generate_performance_test_data
    return generate_performance_test_data(metric_count=500)


# Database testing fixtures
@pytest.fixture
def clean_database():
    """Provide a clean database state for testing."""
    # This would typically reset the test database
    # For now, we'll use a mock
    mock_db = Mock()
    mock_db.reset = Mock()
    mock_db.reset()
    yield mock_db


# File system testing fixtures
@pytest.fixture
def temp_workspace(temp_test_files):
    """Create a temporary workspace for file operations."""
    workspace_files = {
        "test_data.json": '{"test": "data", "numbers": [1, 2, 3]}',
        "test_script.py": 'print("Hello from test script")',
        "config.yaml": 'setting1: value1\nsetting2: value2',
        "data/sample.csv": 'id,name,value\n1,test,100\n2,demo,200',
    }
    
    file_paths = temp_test_files(workspace_files)
    yield file_paths


# Network testing fixtures
@pytest.fixture
def mock_network_responses():
    """Mock network responses for testing."""
    responses = {
        "api_success": {
            "status_code": 200,
            "json": {"status": "success", "data": {"result": "test_result"}},
            "headers": {"Content-Type": "application/json"}
        },
        "api_error": {
            "status_code": 500,
            "json": {"error": "Internal server error"},
            "headers": {"Content-Type": "application/json"}
        },
        "api_timeout": {
            "status_code": 408,
            "json": {"error": "Request timeout"},
            "headers": {"Content-Type": "application/json"}
        }
    }
    return responses


# Agent testing fixtures
@pytest.fixture
def multi_agent_setup(mock_agents):
    """Set up multiple agents for coordination testing."""
    coordinator = Mock()
    coordinator.agents = mock_agents
    coordinator.register_agent = Mock()
    coordinator.discover_agents = Mock(return_value={
        agent_id: agent.capabilities 
        for agent_id, agent in mock_agents.items()
    })
    return coordinator


# Plugin testing fixtures
@pytest.fixture
def mock_plugin_system():
    """Mock plugin system for testing."""
    plugin_system = Mock()
    plugin_system.loaded_plugins = {}
    plugin_system.available_plugins = {
        "test_plugin": {
            "name": "test_plugin",
            "version": "1.0.0",
            "capabilities": ["test_capability"],
            "status": "available"
        }
    }
    
    async def mock_load_plugin(name):
        if name in plugin_system.available_plugins:
            plugin_system.loaded_plugins[name] = plugin_system.available_plugins[name].copy()
            plugin_system.loaded_plugins[name]["status"] = "loaded"
            return True
        return False
    
    plugin_system.load_plugin = mock_load_plugin
    return plugin_system


# Configuration for different test markers
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add slow marker to tests that take longer than normal
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker to tests in integration directory
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to tests in unit directory
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add e2e marker to tests in e2e directory
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Add mock_external marker to tests that use mock APIs
        if any(fixture in item.fixturenames for fixture in [
            'mock_openai_api', 'mock_anthropic_api', 'mock_e2b_api', 
            'mock_searxng_api', 'mock_vector_db', 'mock_external_apis'
        ]):
            item.add_marker(pytest.mark.mock_external)


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Perform any necessary cleanup
    import gc
    gc.collect()


# Skip markers for CI environment
def pytest_runtest_setup(item):
    """Set up individual test runs."""
    # Skip certain tests in CI if needed
    if "CI" in os.environ:
        if item.get_closest_marker("skip_in_ci"):
            pytest.skip("Skipped in CI environment")
        
        # Reduce test complexity in CI
        if item.get_closest_marker("performance"):
            # Set shorter timeouts for performance tests in CI
            item.config.option.benchmark_timeout = 5.0