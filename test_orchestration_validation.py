"""
Simple validation test for async orchestration system.
"""

import asyncio
import sys
import time
import uuid

sys.path.append('/home/runner/work/gary-zero/gary-zero')

from framework.helpers.async_orchestrator import AsyncTaskOrchestrator
from framework.helpers.enhanced_scheduler import EnhancedTaskScheduler
from framework.helpers.orchestration_config import OrchestrationConfig, get_config_manager
from framework.helpers.task_manager import Task as ManagedTask
from framework.helpers.task_manager import TaskCategory, TaskStatus


async def test_basic_orchestration():
    """Test basic orchestration functionality."""
    print("Testing basic async orchestration...")

    # Create orchestrator
    orchestrator = AsyncTaskOrchestrator(
        max_concurrent_tasks=5,
        enable_performance_monitoring=False  # Disable for testing
    )

    await orchestrator.start()

    try:
        # Create test task
        task = ManagedTask(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Testing basic orchestration",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        # Mock the execution method to avoid dependencies
        async def mock_execute(managed_task):
            await asyncio.sleep(0.1)  # Simulate work
            return f"Completed: {managed_task.title}"

        # Replace the execution method
        orchestrator._execute_managed_task = mock_execute

        # Submit task
        task_id = await orchestrator.submit_task(task)
        print(f"✓ Task submitted with ID: {task_id}")

        # Wait for completion
        result = await orchestrator.wait_for_task(task_id, timeout=5.0)
        print(f"✓ Task completed with result: {result}")

        # Check metrics
        metrics = await orchestrator.get_orchestration_metrics()
        print(f"✓ Metrics: {metrics['total_tasks']} total, {metrics['completed_tasks']} completed")

        assert metrics['total_tasks'] >= 1
        assert metrics['completed_tasks'] >= 1

    finally:
        await orchestrator.stop()

    print("✓ Basic orchestration test passed")


async def test_concurrent_execution():
    """Test concurrent task execution."""
    print("Testing concurrent task execution...")

    orchestrator = AsyncTaskOrchestrator(
        max_concurrent_tasks=5,
        enable_performance_monitoring=False
    )

    await orchestrator.start()

    try:
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = ManagedTask(
                id=f"concurrent_task_{i}",
                title=f"Concurrent Task {i}",
                description=f"Testing concurrent execution {i}",
                category=TaskCategory.OTHER,
                status=TaskStatus.PENDING
            )
            tasks.append(task)

        # Mock execution with delay
        async def mock_execute(managed_task):
            await asyncio.sleep(0.2)  # Simulate work
            return f"Result for {managed_task.id}"

        orchestrator._execute_managed_task = mock_execute

        # Submit all tasks and measure time
        start_time = time.time()

        task_ids = []
        for task in tasks:
            task_id = await orchestrator.submit_task(task)
            task_ids.append(task_id)

        # Wait for all tasks to complete
        results = await asyncio.gather(*[
            orchestrator.wait_for_task(task_id, timeout=5.0)
            for task_id in task_ids
        ])

        execution_time = time.time() - start_time

        print(f"✓ {len(results)} tasks completed in {execution_time:.2f} seconds")
        print(f"✓ Average time per task: {execution_time/len(results):.2f} seconds")

        # Concurrent execution should be faster than sequential (5 * 0.2 = 1.0s)
        assert execution_time < 0.5, f"Execution too slow: {execution_time:.2f}s"
        assert len(results) == 5

        # Check final metrics
        metrics = await orchestrator.get_orchestration_metrics()
        print(f"✓ Final metrics: {metrics['total_tasks']} total, {metrics['completed_tasks']} completed")

    finally:
        await orchestrator.stop()

    print("✓ Concurrent execution test passed")


async def test_dependency_management():
    """Test task dependency management."""
    print("Testing dependency management...")

    orchestrator = AsyncTaskOrchestrator(
        max_concurrent_tasks=5,
        enable_performance_monitoring=False
    )

    await orchestrator.start()

    try:
        # Create tasks with dependencies
        task_a = ManagedTask(
            id="dep_task_a",
            title="Task A",
            description="Independent task",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        task_b = ManagedTask(
            id="dep_task_b",
            title="Task B",
            description="Depends on Task A",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        execution_order = []

        async def mock_execute(managed_task):
            execution_order.append(managed_task.id)
            await asyncio.sleep(0.1)
            return f"Result for {managed_task.id}"

        orchestrator._execute_managed_task = mock_execute

        # Submit tasks in reverse order (B before A)
        await orchestrator.submit_task(task_b, dependencies=["dep_task_a"])
        await orchestrator.submit_task(task_a, dependencies=[])

        # Wait for both to complete
        await asyncio.gather(
            orchestrator.wait_for_task("dep_task_a", timeout=5.0),
            orchestrator.wait_for_task("dep_task_b", timeout=5.0)
        )

        print(f"✓ Execution order: {execution_order}")

        # Verify A ran before B despite submission order
        assert execution_order == ["dep_task_a", "dep_task_b"], f"Wrong order: {execution_order}"

    finally:
        await orchestrator.stop()

    print("✓ Dependency management test passed")


async def test_configuration():
    """Test configuration system."""
    print("Testing configuration system...")

    # Test config manager
    config_manager = get_config_manager()
    config = config_manager.get_config()

    assert isinstance(config, OrchestrationConfig)
    assert config.enabled is True

    # Test config updates
    original_max_tasks = config.max_concurrent_tasks
    config_manager.update_config(max_concurrent_tasks=15)
    assert config.max_concurrent_tasks == 15

    # Reset
    config_manager.update_config(max_concurrent_tasks=original_max_tasks)

    print("✓ Configuration test passed")


async def test_enhanced_scheduler():
    """Test enhanced scheduler integration."""
    print("Testing enhanced scheduler...")

    scheduler = EnhancedTaskScheduler()

    # Test initialization
    assert scheduler is not None
    assert scheduler._async_enabled is False

    # Test execution stats
    stats = scheduler.get_execution_stats()
    assert 'sync_executions' in stats
    assert 'async_executions' in stats

    print("✓ Enhanced scheduler test passed")


async def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("ASYNC ORCHESTRATION VALIDATION TESTS")
    print("=" * 60)

    try:
        await test_basic_orchestration()
        print()

        await test_concurrent_execution()
        print()

        await test_dependency_management()
        print()

        test_configuration()
        print()

        await test_enhanced_scheduler()
        print()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
