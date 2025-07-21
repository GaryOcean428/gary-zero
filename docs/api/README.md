# Gary-Zero Framework API Documentation

## Overview

The Gary-Zero framework provides a comprehensive set of APIs for building AI agents with dependency injection, service management, and tool execution capabilities.

## Core Components

### Dependency Injection Container

The container manages service instances and handles dependency resolution.

#### Container Class

```python
from framework.container import Container, get_container

# Get the global container instance
container = get_container()

# Register services
container.register_singleton("config", config_instance)
container.register_service("my_service", MyServiceClass)
container.register_factory("temp_service", lambda: TempService())

# Retrieve services
service = container.get("my_service")
service_by_type = container.get_by_type(MyServiceClass)
```

**Methods:**

- `register_singleton(name: str, instance: Any)` - Register a singleton instance
- `register_service(name: str, service_class: type)` - Register a service class
- `register_factory(name: str, factory: Callable, type_hint: Optional[type])` - Register a factory function
- `get(name: str) -> Any` - Get service by name
- `get_by_type(service_type: type[T]) -> T` - Get service by type
- `initialize_services() -> None` - Initialize all services
- `shutdown_services() -> None` - Shutdown all services

### Service Interfaces

#### BaseService

Abstract base class for framework services with lifecycle management.

```python
from framework.interfaces import BaseService

class MyService(BaseService):
    async def initialize(self) -> None:
        """Initialize the service."""
        # Initialization logic here
        await self._set_initialized()
    
    async def shutdown(self) -> None:
        """Shutdown the service."""
        # Cleanup logic here
        await self._set_shutdown()
```

**Properties:**

- `is_initialized: bool` - Check if service is initialized

**Methods:**

- `initialize() -> None` - Initialize the service (abstract)
- `shutdown() -> None` - Shutdown the service (abstract)

#### Service Protocol

Runtime checkable protocol for services.

```python
from framework.interfaces import Service

@runtime_checkable
class Service(Protocol):
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    @property
    def is_initialized(self) -> bool: ...
```

#### Repository Protocol

Protocol for data access repositories.

```python
from framework.interfaces import Repository

@runtime_checkable
class Repository(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    @property
    def is_connected(self) -> bool: ...
```

#### ToolInterface Protocol

Protocol for framework tools.

```python
from framework.interfaces import ToolInterface

@runtime_checkable
class ToolInterface(Protocol):
    @property
    def name(self) -> str: ...
    async def execute(self, **kwargs: Any) -> Any: ...
```

#### MessageBus Protocol

Protocol for message bus implementations.

```python
from framework.interfaces import MessageBus

@runtime_checkable
class MessageBus(Protocol):
    async def publish(self, topic: str, message: Any) -> None: ...
    async def subscribe(self, topic: str, handler: Any) -> None: ...
    async def unsubscribe(self, topic: str, handler: Any) -> None: ...
```

## Tool Framework

### Tool Base Class

```python
from framework.helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs) -> Response:
        """Execute the tool with given parameters."""
        result = self.do_work(**kwargs)
        return Response(
            message=f"Tool executed: {result}",
            break_loop=False
        )
```

### Response Class

```python
@dataclass
class Response:
    message: str      # Response message
    break_loop: bool  # Whether to break the execution loop
```

## Exception Classes

### DependencyError

Raised when there are dependency injection issues.

```python
from framework.interfaces import DependencyError

try:
    service = container.get("nonexistent_service")
except DependencyError as e:
    print(f"Service not found: {e}")
```

### ServiceError

Raised when there are service-related errors.

```python
from framework.interfaces import ServiceError

class MyService(BaseService):
    async def initialize(self):
        if not self.can_initialize():
            raise ServiceError("Service cannot be initialized")
```

### ConfigurationError

Raised when there are configuration issues.

```python
from framework.interfaces import ConfigurationError

def validate_config(config):
    if not config.get("required_field"):
        raise ConfigurationError("Required field missing")
```

## Usage Examples

### Basic Service Setup

```python
from framework.container import get_container
from framework.interfaces import BaseService

class DatabaseService(BaseService):
    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string
        self.connection = None
    
    async def initialize(self):
        # Connect to database
        self.connection = await connect(self.connection_string)
        await self._set_initialized()
    
    async def shutdown(self):
        # Close database connection
        if self.connection:
            await self.connection.close()
        await self._set_shutdown()

# Register and use the service
container = get_container()
container.register_singleton("db_config", "postgresql://localhost/mydb")
container.register_service("database", DatabaseService)

# Initialize all services
await container.initialize_services()

# Use the service
db_service = container.get("database")
```

### Dependency Injection Example

```python
class UserService(BaseService):
    def __init__(self, database: DatabaseService):
        super().__init__()
        self.database = database
    
    async def get_user(self, user_id: str):
        return await self.database.query("SELECT * FROM users WHERE id = ?", user_id)

# The container will automatically inject DatabaseService
container.register_service("user_service", UserService)
user_service = container.get("user_service")
```

### Tool Implementation

```python
from framework.helpers.tool import Tool, Response

class CalculatorTool(Tool):
    async def execute(self, **kwargs) -> Response:
        operation = kwargs.get("operation")
        a = float(kwargs.get("a", 0))
        b = float(kwargs.get("b", 0))
        
        if operation == "add":
            result = a + b
        elif operation == "multiply":
            result = a * b
        else:
            return Response(
                message=f"Unknown operation: {operation}",
                break_loop=False
            )
        
        return Response(
            message=f"Result: {result}",
            break_loop=False
        )
```

## Best Practices

1. **Service Lifecycle**: Always implement proper initialization and shutdown
2. **Error Handling**: Use appropriate exception types for different error scenarios
3. **Type Hints**: Use type hints for all public APIs
4. **Documentation**: Document all public methods and classes
5. **Testing**: Write tests for all service implementations

## Version Information

This documentation covers the Gary-Zero framework API as of version 0.1.0.