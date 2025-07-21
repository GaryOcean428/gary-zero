# Contributing to Gary-Zero

Thank you for your interest in contributing to Gary-Zero! This guide will help you get started with the development process.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setting up the Development Environment

1. Clone the repository:
```bash
git clone https://github.com/GaryOcean428/gary-zero.git
cd gary-zero
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Code Quality Standards

### Linting and Formatting

We use several tools to maintain code quality:

- **Ruff**: For linting and code formatting
- **MyPy**: For static type checking
- **Pytest**: For testing with coverage reporting

### Running Quality Checks

```bash
# Lint and format code
ruff check --fix .
ruff format .

# Type checking
mypy framework/ --ignore-missing-imports

# Run tests with coverage
pytest --cov=framework --cov-report=term-missing
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality:

- Trailing whitespace removal
- End-of-file fixing
- YAML/TOML/JSON validation
- Code linting and formatting
- Type checking
- Test execution

## Architecture Guidelines

### Dependency Injection

Gary-Zero uses a dependency injection container for managing services:

```python
from framework.container import get_container
from framework.interfaces import BaseService

class MyService(BaseService):
    async def initialize(self):
        # Service initialization logic
        await self._set_initialized()
    
    async def shutdown(self):
        # Service cleanup logic
        await self._set_shutdown()

# Register the service
container = get_container()
container.register_service("my_service", MyService)
```

### Service Interfaces

All services should implement the `Service` protocol:

```python
from framework.interfaces import Service

class MyService(Service):
    async def initialize(self) -> None:
        # Initialize the service
        pass
    
    async def shutdown(self) -> None:
        # Clean shutdown
        pass
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
```

## Testing Guidelines

### Writing Tests

- Use pytest for all tests
- Write both unit and integration tests
- Mock external dependencies
- Aim for high test coverage

### Test Structure

```python
import pytest
from unittest.mock import MagicMock

class TestMyService:
    def setup_method(self):
        """Setup before each test method."""
        pass
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        # Test implementation
        pass
    
    def test_service_configuration(self):
        """Test service configuration."""
        # Test implementation
        pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=framework

# Run specific test file
pytest tests/test_container.py

# Run tests matching pattern
pytest -k "test_container"
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes following the coding standards
4. **Write** tests for your changes
5. **Ensure** all tests pass and coverage is maintained
6. **Update** documentation if needed
7. **Submit** a pull request with a clear description

### Pull Request Requirements

- [ ] All tests pass
- [ ] Code coverage is maintained
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are descriptive

## Code Style

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions and methods
- Write descriptive docstrings
- Keep functions and classes focused and small
- Use meaningful variable and function names

### Example Code

```python
"""Module for handling user authentication."""

from typing import Optional
from framework.interfaces import BaseService

class AuthenticationService(BaseService):
    """Service for handling user authentication and authorization."""
    
    def __init__(self, config: dict[str, str]) -> None:
        """Initialize the authentication service.
        
        Args:
            config: Configuration dictionary for the service.
        """
        super().__init__()
        self._config = config
        self._users: dict[str, str] = {}
    
    async def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate.
            password: The password to verify.
            
        Returns:
            User token if authentication successful, None otherwise.
        """
        # Implementation here
        pass
```

## Documentation

### Code Documentation

- Write clear docstrings for all public functions and classes
- Include type information in docstrings
- Provide examples where helpful
- Document complex algorithms and business logic

### API Documentation

- Use proper HTTP status codes
- Document all endpoints
- Provide request/response examples
- Include error scenarios

## Security Guidelines

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices
- Use HTTPS for all external communications

## Getting Help

- Check existing issues and documentation
- Ask questions in discussions
- Reach out to maintainers for guidance
- Join our community channels

Thank you for contributing to Gary-Zero!