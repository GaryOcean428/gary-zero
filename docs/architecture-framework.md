# Gary-Zero Framework Architecture Guide

This document provides a comprehensive overview of the Gary-Zero framework architecture improvements, including the dependency injection container, security framework, performance optimizations, and interface-based design.

## 🏗️ Architecture Overview

The Gary-Zero framework has been enhanced with modern architectural patterns to support scalable, maintainable, and secure development:

### Core Components

1. **Dependency Injection Container** - Centralized service management
2. **Interface-Based Design** - Clear contracts and abstraction
3. **Security Framework** - Comprehensive input validation and protection
4. **Performance Framework** - Caching, monitoring, and optimization
5. **Activity Monitor** - Real-time application monitoring
6. **Testing Infrastructure** - Comprehensive test coverage

## 📦 Dependency Injection Container

### Overview

The DI container provides centralized service management with automatic dependency resolution, lifecycle management, and different registration patterns.

### Features

- **Singleton Registration**: Single instance shared across application
- **Factory Registration**: Create new instance on each request
- **Service Registration**: Class-based registration with dependency injection
- **Type-based Resolution**: Get services by type annotation
- **Lifecycle Management**: Initialize and shutdown hooks

### Usage Examples

```python
from framework.container import get_container
from framework.interfaces import BaseService

# Get the global container
container = get_container()

# Register a singleton
container.register_singleton("config", {"api_key": "secret"})

# Register a service class
class UserService(BaseService):
    def __init__(self, config: dict):
        self.config = config
        
container.register_service("user_service", UserService)

# Get services (dependencies auto-injected)
config = container.get("config")
user_service = container.get("user_service")

# Initialize all services
await container.initialize_services()

# Shutdown when done
await container.shutdown_services()
```

### Advanced Features

```python
# Get service by type
user_service = container.get_by_type(UserService)

# List all registered services
services = container.list_registered()

# Factory registration
container.register_factory("uuid", lambda: str(uuid.uuid4()))
```

## 🔐 Security Framework

### Overview

Comprehensive security framework providing input validation, rate limiting, audit logging, and content sanitization.

### Components

1. **InputValidator** - Validates user input, tool parameters, and configuration
2. **RateLimiter** - Multiple rate limiting algorithms (sliding window, token bucket, fixed window)
3. **AuditLogger** - Security event logging and analysis
4. **ContentSanitizer** - Content sanitization and suspicious pattern detection

### Input Validation

```python
from framework.security import InputValidator

validator = InputValidator()

# Validate user input
is_valid = validator.validate_user_input("user_input_123")

# Validate tool parameters
tool_params = {"file_path": "/safe/path", "action": "read"}
is_valid = validator.validate_tool_input("file_tool", tool_params)

# Validate configuration
config = {"api_key": "safe_key", "timeout": 30}
is_valid = validator.validate_config_input(config)
```

### Rate Limiting

```python
from framework.security import RateLimiter

# Initialize with custom limits
rate_limiter = RateLimiter()

# Check rate limit
allowed = rate_limiter.check_rate_limit("user_123", "api_call")
if not allowed:
    raise Exception("Rate limit exceeded")

# Get rate limit status
status = rate_limiter.get_rate_limit_status("user_123", "api_call")
print(f"Remaining: {status['remaining']}")
```

### Audit Logging

```python
from framework.security import AuditLogger

audit_logger = AuditLogger()

# Log user input
audit_logger.log_user_input("search query", "search_action")

# Log tool execution
audit_logger.log_tool_execution("file_reader", {"path": "/safe/file.txt"})

# Log security violation
audit_logger.log_security_violation("invalid_input", {"input": "malicious_code"})

# Get security summary
summary = audit_logger.get_security_summary()
print(f"Total events: {summary['total_events']}")
```

### Content Sanitization

```python
from framework.security import ContentSanitizer

sanitizer = ContentSanitizer()

# Sanitize basic text
clean_text = sanitizer.sanitize_basic_text("User input with <script>")

# Sanitize HTML with allowlist
clean_html = sanitizer.sanitize_html("<p>Safe content</p><script>unsafe</script>")

# Sanitize SQL input
clean_sql = sanitizer.sanitize_sql_input("user'; DROP TABLE users; --")

# Detect suspicious patterns
is_suspicious = sanitizer.detect_suspicious_patterns("../../../etc/passwd")
```

## ⚡ Performance Framework

### Overview

Comprehensive performance optimization framework including caching, async utilities, monitoring, and resource optimization.

