"""
Performance tests for concurrent agents and system resources.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import pytest


@pytest.mark.performance
class TestConcurrentPerformance:
    """Performance tests for concurrent operations."""

    def test_concurrent_health_checks(self):
        """Test performance of concurrent health check requests."""
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)

        def make_health_request():
            response = client.get("/health")
            return response.status_code == 200

        # Test with multiple concurrent requests
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_request) for _ in range(50)]
            results = [future.result() for future in futures]

        end_time = time.time()
        duration = end_time - start_time

        # All requests should succeed
        assert all(results)

        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 5.0, f"Health checks took too long: {duration}s"

        # Calculate requests per second
        rps = len(results) / duration
        print(f"Health check RPS: {rps:.2f}")

    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """Test performance with multiple WebSocket connections."""
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)

        async def websocket_interaction():
            try:
                with client.websocket_connect("/ws") as websocket:
                    # Send a message
                    websocket.send_json(
                        {"message": "Performance test message", "agent_id": "perf-test"}
                    )

                    # Receive response
                    response = websocket.receive_json()
                    return "status" in response
            except Exception:
                return False

        # Test multiple concurrent WebSocket connections
        start_time = time.time()

        tasks = [websocket_interaction() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Count successful connections
        successful = sum(1 for r in results if r is True)

        print(
            f"WebSocket connections: {successful}/{len(tasks)} successful in {duration:.2f}s"
        )

        # At least 80% should succeed
        assert successful >= len(tasks) * 0.8


@pytest.mark.performance
class TestMemoryUsage:
    """Performance tests for memory usage."""

    def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make many requests to stress test memory
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

            # Also test metrics endpoint
            metrics_response = client.get("/metrics")
            assert metrics_response.status_code == 200

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(
            f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (+{memory_increase:.2f}MB)"
        )

        # Memory increase should be reasonable (adjust threshold as needed)
        assert (
            memory_increase < 50
        ), f"Memory usage increased too much: {memory_increase}MB"

    def test_code_validation_performance(self):
        """Test performance of code validation."""
        from security.validator import SecurityLevel, validate_code

        test_code = '''
import math
import json
import datetime

def complex_calculation(n):
    """A complex calculation function."""
    result = 0
    for i in range(n):
        result += math.sqrt(i) * math.log(i + 1)
        data = {"iteration": i, "result": result}
        json_str = json.dumps(data)
    return result

# Calculate something
final_result = complex_calculation(1000)
print(f"Final result: {final_result}")
'''

        # Time multiple validations
        start_time = time.time()

        for _ in range(50):
            result = validate_code(test_code, SecurityLevel.STRICT)
            assert result.is_valid is True

        end_time = time.time()
        duration = end_time - start_time

        avg_time = duration / 50
        print(f"Average validation time: {avg_time * 1000:.2f}ms")

        # Should validate quickly (adjust threshold as needed)
        assert avg_time < 0.1, f"Code validation too slow: {avg_time:.3f}s"


@pytest.mark.performance
class TestModelRegistryPerformance:
    """Performance tests for model registry operations."""

    def test_model_lookup_performance(self):
        """Test performance of model lookups."""
        from models.registry import ModelCapability, ModelProvider, get_registry

        registry = get_registry()

        # Time multiple lookups
        start_time = time.time()

        for _ in range(1000):
            # Test various lookup operations
            model = registry.get_model("gpt-4o")
            assert model is not None

            openai_models = registry.list_models(ModelProvider.OPENAI)
            assert len(openai_models) > 0

            coding_models = registry.get_models_by_capability(
                ModelCapability.CODE_GENERATION
            )
            assert len(coding_models) > 0

        end_time = time.time()
        duration = end_time - start_time

        avg_time = duration / 1000
        print(f"Average lookup time: {avg_time * 1000:.2f}ms")

        # Lookups should be fast
        assert avg_time < 0.001, f"Model lookups too slow: {avg_time:.4f}s"
