"""Enhanced dependency injection container with lifecycle management.

Provides advanced dependency injection features including:
- Lifecycle management (singleton, transient, scoped)
- Async service initialization and shutdown
- Service health monitoring
- Automatic dependency resolution
- Service composition patterns
"""

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any, Dict, List, Optional, TypeVar, Union, get_type_hints
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field

from framework.interfaces import BaseService, DependencyError, ServiceError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient" 
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Descriptor for service registration."""
    name: str
    service_type: type
    implementation: Optional[type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[str] = field(default_factory=list)
    initialization_order: int = 0


@dataclass
class ServiceStatus:
    """Service status information."""
    name: str
    is_initialized: bool
    is_healthy: bool
    created_at: datetime
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


class EnhancedContainer:
    """Enhanced dependency injection container with lifecycle management."""
    
    def __init__(self):
        self._descriptors: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._service_status: Dict[str, ServiceStatus] = {}
        self._initialization_order: List[str] = []
        self._current_scope: Optional[str] = None
        self._lock = asyncio.Lock()
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        descriptor = ServiceDescriptor(
            name=name,
            service_type=type(instance),
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self._descriptors[name] = descriptor
        self._instances[name] = instance
        self._service_status[name] = ServiceStatus(
            name=name,
            is_initialized=False,
            is_healthy=True,
            created_at=datetime.utcnow()
        )
        
        logger.debug(f"Registered singleton: {name}")
    
    def register_transient(
        self, 
        name: str, 
        service_type: type, 
        implementation: Optional[type] = None
    ) -> None:
        """Register a transient service."""
        impl = implementation or service_type
        dependencies = self._extract_dependencies(impl)
        
        descriptor = ServiceDescriptor(
            name=name,
            service_type=service_type,
            implementation=impl,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=dependencies
        )
        
        self._descriptors[name] = descriptor
        logger.debug(f"Registered transient service: {name}")
    
    def register_scoped(
        self, 
        name: str, 
        service_type: type, 
        implementation: Optional[type] = None
    ) -> None:
        """Register a scoped service."""
        impl = implementation or service_type
        dependencies = self._extract_dependencies(impl)
        
        descriptor = ServiceDescriptor(
            name=name,
            service_type=service_type,
            implementation=impl,
            lifetime=ServiceLifetime.SCOPED,
            dependencies=dependencies
        )
        
        self._descriptors[name] = descriptor
        logger.debug(f"Registered scoped service: {name}")
    
    def register_factory(
        self, 
        name: str, 
        factory: Callable, 
        service_type: Optional[type] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> None:
        """Register a factory function."""
        descriptor = ServiceDescriptor(
            name=name,
            service_type=service_type or type(None),
            factory=factory,
            lifetime=lifetime
        )
        
        self._descriptors[name] = descriptor
        logger.debug(f"Registered factory: {name}")
    
    async def get(self, name: str) -> Any:
        """Get service instance by name."""
        if name not in self._descriptors:
            raise DependencyError(f"Service '{name}' not registered")
        
        descriptor = self._descriptors[name]
        
        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return await self._get_singleton(descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return await self._get_scoped(descriptor)
        else:  # TRANSIENT
            return await self._create_instance(descriptor)
    
    async def get_by_type(self, service_type: type[T]) -> T:
        """Get service instance by type."""
        for name, descriptor in self._descriptors.items():
            if (descriptor.service_type == service_type or 
                (descriptor.implementation and 
                 issubclass(descriptor.implementation, service_type))):
                return await self.get(name)
        
        raise DependencyError(f"No service registered for type {service_type}")
    
    async def _get_singleton(self, descriptor: ServiceDescriptor) -> Any:
        """Get or create singleton instance."""
        if descriptor.name in self._instances:
            return self._instances[descriptor.name]
        
        async with self._lock:
            # Double-check pattern
            if descriptor.name in self._instances:
                return self._instances[descriptor.name]
            
            instance = await self._create_instance(descriptor)
            self._instances[descriptor.name] = instance
            return instance
    
    async def _get_scoped(self, descriptor: ServiceDescriptor) -> Any:
        """Get or create scoped instance."""
        if not self._current_scope:
            raise ServiceError("No active scope for scoped service")
        
        scope_instances = self._scoped_instances.get(self._current_scope, {})
        
        if descriptor.name in scope_instances:
            return scope_instances[descriptor.name]
        
        instance = await self._create_instance(descriptor)
        
        if self._current_scope not in self._scoped_instances:
            self._scoped_instances[self._current_scope] = {}
        
        self._scoped_instances[self._current_scope][descriptor.name] = instance
        return instance
    
    async def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create new service instance."""
        try:
            if descriptor.instance:
                return descriptor.instance
            
            if descriptor.factory:
                if asyncio.iscoroutinefunction(descriptor.factory):
                    return await descriptor.factory()
                else:
                    return descriptor.factory()
            
            if descriptor.implementation:
                return await self._create_with_dependencies(descriptor.implementation)
            
            raise ServiceError(f"No implementation or factory for service {descriptor.name}")
            
        except Exception as e:
            await self._update_service_status(descriptor.name, error=str(e))
            raise DependencyError(f"Failed to create service {descriptor.name}: {e}") from e
    
    async def _create_with_dependencies(self, service_class: type) -> Any:
        """Create instance with automatic dependency injection."""
        sig = inspect.signature(service_class.__init__)
        type_hints = get_type_hints(service_class.__init__)
        
        args = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            # Try to resolve by type annotation
            if param_name in type_hints:
                param_type = type_hints[param_name]
                try:
                    dependency = await self.get_by_type(param_type)
                    args[param_name] = dependency
                    continue
                except DependencyError:
                    pass
            
            # Try to resolve by parameter name
            try:
                dependency = await self.get(param_name)
                args[param_name] = dependency
            except DependencyError:
                if param.default == inspect.Parameter.empty:
                    raise DependencyError(
                        f"Cannot resolve dependency {param_name} for {service_class}"
                    )
        
        return service_class(**args)
    
    def _extract_dependencies(self, service_class: type) -> List[str]:
        """Extract dependency names from constructor."""
        sig = inspect.signature(service_class.__init__)
        dependencies = []
        
        for param_name, param in sig.parameters.items():
            if param_name != "self" and param.default == inspect.Parameter.empty:
                dependencies.append(param_name)
        
        return dependencies
    
    async def initialize_services(self) -> None:
        """Initialize all registered services."""
        # Sort services by dependencies and initialization order
        sorted_services = self._topological_sort()
        
        for service_name in sorted_services:
            try:
                instance = await self.get(service_name)
                
                if hasattr(instance, "initialize") and isinstance(instance, BaseService):
                    if not instance.is_initialized:
                        await instance.initialize()
                        await self._update_service_status(service_name, initialized=True)
                        logger.info(f"Initialized service: {service_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize service {service_name}: {e}")
                await self._update_service_status(service_name, error=str(e))
                raise
    
    async def shutdown_services(self) -> None:
        """Shutdown all services in reverse order."""
        for service_name in reversed(self._initialization_order):
            try:
                if service_name in self._instances:
                    instance = self._instances[service_name]
                    
                    if hasattr(instance, "shutdown") and isinstance(instance, BaseService):
                        if instance.is_initialized:
                            await instance.shutdown()
                            logger.info(f"Shutdown service: {service_name}")
                
            except Exception as e:
                logger.error(f"Failed to shutdown service {service_name}: {e}")
    
    async def health_check_services(self) -> Dict[str, ServiceStatus]:
        """Perform health checks on all services."""
        results = {}
        
        for service_name in self._service_status.keys():
            try:
                if service_name in self._instances:
                    instance = self._instances[service_name]
                    is_healthy = True
                    
                    # Check if service has health check method
                    if hasattr(instance, "health_check"):
                        is_healthy = await instance.health_check()
                    elif isinstance(instance, BaseService):
                        is_healthy = instance.is_initialized
                    
                    await self._update_service_status(
                        service_name, 
                        healthy=is_healthy,
                        health_checked=True
                    )
                
                results[service_name] = self._service_status[service_name]
                
            except Exception as e:
                logger.error(f"Health check failed for service {service_name}: {e}")
                await self._update_service_status(service_name, error=str(e), healthy=False)
                results[service_name] = self._service_status[service_name]
        
        return results
    
    def create_scope(self, scope_id: str) -> "ServiceScope":
        """Create a new service scope."""
        return ServiceScope(self, scope_id)
    
    def _topological_sort(self) -> List[str]:
        """Sort services by dependencies using topological sort."""
        # Simple implementation - could be enhanced
        visited = set()
        result = []
        
        def visit(service_name: str):
            if service_name in visited:
                return
            
            visited.add(service_name)
            
            if service_name in self._descriptors:
                descriptor = self._descriptors[service_name]
                for dep in descriptor.dependencies:
                    if dep in self._descriptors:
                        visit(dep)
            
            result.append(service_name)
        
        # Sort by initialization order first
        sorted_services = sorted(
            self._descriptors.keys(),
            key=lambda x: self._descriptors[x].initialization_order
        )
        
        for service_name in sorted_services:
            visit(service_name)
        
        self._initialization_order = result
        return result
    
    async def _update_service_status(
        self, 
        service_name: str, 
        initialized: Optional[bool] = None,
        healthy: Optional[bool] = None,
        health_checked: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Update service status."""
        if service_name not in self._service_status:
            self._service_status[service_name] = ServiceStatus(
                name=service_name,
                is_initialized=False,
                is_healthy=True,
                created_at=datetime.utcnow()
            )
        
        status = self._service_status[service_name]
        
        if initialized is not None:
            status.is_initialized = initialized
        
        if healthy is not None:
            status.is_healthy = healthy
        
        if health_checked:
            status.last_health_check = datetime.utcnow()
        
        if error:
            status.error_count += 1
            status.last_error = error
            status.is_healthy = False
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get status for a specific service."""
        return self._service_status.get(service_name)
    
    def list_services(self) -> Dict[str, ServiceDescriptor]:
        """List all registered services."""
        return self._descriptors.copy()


class ServiceScope:
    """Service scope for managing scoped service lifetimes."""
    
    def __init__(self, container: EnhancedContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id
        self._entered = False
    
    async def __aenter__(self):
        if self.container._current_scope:
            raise ServiceError("Nested scopes not supported")
        
        self.container._current_scope = self.scope_id
        self._entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._entered:
            # Cleanup scoped instances
            if self.scope_id in self.container._scoped_instances:
                scoped_instances = self.container._scoped_instances[self.scope_id]
                
                # Shutdown scoped services
                for instance in scoped_instances.values():
                    if hasattr(instance, "shutdown") and isinstance(instance, BaseService):
                        try:
                            await instance.shutdown()
                        except Exception as e:
                            logger.error(f"Error shutting down scoped service: {e}")
                
                del self.container._scoped_instances[self.scope_id]
            
            self.container._current_scope = None
            self._entered = False


# Global enhanced container instance
_enhanced_container: Optional[EnhancedContainer] = None


def get_enhanced_container() -> EnhancedContainer:
    """Get the global enhanced container instance."""
    global _enhanced_container
    if _enhanced_container is None:
        _enhanced_container = EnhancedContainer()
    return _enhanced_container


def reset_enhanced_container() -> None:
    """Reset the global enhanced container (useful for testing)."""
    global _enhanced_container
    _enhanced_container = None