### Components

1. **CacheManager** - Multi-tier caching (memory + persistent)
2. **PerformanceMonitor** - Real-time metrics and timing
3. **ResourceOptimizer** - Memory and CPU optimization
4. **BackgroundTaskManager** - Async task management
5. **Performance Decorators** - Easy-to-use optimization decorators

### Caching

```python
from framework.performance import CacheManager, cached

# Use cache manager directly
cache = CacheManager()
cache.set("key", "value", ttl=300)
value = cache.get("key")

# Use caching decorator
@cached(ttl=60)
def expensive_function(param):
    # Expensive computation
    return f"result_{param}"

# Async caching
async def async_function():
    await cache.set_async("async_key", "async_value")
    value = await cache.get_async("async_key")
```

### Performance Monitoring

```python
from framework.performance import PerformanceMonitor, timer

monitor = PerformanceMonitor()

# Use timing decorator
@timer()
def timed_function():
    # Function execution will be timed
    pass

# Use timing context
with monitor.timing_context("operation_name"):
    # Code to time
    pass

# Get metrics
metrics = monitor.get_metrics_summary()
print(f"Average execution time: {metrics.get('operation_name_avg', 0)}")
```

### Resource Optimization

```python
from framework.performance import memory_optimize, cpu_optimize

@memory_optimize()
def memory_intensive_function():
    # Function will be optimized for memory usage
    pass

@cpu_optimize()
def cpu_intensive_function():
    # Function will be optimized for CPU usage
    pass
```

### Background Task Management

```python
from framework.performance import BackgroundTaskManager

task_manager = BackgroundTaskManager()

# Submit tasks
async def async_task(data):
    await asyncio.sleep(1)
    return f"processed_{data}"

tasks = [lambda: async_task(f"data_{i}") for i in range(5)]
task_ids = await task_manager.submit_tasks(tasks)

# Wait for completion
results = await task_manager.wait_for_tasks(task_ids)
```

## 🔌 Interface-Based Design

### Overview

Clean interface definitions using Python protocols and abstract base classes for better architecture and testability.

### Core Interfaces

```python
from framework.interfaces import Service, Repository, ToolInterface, MessageBus

class MyService(Service):
    async def initialize(self) -> None:
        # Service initialization
        pass
        
    async def shutdown(self) -> None:
        # Service cleanup
        pass

class MyRepository(Repository):
    async def save(self, entity: Any) -> str:
        # Save entity and return ID
        pass
        
    async def find_by_id(self, entity_id: str) -> Any:
        # Find entity by ID
        pass
```

### BaseService Implementation

```python
from framework.interfaces import BaseService

class UserService(BaseService):
    def __init__(self):
        super().__init__()
        self.users = {}
        
    async def initialize(self):
        await super().initialize()
        # Custom initialization
        
    async def shutdown(self):
        # Custom cleanup
        await super().shutdown()
        
    def create_user(self, user_data):
        # Business logic
        pass
```

## 📊 Activity Monitor

### Overview

Real-time activity monitoring with live iframe integration for observing application behavior.

### Features

- **Live Activity Tracking** - Real-time monitoring of browser and coding activities
- **Dynamic Iframe** - Collapsible interface with modern glassmorphism design
- **Activity Types** - Browser navigation, code editing, API calls, iframe changes
- **Interactive Controls** - Toggle visibility, refresh, filter, clear activities
- **Auto-refresh** - Configurable refresh intervals with activity indicators

### Usage

```python
from framework.api.activity_monitor import ActivityMonitor

monitor = ActivityMonitor()

# Log activities
monitor.log_activity("browser_navigation", {"url": "https://example.com"})
monitor.log_activity("code_edit", {"file": "script.py", "changes": 10})
monitor.log_activity("api_call", {"endpoint": "/api/users", "method": "GET"})

# Get activities
activities = monitor.get_activities()
```

### Web Integration

The activity monitor includes a complete web interface accessible via `/activity_monitor` endpoint:

- Modern glassmorphism UI with gradient backgrounds
- Real-time updates every 3 seconds
- Activity filtering by type
- Load external URLs for monitoring
- Activity count indicators

## 🧪 Testing Infrastructure

### Overview

Comprehensive testing setup with pytest, coverage reporting, and integration tests.

### Test Structure

```
tests/
├── test_container.py              # DI container tests (90% coverage)
├── test_integration.py            # Integration tests
├── security/
│   └── test_security_framework.py # Security tests (76-83% coverage)
└── performance/
    └── test_performance.py        # Performance tests (66-84% coverage)
```

