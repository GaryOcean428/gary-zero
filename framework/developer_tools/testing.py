"""
Testing Utilities Module

Provides comprehensive testing utilities, mock generation, and test data factories
for enhanced development and testing workflows.
"""

import asyncio
import inspect
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, Union
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import logging

logger = logging.getLogger(__name__)

try:
    import faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class MockGenerator:
    """Generates mocks and test doubles"""
    
    def __init__(self):
        self._mock_cache: Dict[str, Mock] = {}
        self._specifications: Dict[Type, Dict[str, Any]] = {}
    
    def create_mock(
        self, 
        spec: Optional[Type] = None, 
        name: Optional[str] = None,
        **kwargs
    ) -> Mock:
        """Create a mock object with optional specification"""
        if spec and spec in self._specifications:
            # Use predefined specification
            spec_config = self._specifications[spec]
            kwargs.update(spec_config)
        
        mock = Mock(spec=spec, name=name, **kwargs)
        
        if name:
            self._mock_cache[name] = mock
        
        return mock
    
    def create_async_mock(
        self, 
        spec: Optional[Type] = None, 
        name: Optional[str] = None,
        **kwargs
    ) -> AsyncMock:
        """Create an async mock object"""
        if spec and spec in self._specifications:
            spec_config = self._specifications[spec]
            kwargs.update(spec_config)
        
        mock = AsyncMock(spec=spec, name=name, **kwargs)
        
        if name:
            self._mock_cache[name] = mock
        
        return mock
    
    def create_class_mock(self, cls: Type, **overrides) -> Mock:
        """Create a mock for a class with all methods mocked"""
        # Get all methods and properties
        methods = {}
        
        for name, method in inspect.getmembers(cls, inspect.ismethod):
            if not name.startswith('_'):
                if asyncio.iscoroutinefunction(method):
                    methods[name] = AsyncMock()
                else:
                    methods[name] = Mock()
        
        for name, func in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith('_'):
                if asyncio.iscoroutinefunction(func):
                    methods[name] = AsyncMock()
                else:
                    methods[name] = Mock()
        
        # Apply overrides
        methods.update(overrides)
        
        # Create class mock
        class_mock = Mock(spec=cls)
        for name, mock_method in methods.items():
            setattr(class_mock, name, mock_method)
        
        return class_mock
    
    def create_api_response_mock(
        self, 
        status_code: int = 200, 
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Mock:
        """Create a mock API response"""
        response_mock = Mock()
        response_mock.status_code = status_code
        response_mock.json.return_value = data or {}
        response_mock.headers = headers or {}
        response_mock.text = str(data) if data else ""
        response_mock.ok = 200 <= status_code < 300
        
        return response_mock
    
    def register_specification(self, cls: Type, **attributes):
        """Register a specification for a class"""
        self._specifications[cls] = attributes
    
    def get_mock(self, name: str) -> Optional[Mock]:
        """Get cached mock by name"""
        return self._mock_cache.get(name)


class TestDataFactory:
    """Generates test data using various strategies"""
    
    def __init__(self):
        self._fake = None
        if HAS_FAKER:
            self._fake = faker.Faker()
        
        self._sequences: Dict[str, int] = {}
        self._custom_generators: Dict[str, Callable] = {}
    
    def register_generator(self, data_type: str, generator: Callable):
        """Register a custom data generator"""
        self._custom_generators[data_type] = generator
    
    def generate_string(
        self, 
        length: int = 10, 
        charset: str = string.ascii_letters + string.digits
    ) -> str:
        """Generate random string"""
        return ''.join(random.choice(charset) for _ in range(length))
    
    def generate_email(self) -> str:
        """Generate random email"""
        if self._fake:
            return self._fake.email()
        
        username = self.generate_string(8)
        domain = self.generate_string(6)
        return f"{username}@{domain}.com"
    
    def generate_phone(self) -> str:
        """Generate random phone number"""
        if self._fake:
            return self._fake.phone_number()
        
        return f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    def generate_name(self) -> str:
        """Generate random name"""
        if self._fake:
            return self._fake.name()
        
        first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def generate_address(self) -> Dict[str, str]:
        """Generate random address"""
        if self._fake:
            return {
                'street': self._fake.street_address(),
                'city': self._fake.city(),
                'state': self._fake.state(),
                'zip_code': self._fake.zipcode(),
                'country': self._fake.country()
            }
        
        return {
            'street': f"{random.randint(1, 9999)} {self.generate_string(8)} St",
            'city': self.generate_string(8),
            'state': self.generate_string(2, string.ascii_uppercase),
            'zip_code': f"{random.randint(10000, 99999)}",
            'country': "United States"
        }
    
    def generate_uuid(self) -> str:
        """Generate random UUID"""
        return str(uuid.uuid4())
    
    def generate_id(self, prefix: str = "id") -> str:
        """Generate sequential ID"""
        if prefix not in self._sequences:
            self._sequences[prefix] = 0
        
        self._sequences[prefix] += 1
        return f"{prefix}_{self._sequences[prefix]:06d}"
    
    def generate_datetime(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> datetime:
        """Generate random datetime"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        
        if end_date is None:
            end_date = datetime.now()
        
        time_between = end_date - start_date
        random_time = start_date + timedelta(seconds=random.randint(0, int(time_between.total_seconds())))
        
        return random_time
    
    def generate_number(
        self, 
        min_value: Union[int, float] = 0, 
        max_value: Union[int, float] = 100,
        is_float: bool = False
    ) -> Union[int, float]:
        """Generate random number"""
        if is_float:
            return random.uniform(min_value, max_value)
        else:
            return random.randint(int(min_value), int(max_value))
    
    def generate_boolean(self, true_probability: float = 0.5) -> bool:
        """Generate random boolean"""
        return random.random() < true_probability
    
    def generate_list(
        self, 
        generator: Callable, 
        length: Optional[int] = None,
        min_length: int = 1,
        max_length: int = 10
    ) -> List[Any]:
        """Generate list of items using generator"""
        if length is None:
            length = random.randint(min_length, max_length)
        
        return [generator() for _ in range(length)]
    
    def generate_dict(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dictionary based on schema"""
        result = {}
        
        for key, value_spec in schema.items():
            if callable(value_spec):
                result[key] = value_spec()
            elif isinstance(value_spec, dict):
                result[key] = self.generate_dict(value_spec)
            elif value_spec in self._custom_generators:
                result[key] = self._custom_generators[value_spec]()
            elif value_spec == 'string':
                result[key] = self.generate_string()
            elif value_spec == 'email':
                result[key] = self.generate_email()
            elif value_spec == 'number':
                result[key] = self.generate_number()
            elif value_spec == 'boolean':
                result[key] = self.generate_boolean()
            elif value_spec == 'uuid':
                result[key] = self.generate_uuid()
            elif value_spec == 'datetime':
                result[key] = self.generate_datetime()
            else:
                result[key] = value_spec  # Use as literal value
        
        return result
    
    def generate_model_instance(self, model_class: Type, **overrides) -> Any:
        """Generate instance of a model class"""
        # Get class signature
        signature = inspect.signature(model_class.__init__)
        kwargs = {}
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            if param_name in overrides:
                kwargs[param_name] = overrides[param_name]
            else:
                # Try to infer type from annotation
                param_type = param.annotation
                
                if param_type == str:
                    kwargs[param_name] = self.generate_string()
                elif param_type == int:
                    kwargs[param_name] = self.generate_number(is_float=False)
                elif param_type == float:
                    kwargs[param_name] = self.generate_number(is_float=True)
                elif param_type == bool:
                    kwargs[param_name] = self.generate_boolean()
                elif param_type == datetime:
                    kwargs[param_name] = self.generate_datetime()
                else:
                    # Use default if available
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        kwargs[param_name] = None
        
        return model_class(**kwargs)


class TestingUtilities:
    """Main testing utilities class"""
    
    def __init__(self):
        self.mock_generator = MockGenerator()
        self.data_factory = TestDataFactory()
        self._test_contexts: List[Any] = []
        self._cleanup_functions: List[Callable] = []
    
    def setup_test_environment(self, test_name: str):
        """Setup test environment"""
        logger.info(f"Setting up test environment for: {test_name}")
        
        # Clear any previous state
        self.cleanup_test_environment()
        
        # Initialize test context
        test_context = {
            'name': test_name,
            'start_time': datetime.now(),
            'mocks': {},
            'patches': []
        }
        
        self._test_contexts.append(test_context)
        
        return test_context
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        # Stop all patches
        for context in self._test_contexts:
            for patch_obj in context.get('patches', []):
                try:
                    patch_obj.stop()
                except Exception as e:
                    logger.warning(f"Error stopping patch: {e}")
        
        # Run cleanup functions
        for cleanup_func in self._cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                logger.warning(f"Error in cleanup function: {e}")
        
        # Clear state
        self._test_contexts.clear()
        self._cleanup_functions.clear()
    
    def create_test_database(self, db_url: str = "sqlite:///:memory:") -> Any:
        """Create test database"""
        # This would integrate with SQLAlchemy or other ORMs
        # For now, return a mock database
        return self.mock_generator.create_mock(name="test_database")
    
    def create_test_api_client(self, app: Any) -> Any:
        """Create test API client"""
        try:
            from fastapi.testclient import TestClient
            return TestClient(app)
        except ImportError:
            # Return mock client
            return self.mock_generator.create_mock(name="test_client")
    
    def assert_called_with_timeout(
        self, 
        mock_obj: Mock, 
        timeout: float = 1.0,
        expected_calls: int = 1
    ) -> bool:
        """Assert mock was called within timeout"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if mock_obj.call_count >= expected_calls:
                return True
            time.sleep(0.01)
        
        return False
    
    def patch_module(self, module_path: str, **patches) -> Dict[str, Any]:
        """Patch multiple attributes in a module"""
        patch_objects = {}
        
        for attr_name, patch_value in patches.items():
            full_path = f"{module_path}.{attr_name}"
            patch_obj = patch(full_path, patch_value)
            patch_objects[attr_name] = patch_obj.start()
            
            # Add to current test context
            if self._test_contexts:
                self._test_contexts[-1]['patches'].append(patch_obj)
        
        return patch_objects
    
    def create_performance_test(
        self, 
        func: Callable, 
        max_execution_time: float = 1.0,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """Create performance test for a function"""
        import time
        
        execution_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            func()
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        performance_result = {
            'average_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'iterations': iterations,
            'passed': max_time <= max_execution_time,
            'execution_times': execution_times
        }
        
        return performance_result
    
    def create_load_test(
        self, 
        func: Callable, 
        concurrent_users: int = 10,
        duration: float = 10.0
    ) -> Dict[str, Any]:
        """Create load test for a function"""
        import threading
        import time
        
        results = []
        start_time = time.time()
        
        def worker():
            while time.time() - start_time < duration:
                try:
                    exec_start = time.time()
                    func()
                    exec_end = time.time()
                    results.append({
                        'success': True,
                        'execution_time': exec_end - exec_start,
                        'timestamp': exec_end
                    })
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    })
        
        # Start worker threads
        threads = []
        for _ in range(concurrent_users):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            avg_response_time = sum(r['execution_time'] for r in successful_requests) / len(successful_requests)
        else:
            avg_response_time = 0
        
        return {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(results) * 100 if results else 0,
            'average_response_time': avg_response_time,
            'requests_per_second': len(results) / duration,
            'concurrent_users': concurrent_users,
            'duration': duration
        }
    
    def add_cleanup_function(self, func: Callable):
        """Add function to be called during cleanup"""
        self._cleanup_functions.append(func)


# Context managers for testing
class test_environment:
    """Context manager for test environment setup/cleanup"""
    
    def __init__(self, test_name: str, utilities: Optional[TestingUtilities] = None):
        self.test_name = test_name
        self.utilities = utilities or _global_utilities
        self.context = None
    
    def __enter__(self):
        self.context = self.utilities.setup_test_environment(self.test_name)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.utilities.cleanup_test_environment()


class mock_context:
    """Context manager for mock objects"""
    
    def __init__(self, patches: Dict[str, Any]):
        self.patches = patches
        self.patch_objects = []
    
    def __enter__(self):
        for target, mock_value in self.patches.items():
            patch_obj = patch(target, mock_value)
            self.patch_objects.append(patch_obj)
            patch_obj.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in self.patch_objects:
            patch_obj.stop()


# Pytest fixtures (if pytest is available)
if HAS_PYTEST:
    @pytest.fixture
    def mock_generator():
        """Pytest fixture for mock generator"""
        return MockGenerator()
    
    @pytest.fixture
    def test_data_factory():
        """Pytest fixture for test data factory"""
        return TestDataFactory()
    
    @pytest.fixture
    def testing_utilities():
        """Pytest fixture for testing utilities"""
        utilities = TestingUtilities()
        yield utilities
        utilities.cleanup_test_environment()


# Global instances
_global_utilities = TestingUtilities()

# Convenience functions
def create_mock(spec: Optional[Type] = None, name: Optional[str] = None, **kwargs) -> Mock:
    """Create a mock object"""
    return _global_utilities.mock_generator.create_mock(spec, name, **kwargs)

def create_async_mock(spec: Optional[Type] = None, name: Optional[str] = None, **kwargs) -> AsyncMock:
    """Create an async mock object"""
    return _global_utilities.mock_generator.create_async_mock(spec, name, **kwargs)

def generate_test_data(data_type: str, **kwargs) -> Any:
    """Generate test data"""
    factory = _global_utilities.data_factory
    
    if data_type == 'string':
        return factory.generate_string(**kwargs)
    elif data_type == 'email':
        return factory.generate_email()
    elif data_type == 'number':
        return factory.generate_number(**kwargs)
    elif data_type == 'boolean':
        return factory.generate_boolean(**kwargs)
    elif data_type == 'uuid':
        return factory.generate_uuid()
    elif data_type == 'datetime':
        return factory.generate_datetime(**kwargs)
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def setup_test_environment(test_name: str):
    """Setup test environment"""
    return _global_utilities.setup_test_environment(test_name)

def cleanup_test_environment():
    """Cleanup test environment"""
    _global_utilities.cleanup_test_environment()