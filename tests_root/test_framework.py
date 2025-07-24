#!/usr/bin/env python3
"""
Test script for unified logging, monitoring & benchmarking framework.

This script validates that all components work together properly.
"""

import asyncio
import time

from framework.benchmarking.harness import (
    BenchmarkHarness,
    BenchmarkResult,
    TaskStatus,
    TestExecutor,
)
from framework.benchmarking.tasks import StandardTasks
from framework.logging.hooks import log_tool_execution
from framework.logging.storage import SqliteStorage

# Import our new components
from framework.logging.unified_logger import (
    EventType,
    LogEvent,
    LogLevel,
    get_unified_logger,
)


class DummyTestExecutor(TestExecutor):
    """Simple test executor for testing the framework."""

    async def execute(self, test_case, config):
        """Execute a test case with dummy logic."""
        start_time = time.time()

        # Simulate some processing time
        await asyncio.sleep(0.1)

        # For testing, just return a successful result
        result = BenchmarkResult(
            task_id=test_case.task_id,
            run_id=f"test_{int(start_time)}",
            timestamp=start_time,
            status=TaskStatus.COMPLETED,
            duration_seconds=time.time() - start_time,
            score=0.85,  # Dummy score
            scores={"accuracy": 0.9, "completeness": 0.8},
            output_data={"generated": "dummy output"},
            configuration=config,
        )

        return result


async def test_unified_logger():
    """Test the unified logger functionality."""
    print("🧪 Testing Unified Logger...")

    logger = get_unified_logger()

    # Test basic event logging
    event_id = await logger.log_tool_execution(
        tool_name="test_tool",
        parameters={"param1": "value1", "param2": 42},
        success=True,
        duration_ms=150.5,
        user_id="test_user",
        agent_id="test_agent",
    )

    print(f"✅ Logged tool execution event: {event_id}")

    # Test event retrieval
    events = await logger.get_events(limit=5)
    print(f"✅ Retrieved {len(events)} events")

    # Test statistics
    stats = logger.get_statistics()
    print(f"✅ Logger statistics: {stats['total_events']} total events")

    return True


async def test_logging_hooks():
    """Test logging hooks and decorators."""
    print("🧪 Testing Logging Hooks...")

    @log_tool_execution(tool_name="hooked_function", user_id="test_user")
    def test_function(x, y):
        """A function to test hook decoration."""
        return x + y

    # Call the decorated function
    result = test_function(5, 3)
    print(f"✅ Hooked function result: {result}")

    # Give async logging time to complete
    await asyncio.sleep(0.1)

    return True


async def test_storage():
    """Test the SQLite storage backend."""
    print("🧪 Testing SQLite Storage...")

    # Create temporary storage
    storage = SqliteStorage("./test_logs.db")

    # Create and store a test event

    event = LogEvent(
        event_type=EventType.SYSTEM_EVENT,
        level=LogLevel.INFO,
        message="Test storage event",
        agent_id="test_agent",
        metadata={"test": True},
    )

    await storage.store_event(event)
    print("✅ Stored event to SQLite")

    # Retrieve events
    stored_events = await storage.get_events(limit=5)
    print(f"✅ Retrieved {len(stored_events)} events from storage")

    # Get statistics
    stats = await storage.get_statistics()
    print(f"✅ Storage statistics: {stats['total_events']} total events")

    return True


async def test_benchmarking():
    """Test the benchmarking framework."""
    print("🧪 Testing Benchmarking Framework...")

    # Create benchmark harness
    harness = BenchmarkHarness(results_dir="./test_benchmark_results")

    # Get standard tasks
    task_registry = StandardTasks.get_all_standard_tasks()

    # Register some tasks
    summarization_tasks = task_registry.get_tasks_by_group("summarization")
    if summarization_tasks:
        harness.register_test_case(summarization_tasks[0])
        print(f"✅ Registered task: {summarization_tasks[0].name}")

    # Register dummy executor
    harness.register_executor("dummy", DummyTestExecutor())
    print("✅ Registered dummy executor")

    # Register configuration
    harness.register_configuration(
        "test_config", {"model": "test-model", "temperature": 0.7, "max_tokens": 1000}
    )
    print("✅ Registered test configuration")

    # Run a single test
    if summarization_tasks:
        result = await harness.run_single_test(
            task_id=summarization_tasks[0].task_id,
            executor_name="dummy",
            config_name="test_config",
        )
        print(
            f"✅ Test completed with status: {result.status.value}, score: {result.score}"
        )

    # Get statistics
    stats = harness.get_statistics()
    print(f"✅ Harness statistics: {stats}")

    return True


async def test_api_integration():
    """Test API endpoints (without starting server)."""
    print("🧪 Testing API Integration...")

    # Test that we can import the API module
    try:
        from framework.api.monitoring import router

        print("✅ API module imported successfully")

        # Check that routes are defined
        routes = [route.path for route in router.routes]
        print(f"✅ Found {len(routes)} API routes")

        return True
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Unified Logging, Monitoring & Benchmarking Framework Tests\n")

    tests = [
        ("Unified Logger", test_unified_logger),
        ("Logging Hooks", test_logging_hooks),
        ("SQLite Storage", test_storage),
        ("Benchmarking Framework", test_benchmarking),
        ("API Integration", test_api_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}\n")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: FAILED - {e}\n")

    # Print summary
    print("📊 Test Summary:")
    print("=" * 50)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")

    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Framework is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