### Running Tests

```bash
# Run all tests with coverage
python -m pytest --cov=framework --cov-report=term-missing

# Run specific test suites
python -m pytest tests/test_container.py -v
python -m pytest tests/security/ -v
python -m pytest framework/tests/performance/ -v

# Run integration tests
python -m pytest tests/test_integration.py -v
```

### Test Coverage

- **Container Module**: 90% coverage
- **Security Modules**: 76-83% coverage across all components
- **Performance Modules**: 66-84% coverage across all components
- **Integration Tests**: Comprehensive end-to-end workflow testing

## 🚀 Getting Started

### Quick Setup

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the comprehensive demo
python examples/comprehensive_demo.py

# Run tests
python -m pytest --cov=framework

# Start development server with activity monitor
python run_ui.py
```

### Development Workflow

1. **Set up environment**: Install dependencies and configure tools
2. **Use DI container**: Register services and dependencies
3. **Add security**: Implement input validation and rate limiting
4. **Optimize performance**: Add caching and monitoring
5. **Write tests**: Create unit and integration tests
6. **Monitor activities**: Use activity monitor for debugging

## 📈 Performance Metrics

### Benchmarks

- **Cache Performance**: 1000 operations in <1.0s (set) and <0.5s (get)
- **Container Resolution**: Sub-millisecond service resolution
- **Security Validation**: High-throughput input validation
- **Background Tasks**: Efficient async task management

### Monitoring

- **Real-time Metrics**: CPU, memory, I/O, and network tracking
- **Statistical Analysis**: Min, max, average, percentile calculations
- **Resource Tracking**: Automatic resource optimization
- **Performance Timers**: Decorator-based timing with context managers

## 🔒 Security Features

### Protection Layers

1. **Input Validation**: Multi-layer validation for all user inputs
2. **Rate Limiting**: Configurable rate limiting with multiple algorithms
3. **Content Sanitization**: XSS, SQL injection, and malicious content protection
4. **Audit Logging**: Comprehensive security event tracking
5. **Pattern Detection**: Suspicious activity pattern recognition

### Security Best Practices

- Always validate inputs at service boundaries
- Use rate limiting for public APIs
- Log security events for analysis
- Sanitize content before processing
- Monitor for suspicious patterns

## 🔧 Configuration

### Container Configuration

```python
# Configure container with custom settings
container.configure({
    "auto_wire": True,
    "strict_mode": False,
    "lifecycle_timeout": 30
})
```

### Security Configuration

```python
# Configure security components
validator = InputValidator(config={
    "max_input_length": 10000,
    "allowed_patterns": [r"^[a-zA-Z0-9_]+$"],
    "blocked_patterns": [r"<script", r"javascript:"]
})

rate_limiter = RateLimiter(config={
    "default_window_size": 3600,  # 1 hour
    "default_max_requests": 100,
    "algorithm": "sliding_window"
})
```

### Performance Configuration

```python
# Configure performance components
cache_manager = CacheManager(config={
    "memory_cache_size": 1000,
    "persistent_cache_path": "./cache",
    "default_ttl": 300
})

monitor = PerformanceMonitor(config={
    "enable_resource_tracking": True,
    "metrics_retention_hours": 24,
    "alert_thresholds": {"cpu": 80, "memory": 90}
})
```

## 🎯 Best Practices

### Service Design

1. **Single Responsibility**: Each service should have one clear purpose
2. **Dependency Injection**: Use constructor injection for dependencies
3. **Interface Contracts**: Define clear interfaces for services
4. **Lifecycle Management**: Implement proper initialization and shutdown
5. **Error Handling**: Use custom exceptions and proper error logging

### Security Implementation

1. **Defense in Depth**: Multiple security layers
2. **Fail Secure**: Default to secure behavior on errors
3. **Audit Everything**: Log all security-relevant events
4. **Rate Limit**: Protect against abuse and DoS attacks
5. **Sanitize Inputs**: Clean all user-provided content

### Performance Optimization

1. **Cache Strategically**: Cache expensive operations with appropriate TTL
2. **Monitor Continuously**: Track performance metrics in real-time
3. **Optimize Resources**: Use memory and CPU optimization decorators
4. **Async Where Possible**: Use async operations for I/O bound tasks
5. **Background Processing**: Offload long-running tasks

This architecture provides a solid foundation for building scalable, secure, and high-performance applications with the Gary-Zero framework.