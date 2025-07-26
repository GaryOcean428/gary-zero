# Testing Guide for Gary-Zero

This document provides comprehensive guidance for running, writing, and maintaining tests in the Gary-Zero project.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Running Tests](#running-tests)
3. [Writing Tests](#writing-tests)
4. [Environment Configuration](#environment-configuration)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Coverage and Quality](#coverage-and-quality)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)
9. [Troubleshooting](#troubleshooting)

## Test Structure

The Gary-Zero project uses a comprehensive testing strategy with multiple test types:

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_environment.py         # Mock services and test utilities
├── unit/                       # Fast, isolated unit tests
│   ├── test_performance_monitor.py
│   ├── test_a2a_communication.py
│   ├── test_security_validator.py
│   └── test_model_registry.py
├── integration/                # Tests with external dependencies
│   ├── test_multi_agent_coordination.py
│   ├── test_api_bridge.py
│   └── test_plugin_loading.py
├── e2e/                       # End-to-end system tests
│   └── test_web_ui.py
├── performance/               # Performance and benchmark tests
│   └── test_benchmark_suite.py
└── security/                  # Security-focused tests
    └── test_code_validation.py
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests with external dependencies
- `@pytest.mark.e2e` - End-to-end system tests
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.slow` - Tests that take longer than 1 second
- `@pytest.mark.mock_external` - Tests that mock external services

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

### Basic Test Execution

Run all tests:

```bash
pytest
```

Run specific test types:

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Performance tests
pytest -m performance

# Security tests
pytest -m security
```

Run tests with coverage:

```bash
pytest --cov=framework --cov=api --cov=security --cov-report=html
```

### Advanced Test Options

Run tests in parallel:

```bash
pytest -n auto  # Auto-detect CPU cores
pytest -n 4     # Use 4 processes
```

Run tests with benchmarking:

```bash
pytest --benchmark-only  # Only benchmark tests
pytest --benchmark-skip  # Skip benchmark tests
```

Run specific test files or functions:

```bash
pytest tests/unit/test_performance_monitor.py
pytest tests/unit/test_performance_monitor.py::TestMetricsCollector::test_record_metric
```

### JavaScript/TypeScript Tests

Run JavaScript tests using Vitest:

```bash
npm run test           # Run tests
npm run test:coverage  # Run with coverage
npm run test:ui        # Run with UI
npm run test:watch     # Watch mode
```

## Writing Tests

### Test Structure Guidelines

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use descriptive names**: Test names should explain what is being tested
3. **Keep tests focused**: One test should verify one behavior
4. **Use fixtures**: Leverage pytest fixtures for setup and teardown

### Unit Test Example

```python
import pytest
from framework.performance.monitor import MetricsCollector

class TestMetricsCollector:
    """Test cases for MetricsCollector class."""

    def test_record_metric_stores_value_correctly(self):
        """Test that recording a metric stores the value correctly."""
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record("test_metric", 42.0, tags={"env": "test"})

        # Assert
        latest = collector.get_latest("test_metric")
        assert latest is not None
        assert latest.value == 42.0
        assert latest.tags == {"env": "test"}
```

### Integration Test Example

```python
@pytest.mark.integration
class TestMultiAgentCoordination:
    """Integration tests for multi-agent coordination."""

    @pytest.mark.asyncio
    async def test_distributed_task_execution(self, coordinator):
        """Test distributed task execution across multiple agents."""
        # Arrange
        session_id = "test-session"
        await coordinator.create_workflow_session(session_id, ["agent-1", "agent-2"])

        task_definition = {
            "task_id": "integration-test",
            "subtasks": [
                {"id": "subtask-1", "required_capabilities": ["data_processing"]},
                {"id": "subtask-2", "required_capabilities": ["web_scraping"]}
            ]
        }

        # Act
        result = await coordinator.execute_distributed_task(session_id, task_definition)

        # Assert
        assert result["status"] == "completed"
        assert result["completed_subtasks"] > 0
```

### Performance Test Example

```python
@pytest.mark.performance
class TestPerformanceMetrics:
    """Performance benchmark tests."""

    def test_metrics_collection_performance(self, benchmark):
        """Benchmark metrics collection performance."""
        collector = MetricsCollector()

        def record_metrics():
            for i in range(1000):
                collector.record(f"metric_{i % 10}", float(i))

        # Benchmark the operation
        result = benchmark(record_metrics)

        # Verify performance expectations
        assert len(collector._metrics) == 10
```

### Mock Usage

Use the test environment for mocking external services:

```python
def test_api_call_with_mock(mock_openai_api):
    """Test API call using mocked OpenAI service."""
    # The mock is automatically configured in test_environment.py
    response = mock_openai_api.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Test message"}]
    )

    assert response.choices[0].message.content == "This is a mock response from OpenAI API"
```

## Environment Configuration

### Environment Variables

The test environment automatically configures these variables:

```python
TEST_CONFIG = {
    "PORT": "8080",
    "WEB_UI_HOST": "localhost",
    "SEARXNG_URL": "http://localhost:8080/mock-searxng",
    "E2B_API_KEY": "test-e2b-key-12345",
    "OPENAI_API_KEY": "test-openai-key-12345",
    # ... other test API keys
    "TESTING": "true"
}
```

### Mock Services

Mock services are available for testing without external dependencies:

- **OpenAI API**: Mock chat completions and embeddings
- **Anthropic API**: Mock Claude responses
- **E2B API**: Mock code execution sandboxes
- **SearXNG**: Mock search results
- **Vector Database**: Mock vector operations
- **Database**: Mock database sessions

### Custom Test Configuration

Create custom test configurations:

```python
@pytest.fixture
def custom_test_config():
    """Custom configuration for specific tests."""
    return {
        "CUSTOM_SETTING": "test_value",
        "TIMEOUT": "30",
        "MAX_RETRIES": "3"
    }

def test_with_custom_config(custom_test_config):
    """Test using custom configuration."""
    with patch.dict(os.environ, custom_test_config):
        # Your test code here
        pass
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline runs comprehensive tests:

1. **Code Quality**: Linting, type checking, security scanning
2. **Unit Tests**: Fast isolated tests with coverage
3. **Integration Tests**: Tests with mocked dependencies
4. **Performance Tests**: Benchmark execution and regression detection
5. **E2E Tests**: Full system testing with browser automation
6. **Coverage Reporting**: Upload to Codecov

### Pipeline Stages

```yaml
jobs:
  code-quality:
    # Ruff linting, MyPy type checking, Bandit security scan

  python-tests:
    strategy:
      matrix:
        test-type: [unit, integration, performance]
    # Parallel test execution with coverage

  e2e-tests:
    # End-to-end testing with Playwright

  deployment-validation:
    # Port configuration and Docker build validation
```

### Running Tests Locally Like CI

Simulate CI environment locally:

```bash
# Run the same checks as CI
python -m ruff check .
python -m mypy framework/
python -m bandit -r framework/ api/ security/
python -m pytest --cov=framework --cov-fail-under=80
```

## Coverage and Quality

### Coverage Requirements

- **Minimum Coverage**: 80% overall
- **Branch Coverage**: Required for critical paths
- **Coverage Reports**: HTML, XML, and terminal formats

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=framework --cov=api --cov=security --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Check coverage threshold
pytest --cov=framework --cov-fail-under=80
```

### Quality Tools

1. **Ruff**: Fast Python linter and formatter
2. **MyPy**: Static type checking
3. **Bandit**: Security vulnerability scanner
4. **Safety**: Dependency security checking
5. **Detect-secrets**: Secret detection and prevention

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

Run hooks manually:

```bash
pre-commit run --all-files
```

## Performance Testing

### Benchmark Tests

Write benchmark tests using pytest-benchmark:

```python
def test_performance_operation(benchmark):
    """Benchmark a performance-critical operation."""
    def operation_to_benchmark():
        # Your operation here
        return expensive_computation()

    result = benchmark(operation_to_benchmark)
    assert result is not None
```

### Performance Monitoring

Tests include performance monitoring:

- **Memory Usage**: Track memory growth during operations
- **Execution Time**: Measure operation duration
- **Concurrency**: Test performance under concurrent load
- **Resource Efficiency**: Monitor CPU and I/O usage

### Performance Thresholds

Set performance expectations:

```python
@pytest.mark.performance
def test_operation_performance():
    """Test that operation meets performance requirements."""
    start_time = time.time()

    # Perform operation
    result = expensive_operation()

    duration = time.time() - start_time
    assert duration < 5.0  # Should complete within 5 seconds
    assert result is not None
```

## Security Testing

### Security Test Categories

1. **Code Injection**: Test for code execution vulnerabilities
2. **Input Validation**: Verify input sanitization
3. **Authentication**: Test authentication mechanisms
4. **Authorization**: Verify permission checks
5. **Data Protection**: Test sensitive data handling

### Security Test Example

```python
@pytest.mark.security
def test_code_injection_prevention(code_validator, malicious_code_samples):
    """Test that code injection attempts are blocked."""
    for attack_name, malicious_code in malicious_code_samples.items():
        result = code_validator.validate_code(malicious_code)

        assert result.is_valid is False, f"Failed to block {attack_name}"
        assert len(result.blocked_items) > 0
```

### Security Tools Integration

- **Bandit**: Scans for security vulnerabilities in Python code
- **Safety**: Checks dependencies for known security issues
- **Detect-secrets**: Prevents secrets from being committed

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Environment Variables**: Check test environment configuration
3. **Mock Failures**: Verify mock service setup
4. **Timeout Issues**: Increase test timeouts for slow operations
5. **Coverage Failures**: Add tests for uncovered code paths

### Debug Test Execution

```bash
# Run tests with verbose output
pytest -v

# Run tests with detailed output
pytest -s

# Run tests with debugging
pytest --pdb

# Run specific test with debugging
pytest --pdb tests/unit/test_performance_monitor.py::TestMetricsCollector::test_record_metric
```

### Test Data and Fixtures

Use test fixtures for consistent test data:

```python
@pytest.fixture
def sample_test_data():
    """Provide sample data for testing."""
    return {
        "users": [
            {"id": 1, "name": "Test User 1"},
            {"id": 2, "name": "Test User 2"}
        ],
        "tasks": [
            {"id": 1, "title": "Test Task", "user_id": 1}
        ]
    }
```

### Mock Debugging

Debug mock services:

```python
def test_mock_debugging(mock_openai_api):
    """Debug mock service behavior."""
    # Check mock configuration
    assert mock_openai_api is not None

    # Verify mock calls
    response = mock_openai_api.chat.completions.create(model="gpt-4", messages=[])

    # Debug mock call history
    print(mock_openai_api.chat.completions.create.call_args_list)
```

### Performance Debugging

Debug performance issues:

```python
import cProfile
import pstats

def test_performance_debugging():
    """Debug performance of specific operation."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Your operation here
    expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Print top 10 functions
```

### Getting Help

1. Check the test output for specific error messages
2. Review the test configuration in `conftest.py` and `test_environment.py`
3. Ensure all test dependencies are installed: `pip install -r requirements-dev.txt`
4. Verify environment variables are set correctly
5. Check that mock services are properly configured
6. Review the CI pipeline logs for additional context

For additional support, refer to the project documentation or create an issue with:
- Test command used
- Full error output
- Environment details (Python version, OS, etc.)
- Steps to reproduce the issue
