# Contributing to Gary-Zero

Thank you for your interest in contributing to Gary-Zero! This guide will help you get started with the development process.

## 🚀 CI/CD Pipeline Overview

Gary-Zero features a modern, modular CI/CD pipeline built around 4 reusable composite workflows:

### 🧩 Composite Workflows

| Workflow | Purpose | Components |
|----------|---------|------------|
| **A. Static Checks** | Code quality & consistency | Ruff, MyPy, ESLint, TypeScript, Secret scanning |
| **B. Tests** | Comprehensive testing | Unit, Integration, E2E, Performance, Coverage reporting |
| **C. Security Audit** | Multi-layer security scanning | Bandit, Safety, npm audit, OSSF Scorecard |
| **D. Deploy** | Production deployment | Railway validation, Docker build, health checks |

### 🔄 Usage Patterns

- **Feature Branches**: Uses workflows A + B (static checks + tests)
- **Main Branch**: Uses full pipeline A + B + C + D (complete CI/CD)
- **Quality Gate**: All checks must pass before deployment
- **Railway Integration**: Automated deployment with health verification

### 🏃‍♂️ Running CI Pipeline Locally

**Quick Start:**
```bash
# Run the complete CI pipeline locally
make ci

# Or run individual components
make setup       # Setup development environment
make lint        # Code quality checks
make test        # Run all tests
make security    # Security scans
make quick-check # Fast checks without tests
```

**Available Commands:**
```bash
make help        # Show all available commands
make format      # Auto-fix formatting issues
make docker-build # Test Docker build locally
make clean       # Clean up build artifacts
```

## Development Setup

### Prerequisites

- Python 3.13 or higher
- Node.js 22 or higher
- Git
- Docker (for local testing)
- Make (for running CI pipeline)

### Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/GaryOcean428/gary-zero.git
cd gary-zero
```

2. Run automated setup:
```bash
make setup
```

This will:
- Install Python and Node.js dependencies
- Set up pre-commit hooks
- Create necessary directories
- Validate the development environment

### Manual Setup (if needed)

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-dev.txt
npm ci
```

3. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
npm run prepare
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

## Railpack Configuration & Deployment

### Understanding Railpack

Railpack is Railway's deployment descriptor system that defines how your application is built and deployed. Gary-Zero uses a `railpack.json` file to configure the deployment pipeline.

### Required Railpack Configuration

```json
{
  "$schema": "./.github/schemas/railpack.schema.json",
  "builder": "NIXPACKS",
  "buildCommand": "bash scripts/build.sh",
  "startCommand": "bash scripts/start.sh",
  "healthcheckPath": "/health",
  "healthcheckTimeout": 300,
  "restartPolicyType": "ON_FAILURE",
  "restartPolicyMaxRetries": 3,
  "environment": {
    "PORT": "${PORT}",
    "WEB_UI_HOST": "0.0.0.0",
    "PYTHONUNBUFFERED": "1"
  }
}
```

### Railpack Rules & Requirements

#### 1. Required Fields
- **`builder`**: Must be one of `NIXPACKS`, `DOCKERFILE`, or `BUILDPACKS`
- **`buildCommand`**: Command to build the application
- **`startCommand`**: Command to start the application
- **`healthcheckPath`**: Health check endpoint (must start with `/`)

#### 2. PORT Environment Variable
**CRITICAL**: Your application MUST use Railway's dynamic PORT assignment.

**✅ Correct configurations:**
```json
// Option 1: Environment variable
"environment": {
  "PORT": "${PORT}"
}

// Option 2: In start command
"startCommand": "python app.py --port $PORT"

// Option 3: In scripts
"startCommand": "bash scripts/start.sh"
// where start.sh references $PORT
```

**❌ Incorrect configurations:**
```json
// Hard-coded port
"environment": {
  "PORT": "8080"
}

// No PORT reference
"startCommand": "python app.py"
```

#### 3. Health Check Requirements
- Path must start with `/` (e.g., `/health`, `/api/health`)
- Endpoint must return HTTP 200 when service is healthy
- Should respond within the configured timeout (default: 300s)

#### 4. Script Files
- Referenced scripts must exist and be executable
- Use `chmod +x scripts/*.sh` to make scripts executable
- Scripts should handle errors gracefully

### Common Railpack Failure Messages

#### ❌ "railpack.json not found"
**Cause**: Missing railpack.json file in repository root  
**Solution**: Create railpack.json with required configuration

#### ❌ "Invalid JSON syntax in railpack.json"
**Cause**: Malformed JSON (missing commas, quotes, brackets)  
**Solution**: Validate JSON syntax with `jq empty railpack.json`

#### ❌ "Missing required fields"
**Cause**: One of builder, buildCommand, startCommand, or healthcheckPath is missing  
**Solution**: Add all required fields to railpack.json

#### ❌ "PORT environment variable not properly configured"
**Cause**: PORT is not set to `${PORT}` or referenced in scripts  
**Solution**: Set `"PORT": "${PORT}"` in environment section OR reference `$PORT` in your start command/scripts

#### ❌ "Health check path doesn't start with '/'"
**Cause**: healthcheckPath is missing leading slash  
**Solution**: Change `"healthcheckPath": "health"` to `"healthcheckPath": "/health"`

#### ❌ "Build script not found" / "Start script not found"
**Cause**: Referenced script files don't exist  
**Solution**: 
- Create the missing script files
- Make them executable: `chmod +x scripts/build.sh scripts/start.sh`
- Ensure scripts are committed to repository

#### ❌ "Builder must be one of: NIXPACKS, DOCKERFILE, BUILDPACKS"
**Cause**: Invalid builder value  
**Solution**: Use one of the three supported builders

### Validating Railpack Configuration

```bash
# Local validation
make railpack-validate

# Manual validation
jq empty railpack.json                    # Check JSON syntax
jq '.builder' railpack.json               # Check builder
jq '.environment.PORT' railpack.json      # Check PORT config
```

### Railway Deployment Best Practices

1. **Environment Variables**: Use Railway's environment variable system instead of `.env` files
2. **Health Checks**: Implement comprehensive health checks that verify all critical services
3. **Graceful Shutdown**: Handle SIGTERM signals for graceful shutdowns
4. **Logging**: Use structured logging that Railway can parse and display
5. **Resource Limits**: Consider memory and CPU limits for your service size

### Debugging Deployment Issues

1. **Check Railway Logs**: View build and runtime logs in Railway dashboard
2. **Local Testing**: Use `make docker-build` to test container builds locally
3. **Health Check Testing**: Test your health endpoint manually
4. **Environment Variables**: Verify all required environment variables are set
5. **Script Permissions**: Ensure scripts are executable and have correct paths

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