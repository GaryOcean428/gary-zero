"""
Comprehensive test suite for async task orchestration system.

Tests include:
- Basic async task execution
- Dependency management and DAG resolution
- Concurrency controls and resource management
- Performance monitoring integration
- Error handling and failure scenarios
- Backward compatibility
"""

import asyncio

# Import the components we're testing
import sys
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append('/home/runner/work/gary-zero/gary-zero')

from framework.helpers.async_orchestrator import AsyncTaskOrchestrator, OrchestrationStatus
from framework.helpers.enhanced_scheduler import EnhancedTaskScheduler
from framework.helpers.orchestration_config import OrchestrationConfig, OrchestrationConfigManager
from framework.helpers.task_manager import Task as ManagedTask
from framework.helpers.task_manager import TaskCategory, TaskStatus


class TestAsyncOrchestrator:
    """Test suite for AsyncTaskOrchestrator."""

    @pytest.fixture
    async def orchestrator(self):
        """Create a test orchestrator."""
        orchestrator = AsyncTaskOrchestrator(
            max_concurrent_tasks=5,
            default_task_timeout=10.0,
            enable_performance_monitoring=False  # Disable for testing
        )
        await orchestrator.start()
        yield orchestrator
        await orchestrator.stop()

    @pytest.fixture
    def sample_task(self):
        """Create a sample managed task."""
        return ManagedTask(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="A test task for orchestration",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

    async def test_orchestrator_lifecycle(self):
        """Test orchestrator start/stop lifecycle."""
        orchestrator = AsyncTaskOrchestrator(enable_performance_monitoring=False)

        assert not orchestrator.is_running

        await orchestrator.start()
        assert orchestrator.is_running

        await orchestrator.stop()
        assert not orchestrator.is_running

    async def test_task_submission(self, orchestrator, sample_task):
        """Test basic task submission."""
        task_id = await orchestrator.submit_task(sample_task)

        assert task_id == sample_task.id
        assert task_id in orchestrator.tasks

        orchestration_task = orchestrator.tasks[task_id]
        assert orchestration_task.managed_task == sample_task
        assert orchestration_task.status in (OrchestrationStatus.PENDING, OrchestrationStatus.READY)

    async def test_task_execution(self, orchestrator, sample_task):
        """Test task execution with result."""
        # Mock the task execution
        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Task completed successfully"

            task_id = await orchestrator.submit_task(sample_task)
            result = await orchestrator.wait_for_task(task_id, timeout=5.0)

            assert result == "Task completed successfully"
            assert orchestrator.tasks[task_id].status == OrchestrationStatus.COMPLETED

    async def test_concurrent_task_execution(self, orchestrator):
        """Test concurrent execution of multiple tasks."""
        # Create multiple tasks
        tasks = [
            ManagedTask(
                id=str(uuid.uuid4()),
                title=f"Concurrent Task {i}",
                description=f"Concurrent test task {i}",
                category=TaskCategory.OTHER,
                status=TaskStatus.PENDING
            )
            for i in range(5)
        ]

        # Mock task execution with different delays
        async def mock_execute(task):
            await asyncio.sleep(0.1)  # Simulate work
            return f"Result for {task.id}"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute_method:
            mock_execute_method.side_effect = mock_execute

            start_time = time.time()

            # Submit all tasks
            task_ids = []
            for task in tasks:
                task_id = await orchestrator.submit_task(task)
                task_ids.append(task_id)

            # Wait for all tasks
            results = await asyncio.gather(*[
                orchestrator.wait_for_task(task_id, timeout=5.0)
                for task_id in task_ids
            ])

            execution_time = time.time() - start_time

            # Verify results
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result == f"Result for {task_ids[i]}"

            # Concurrent execution should be faster than sequential
            # (5 tasks * 0.1s = 0.5s sequential, but should be ~0.1s concurrent)
            assert execution_time < 0.3  # Allow some overhead

    async def test_dependency_management(self, orchestrator):
        """Test task dependency resolution."""
        # Create tasks with dependencies
        task_a = ManagedTask(
            id="task_a",
            title="Task A",
            description="Independent task",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        task_b = ManagedTask(
            id="task_b",
            title="Task B",
            description="Depends on Task A",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        task_c = ManagedTask(
            id="task_c",
            title="Task C",
            description="Depends on Task B",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        execution_order = []

        async def mock_execute(task):
            execution_order.append(task.id)
            await asyncio.sleep(0.1)
            return f"Result for {task.id}"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute_method:
            mock_execute_method.side_effect = mock_execute

            # Submit tasks in reverse dependency order
            await orchestrator.submit_task(task_c, dependencies=["task_b"])
            await orchestrator.submit_task(task_b, dependencies=["task_a"])
            await orchestrator.submit_task(task_a, dependencies=[])

            # Wait for all tasks
            await asyncio.gather(
                orchestrator.wait_for_task("task_a", timeout=5.0),
                orchestrator.wait_for_task("task_b", timeout=5.0),
                orchestrator.wait_for_task("task_c", timeout=5.0)
            )

            # Verify execution order respects dependencies
            assert execution_order == ["task_a", "task_b", "task_c"]

    async def test_cycle_detection(self, orchestrator):
        """Test dependency cycle detection."""
        task_a = ManagedTask(id="task_a", title="Task A", description="Test", category=TaskCategory.OTHER)
        task_b = ManagedTask(id="task_b", title="Task B", description="Test", category=TaskCategory.OTHER)

        # Submit first task
        await orchestrator.submit_task(task_a, dependencies=["task_b"])

        # Attempting to create a cycle should raise an error
        with pytest.raises(ValueError, match="would create a cycle"):
            await orchestrator.submit_task(task_b, dependencies=["task_a"])

    async def test_task_timeout(self, orchestrator, sample_task):
        """Test task timeout handling."""
        async def slow_task(task):
            await asyncio.sleep(2.0)  # Longer than timeout
            return "Should not complete"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = slow_task

            # Submit with short timeout
            task_id = await orchestrator.submit_task(sample_task, timeout_seconds=0.5)

            # Should timeout
            with pytest.raises(asyncio.TimeoutError):
                await orchestrator.wait_for_task(task_id, timeout=1.0)

            # Task should be marked as timeout
            orchestration_task = orchestrator.tasks[task_id]
            assert orchestration_task.status == OrchestrationStatus.TIMEOUT

    async def test_task_cancellation(self, orchestrator, sample_task):
        """Test task cancellation."""
        async def long_running_task(task):
            await asyncio.sleep(10.0)
            return "Should be cancelled"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = long_running_task

            task_id = await orchestrator.submit_task(sample_task)

            # Let it start
            await asyncio.sleep(0.1)

            # Cancel the task
            success = await orchestrator.cancel_task(task_id)
            assert success

            # Task should be cancelled
            orchestration_task = orchestrator.tasks[task_id]
            assert orchestration_task.status == OrchestrationStatus.CANCELLED

    async def test_agent_resource_limits(self, orchestrator):
        """Test agent resource limit enforcement."""
        # Configure tight limits for testing
        orchestrator.default_agent_limits['max_concurrent_tasks'] = 2

        tasks = [
            ManagedTask(
                id=f"task_{i}",
                title=f"Agent Task {i}",
                description="Test task for agent limits",
                category=TaskCategory.OTHER,
                status=TaskStatus.PENDING
            )
            for i in range(4)
        ]

        async def slow_task(task):
            await asyncio.sleep(0.5)
            return f"Result for {task.id}"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = slow_task

            # Submit all tasks to same agent
            for task in tasks:
                await orchestrator.submit_task(task, assigned_agent="test_agent")

            # Check that resource constraints are hit
            await asyncio.sleep(0.2)  # Let some tasks start

            metrics = await orchestrator.get_orchestration_metrics()
            assert metrics['orchestration_metrics']['resource_constraints_hit'] > 0

    async def test_retry_logic(self, orchestrator, sample_task):
        """Test task retry on failure."""
        call_count = 0

        async def failing_task(task):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times
                raise Exception(f"Attempt {call_count} failed")
            return "Success on retry"

        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = failing_task

            task_id = await orchestrator.submit_task(sample_task)
            result = await orchestrator.wait_for_task(task_id, timeout=5.0)

            assert result == "Success on retry"
            assert call_count == 3  # Original + 2 retries

    async def test_metrics_collection(self, orchestrator, sample_task):
        """Test metrics collection."""
        with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Test result"

            # Submit and complete a task
            task_id = await orchestrator.submit_task(sample_task)
            await orchestrator.wait_for_task(task_id, timeout=5.0)

            metrics = await orchestrator.get_orchestration_metrics()

            assert metrics['total_tasks'] >= 1
            assert metrics['completed_tasks'] >= 1
            assert metrics['orchestration_metrics']['tasks_submitted'] >= 1
            assert metrics['orchestration_metrics']['tasks_completed'] >= 1


class TestOrchestrationConfig:
    """Test suite for orchestration configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OrchestrationConfig()

        assert config.enabled is True
        assert config.max_concurrent_tasks == 10
        assert config.default_task_timeout_seconds == 300.0
        assert config.default_agent_max_concurrent_tasks == 3

    def test_config_manager(self):
        """Test configuration manager."""
        manager = OrchestrationConfigManager()
        config = manager.get_config()

        assert isinstance(config, OrchestrationConfig)

        # Test updates
        manager.update_config(max_concurrent_tasks=20)
        assert config.max_concurrent_tasks == 20

    def test_agent_specific_config(self):
        """Test agent-specific configuration."""
        manager = OrchestrationConfigManager()

        # Set agent config
        agent_config = {
            'max_concurrent_tasks': 5,
            'max_requests_per_minute': 120
        }
        manager.set_agent_config('test_agent', agent_config)

        # Get agent config
        retrieved_config = manager.get_agent_config('test_agent')
        assert retrieved_config['max_concurrent_tasks'] == 5
        assert retrieved_config['max_requests_per_minute'] == 120

    @patch.dict('os.environ', {'ORCHESTRATION_ENABLED': 'false', 'ORCHESTRATION_MAX_CONCURRENT': '15'})
    def test_environment_variables(self):
        """Test loading configuration from environment variables."""
        manager = OrchestrationConfigManager()
        config = manager.get_config()

        assert config.enabled is False
        assert config.max_concurrent_tasks == 15


class TestEnhancedScheduler:
    """Test suite for enhanced scheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create a test scheduler."""
        return EnhancedTaskScheduler()

    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initialization."""
        assert scheduler is not None
        assert scheduler._async_enabled is False
        assert scheduler._execution_stats['sync_executions'] == 0

    async def test_async_mode_initialization(self, scheduler):
        """Test async mode initialization."""
        with patch('framework.helpers.enhanced_scheduler.is_orchestration_enabled', return_value=True):
            with patch('framework.helpers.enhanced_scheduler.get_orchestrator') as mock_get_orchestrator:
                mock_orchestrator = AsyncMock()
                mock_get_orchestrator.return_value = mock_orchestrator

                await scheduler.initialize_async_mode()

                assert scheduler._async_enabled is True
                assert scheduler._orchestrator is not None

    async def test_enhanced_tick_sync_mode(self, scheduler):
        """Test enhanced tick in sync mode."""
        with patch('framework.helpers.enhanced_scheduler.is_orchestration_enabled', return_value=False):
            with patch.object(scheduler, '_sync_tick', new_callable=AsyncMock) as mock_sync_tick:
                mock_sync_tick.return_value = {
                    'mode': 'sync',
                    'tasks_processed': 1,
                    'concurrent_tasks': 0,
                    'errors': [],
                    'execution_time': 0.1
                }

                result = await scheduler.enhanced_tick()

                assert result['mode'] == 'sync'
                assert result['tasks_processed'] == 1
                mock_sync_tick.assert_called_once()

    async def test_enhanced_tick_async_mode(self, scheduler):
        """Test enhanced tick in async mode."""
        with patch('framework.helpers.enhanced_scheduler.is_orchestration_enabled', return_value=True):
            with patch('framework.helpers.enhanced_scheduler.should_use_sync_fallback', return_value=False):
                with patch.object(scheduler, 'initialize_async_mode', new_callable=AsyncMock):
                    with patch.object(scheduler, '_async_tick', new_callable=AsyncMock) as mock_async_tick:
                        mock_async_tick.return_value = {
                            'mode': 'async',
                            'tasks_processed': 3,
                            'concurrent_tasks': 3,
                            'errors': [],
                            'execution_time': 0.05
                        }

                        scheduler._async_enabled = True
                        scheduler._orchestrator = AsyncMock()

                        result = await scheduler.enhanced_tick()

                        assert result['mode'] == 'async'
                        assert result['tasks_processed'] == 3
                        assert result['concurrent_tasks'] == 3
                        mock_async_tick.assert_called_once()

    async def test_fallback_to_sync(self, scheduler):
        """Test fallback to sync mode on error."""
        with patch('framework.helpers.enhanced_scheduler.is_orchestration_enabled', return_value=True):
            with patch('framework.helpers.enhanced_scheduler.should_use_sync_fallback', return_value=True):
                with patch.object(scheduler, '_async_tick', new_callable=AsyncMock) as mock_async_tick:
                    with patch.object(scheduler, '_sync_tick', new_callable=AsyncMock) as mock_sync_tick:
                        # Async tick fails
                        mock_async_tick.side_effect = Exception("Async failed")
                        mock_sync_tick.return_value = {
                            'mode': 'sync',
                            'tasks_processed': 1,
                            'concurrent_tasks': 0,
                            'errors': [],
                            'execution_time': 0.1
                        }

                        scheduler._async_enabled = True
                        scheduler._orchestrator = AsyncMock()

                        result = await scheduler.enhanced_tick()

                        assert result['mode'] == 'sync'
                        assert scheduler._execution_stats['fallbacks_to_sync'] > 0


class TestPerformanceIntegration:
    """Test performance monitoring integration."""

    async def test_concurrent_performance_improvement(self):
        """Test that concurrent execution shows performance improvement."""
        orchestrator = AsyncTaskOrchestrator(
            max_concurrent_tasks=5,
            enable_performance_monitoring=False
        )
        await orchestrator.start()

        try:
            # Create tasks that simulate different durations
            tasks = []
            for i in range(5):
                task = ManagedTask(
                    id=f"perf_task_{i}",
                    title=f"Performance Task {i}",
                    description="Performance test task",
                    category=TaskCategory.OTHER,
                    status=TaskStatus.PENDING
                )
                tasks.append(task)

            async def mock_execute(task):
                # Simulate variable work duration
                await asyncio.sleep(0.2)
                return f"Result for {task.id}"

            with patch.object(orchestrator, '_execute_managed_task', new_callable=AsyncMock) as mock_execute_method:
                mock_execute_method.side_effect = mock_execute

                # Test concurrent execution
                start_time = time.time()

                # Submit all tasks
                task_ids = []
                for task in tasks:
                    task_id = await orchestrator.submit_task(task)
                    task_ids.append(task_id)

                # Wait for completion
                await asyncio.gather(*[
                    orchestrator.wait_for_task(task_id, timeout=5.0)
                    for task_id in task_ids
                ])

                concurrent_time = time.time() - start_time

                # Concurrent execution should be significantly faster than sequential
                # Sequential would be 5 * 0.2 = 1.0 seconds
                # Concurrent should be ~0.2 seconds + overhead
                assert concurrent_time < 0.5

                # Get metrics
                metrics = await orchestrator.get_orchestration_metrics()
                assert metrics['total_tasks'] == 5
                assert metrics['completed_tasks'] == 5

        finally:
            await orchestrator.stop()


if __name__ == "__main__":
    # Run basic tests
    async def run_basic_tests():
        print("Running basic async orchestration tests...")

        # Test orchestrator lifecycle
        orchestrator = AsyncTaskOrchestrator(enable_performance_monitoring=False)
        await orchestrator.start()

        # Test task submission and execution
        task = ManagedTask(
            id="test_task",
            title="Basic Test Task",
            description="Testing basic functionality",
            category=TaskCategory.OTHER,
            status=TaskStatus.PENDING
        )

        # Mock execution
        original_execute = orchestrator._execute_managed_task
        async def mock_execute(managed_task):
            await asyncio.sleep(0.1)
            return f"Completed: {managed_task.title}"

        orchestrator._execute_managed_task = mock_execute

        task_id = await orchestrator.submit_task(task)
        result = await orchestrator.wait_for_task(task_id, timeout=5.0)

        print(f"✓ Task completed with result: {result}")

        # Test metrics
        metrics = await orchestrator.get_orchestration_metrics()
        print(f"✓ Orchestration metrics: {metrics['total_tasks']} total, {metrics['completed_tasks']} completed")

        await orchestrator.stop()
        print("✓ Basic tests completed successfully")

    # Run the tests
    asyncio.run(run_basic_tests())
