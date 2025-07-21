"""Tests for the dependency injection container and interfaces."""


import pytest

from framework.container import Container, get_container, reset_container
from framework.interfaces import BaseService, DependencyError


class MockService(BaseService):
    """Mock service implementation for testing."""

    def __init__(self):
        super().__init__()
        self.init_called = False
        self.shutdown_called = False

    async def initialize(self):
        self.init_called = True
        await self._set_initialized()

    async def shutdown(self):
        self.shutdown_called = True
        await self._set_shutdown()


class MockServiceWithDependency(BaseService):
    """Mock service with dependency injection for testing."""

    def __init__(self, dependency: MockService):
        super().__init__()
        self.dependency = dependency
        self.init_called = False

    async def initialize(self):
        self.init_called = True
        await self._set_initialized()

    async def shutdown(self):
        await self._set_shutdown()


class TestContainer:
    """Test cases for the dependency injection container."""

    def setup_method(self):
        """Reset container before each test."""
        reset_container()
        self.container = Container()

    def test_register_and_get_singleton(self):
        """Test singleton registration and retrieval."""
        service = MockService()
        self.container.register_singleton("test_service", service)

        retrieved = self.container.get("test_service")
        assert retrieved is service

        # Should return same instance
        retrieved2 = self.container.get("test_service")
        assert retrieved2 is service

    def test_register_and_get_factory(self):
        """Test factory registration and retrieval."""
        def create_service():
            return MockService()

        self.container.register_factory("test_service", create_service, MockService)

        service1 = self.container.get("test_service")
        service2 = self.container.get("test_service")

        assert isinstance(service1, MockService)
        assert isinstance(service2, MockService)
        # Factory should create new instances
        assert service1 is not service2

    def test_register_and_get_service(self):
        """Test service class registration and retrieval."""
        self.container.register_service("test_service", MockService)

        service = self.container.get("test_service")
        assert isinstance(service, MockService)

    def test_get_by_type(self):
        """Test getting service by type."""
        service = MockService()
        self.container.register_singleton("test_service", service)

        retrieved = self.container.get_by_type(MockService)
        assert retrieved is service

    def test_dependency_injection(self):
        """Test automatic dependency injection."""
        # Register dependency first
        dependency = MockService()
        self.container.register_singleton("dependency", dependency)

        # Register service that needs the dependency
        self.container.register_service("service_with_dep", MockServiceWithDependency)

        service = self.container.get("service_with_dep")
        assert isinstance(service, MockServiceWithDependency)
        assert service.dependency is dependency

    def test_missing_service_error(self):
        """Test error when requesting non-existent service."""
        with pytest.raises(DependencyError, match="Service 'nonexistent' not found"):
            self.container.get("nonexistent")

    def test_missing_dependency_error(self):
        """Test error when dependency cannot be resolved."""
        self.container.register_service("service_with_dep", MockServiceWithDependency)

        with pytest.raises(DependencyError, match="Cannot resolve dependency"):
            self.container.get("service_with_dep")

    @pytest.mark.asyncio
    async def test_initialize_services(self):
        """Test service initialization."""
        service = MockService()
        self.container.register_singleton("test_service", service)

        await self.container.initialize_services()

        assert service.init_called
        assert service.is_initialized

    @pytest.mark.asyncio
    async def test_shutdown_services(self):
        """Test service shutdown."""
        service = MockService()
        service._initialized = True  # Mark as initialized
        self.container.register_singleton("test_service", service)

        await self.container.shutdown_services()

        assert service.shutdown_called
        assert not service.is_initialized

    def test_list_registered(self):
        """Test listing registered services."""
        service = MockService()
        self.container.register_singleton("test_service", service)

        registered = self.container.list_registered()
        assert "test_service" in registered
        assert "MockService" in registered["test_service"]

    def test_global_container(self):
        """Test global container access."""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

        reset_container()
        container3 = get_container()
        assert container3 is not container1


class TestBaseService:
    """Test the BaseService base class."""

    def test_initial_state(self):
        """Test initial service state."""
        service = MockService()
        assert not service.is_initialized

    @pytest.mark.asyncio
    async def test_lifecycle(self):
        """Test service lifecycle."""
        service = MockService()

        # Initial state
        assert not service.is_initialized
        assert not service.init_called

        # After initialization
        await service.initialize()
        assert service.is_initialized
        assert service.init_called

        # After shutdown
        await service.shutdown()
        assert not service.is_initialized
        assert service.shutdown_called
