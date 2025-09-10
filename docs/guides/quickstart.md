# Gary-Zero Framework - Quick Start Guide

## Overview

Gary-Zero is a sophisticated AI assistant framework with multi-provider AI integrations, clean architecture, and enterprise-grade security features. This guide will help you get started quickly.

## 🚀 Quick Installation

### Prerequisites

- Python 3.12+
- Redis (optional, for distributed caching)
- PostgreSQL (optional, for persistent storage)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/GaryOcean428/gary-zero.git
   cd gary-zero
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp example.env .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**
   ```bash
   # CLI interface
   python run_cli.py
   
   # Web interface
   python run_ui.py
   ```

## 🏗️ Architecture Overview

Gary-Zero implements a modern, layered architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Application   │    │   Infrastructure│
│   (API/Web UI)  │◄──►│   (Use Cases)   │◄──►│   (AI Providers)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
┌─────────────────────────────────────────────────────────────────┐
│                     Domain Layer                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐│
│  │  Entities   │ │   Events    │ │   Services  │ │ Value Objects││
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

- **Domain Layer**: Core business logic with entities, events, and services
- **Application Layer**: Use cases and orchestration logic
- **Infrastructure Layer**: External integrations (AI providers, databases)
- **Presentation Layer**: APIs and user interfaces

## 🤖 Creating Your First Agent

### Basic Agent Creation

```python
from framework.domain.services import AgentOrchestrationService
from framework.domain.value_objects import ModelConfiguration, SecurityContext

# Create security context
security_context = SecurityContext(
    user_id="user_123",
    session_id="session_456",
    permissions=["agent.create", "message.process"]
)

# Configure the AI model
model_config = ModelConfiguration(
    model_name="gpt-4",
    temperature=0.7,
    max_tokens=4096
)

# Create orchestration service
orchestrator = AgentOrchestrationService()

# Create agent
agent = await orchestrator.create_agent(
    name="Chat Assistant",
    agent_type="conversational",
    config=model_config,
    security_context=security_context
)

print(f"Created agent: {agent.id}")
```

### Processing Messages

```python
from framework.domain.services import MessageProcessingService
from framework.domain.entities import Message

# Create message processing service
processor = MessageProcessingService()

# Create a message
message = Message(
    content="Hello, how are you?",
    sender_id="user_123",
    recipient_id=agent.id
)

# Process the message
result = await processor.process_message(
    message, 
    agent.id, 
    security_context
)

print(f"Response: {result['response']}")
```

## 🔒 Security Features

### Input Validation

Gary-Zero provides comprehensive input validation:

```python
from framework.security.enhanced_sanitizer import sanitize_and_validate_input

# Define validation rules
validation_rules = {
    "message": {
        "required": True,
        "type": str,
        "max_length": 10000
    },
    "model": {
        "type": str,
        "allowed_values": ["gpt-4", "claude-3", "gemini-pro"]
    }
}

# Validate and sanitize input
clean_data = sanitize_and_validate_input(user_input, validation_rules)
```

### Rate Limiting

```python
from framework.security.enhanced_rate_limiter import create_rate_limiter

# Create rate limiter
rate_limiter = create_rate_limiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_limit=10
)

# Check rate limit
result = await rate_limiter.check_rate_limit("user_123", "api.chat")
if not result.allowed:
    print(f"Rate limited. Try again in {result.retry_after} seconds")
```

## 🚀 Performance Features

### Caching

```python
from framework.performance.caching.multi_level_cache import create_cache_hierarchy

# Create cache hierarchy
cache = create_cache_hierarchy(redis_client=redis_client)

# Cache decorator
from framework.performance.caching.multi_level_cache import cached

@cached(cache, ttl=300)
async def expensive_operation(param1, param2):
    # Expensive computation
    return result
```

### Event-Driven Architecture

```python
from framework.domain.events import get_event_bus, AgentCreatedEvent

# Get event bus
event_bus = get_event_bus()

# Register event handler
async def on_agent_created(event: AgentCreatedEvent):
    print(f"Agent created: {event.agent_id}")

event_bus.register_handler("agent.created", on_agent_created)

# Events are automatically published by domain entities
agent.activate()  # This publishes AgentCreatedEvent
```

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# AI Provider API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/gary_zero
REDIS_URL=redis://localhost:6379

# Security Configuration
SECRET_KEY=your_secret_key_here
JWT_EXPIRATION=3600

# Rate Limiting
DEFAULT_RATE_LIMIT_PER_MINUTE=60
DEFAULT_RATE_LIMIT_PER_HOUR=1000
```

### Model Configuration

```python
# Configure multiple AI providers
model_configs = {
    "gpt-4": ModelConfiguration(
        model_name="gpt-4",
        temperature=0.7,
        max_tokens=4096
    ),
    "claude-3": ModelConfiguration(
        model_name="claude-3-sonnet",
        temperature=0.5,
        max_tokens=8192
    )
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/domain/          # Domain layer tests
pytest tests/security/        # Security tests
pytest tests/integration/     # Integration tests

# Run with coverage
pytest --cov=framework --cov=api --cov-report=html
```

### Writing Tests

```python
import pytest
from framework.domain.entities import Agent

class TestAgent:
    def test_agent_creation(self):
        agent = Agent(name="Test Agent", agent_type="chat")
        assert agent.name == "Test Agent"
        assert agent.status == "created"
    
    @pytest.mark.asyncio
    async def test_agent_activation(self):
        agent = Agent(name="Test Agent")
        agent.activate()
        
        assert agent.status == "active"
        
        # Check events
        events = agent.get_uncommitted_events()
        assert len(events) == 1
        assert events[0].event_type == "agent.created"
```

## 📊 Monitoring

### Health Checks

```python
# Built-in health check endpoints
GET /health              # Basic health status
GET /health/detailed     # Detailed component status
GET /api/health         # API-specific health checks
```

### Metrics

```python
from framework.performance.monitor import get_performance_monitor

monitor = get_performance_monitor()

# Custom metrics
monitor.increment_counter("requests_processed")
monitor.record_histogram("request_duration", duration_ms)
monitor.set_gauge("active_agents", agent_count)
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Use the provided Dockerfile
docker build -t gary-zero .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key gary-zero
```

### Railway Deployment

```bash
# Deploy to Railway
railway login
railway init
railway deploy
```

### Environment Setup

```bash
# Production environment variables
railway variables set ENVIRONMENT=production
railway variables set OPENAI_API_KEY=your_key
railway variables set DATABASE_URL=your_db_url
```

## 📚 Next Steps

- **[API Documentation](api.md)**: Detailed API reference
- **[Architecture Guide](architecture.md)**: Deep dive into the architecture
- **[Security Guide](security.md)**: Security best practices
- **[Performance Guide](performance.md)**: Optimization techniques
- **[Examples](../examples/)**: Complete examples and use cases

## 🆘 Getting Help

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and API reference
- **Examples**: Ready-to-use code examples
- **Community**: Join our Discord server for discussions

## 🔗 Additional Resources

- [Complete API Reference](api.md)
- [Architecture Deep Dive](architecture.md)
- [Security Best Practices](security.md)
- [Deployment Guide](deployment.md)
- [Contributing Guidelines](../CONTRIBUTING.md)