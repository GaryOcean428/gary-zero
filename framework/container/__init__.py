"""Dependency injection container for the Gary-Zero framework.

This module provides a lightweight dependency injection container that manages
service instances, handles lifecycle, and enables testable, modular architecture.
"""

import inspect
import logging
from typing import Any, Callable, Optional, TypeVar

from framework.interfaces import DependencyError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Container:
    """Lightweight dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._types: dict[str, type] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        self._singletons[name] = instance
        self._types[name] = type(instance)
        logger.debug(f"Registered singleton: {name}")

    def register_factory(
        self, name: str, factory: Callable[[], Any], type_hint: Optional[type] = None
    ) -> None:
        """Register a factory function for creating instances."""
        self._factories[name] = factory
        if type_hint:
            self._types[name] = type_hint
        logger.debug(f"Registered factory: {name}")

    def register_service(self, name: str, service_class: type[T]) -> None:
        """Register a service class."""
        self._services[name] = service_class
        self._types[name] = service_class
        logger.debug(f"Registered service: {name}")

    def get(self, name: str) -> Any:
        """Get an instance by name."""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]

        # Check factories
        if name in self._factories:
            instance = self._factories[name]()
            return instance

        # Check services (create new instance)
        if name in self._services:
            service_class = self._services[name]
            try:
                # Try to create with dependency injection
                instance = self._create_with_dependencies(service_class)
                return instance
            except Exception as e:
                logger.error(f"Failed to create service {name}: {e}")
                raise DependencyError(f"Failed to create service {name}: {e}") from e

        raise DependencyError(f"Service '{name}' not found in container")

    def get_by_type(self, service_type: type[T]) -> T:
        """Get an instance by type."""
        for name, registered_type in self._types.items():
            if registered_type == service_type or issubclass(registered_type, service_type):
                return self.get(name)

        raise DependencyError(f"No service registered for type {service_type}")

    def _create_with_dependencies(self, service_class: type) -> Any:
        """Create an instance with automatic dependency injection."""
        # Get constructor signature
        sig = inspect.signature(service_class.__init__)
        params = sig.parameters

        # Skip 'self' parameter
        args = {}
        for param_name, param in params.items():
            if param_name == 'self':
                continue

            # Try to resolve dependency
            if param.annotation != inspect.Parameter.empty:
                try:
                    # Try to get by type first
                    dependency = self.get_by_type(param.annotation)
                    args[param_name] = dependency
                except DependencyError:
                    # Try to get by name
                    try:
                        dependency = self.get(param_name)
                        args[param_name] = dependency
                    except DependencyError:
                        if param.default == inspect.Parameter.empty:
                            raise DependencyError(
                                f"Cannot resolve dependency {param_name} for {service_class}"
                            ) from None

        return service_class(**args)

    async def initialize_services(self) -> None:
        """Initialize all registered services that implement the Service protocol."""
        for name in list(self._singletons.keys()) + list(self._services.keys()):
            try:
                instance = self.get(name)
                if (hasattr(instance, 'initialize') and hasattr(instance, 'is_initialized')
                    and not instance.is_initialized):
                    await instance.initialize()
                    logger.info(f"Initialized service: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {e}")
                raise

    async def shutdown_services(self) -> None:
        """Shutdown all services in reverse order."""
        all_services = list(self._singletons.keys()) + list(self._services.keys())
        for name in reversed(all_services):
            try:
                instance = self.get(name)
                if (hasattr(instance, 'shutdown') and hasattr(instance, 'is_initialized')
                    and instance.is_initialized):
                    await instance.shutdown()
                    logger.info(f"Shutdown service: {name}")
            except Exception as e:
                logger.error(f"Failed to shutdown service {name}: {e}")

    def list_registered(self) -> dict[str, str]:
        """List all registered services and their types."""
        result = {}
        for name, type_class in self._types.items():
            result[name] = f"{type_class.__module__}.{type_class.__name__}"
        return result

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._types.clear()


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None
