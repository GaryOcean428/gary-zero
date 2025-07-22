"""
Enhanced Task Scheduler with Async Orchestration Integration

Provides an enhanced scheduler that can operate in both sync and async modes,
with seamless integration with the AsyncTaskOrchestrator for improved
concurrency and performance.
"""

import asyncio
import logging
import time
from typing import Any

from framework.helpers.async_orchestrator import (
    AsyncTaskOrchestrator,
    get_orchestrator,
)
from framework.helpers.orchestration_config import (
    get_orchestration_config,
    is_orchestration_enabled,
    should_use_sync_fallback,
)
from framework.helpers.task_management import TaskScheduler as BaseTaskScheduler
from framework.helpers.task_manager import Task as ManagedTask
from framework.helpers.task_manager import TaskCategory, TaskStatus
from framework.helpers.task_models import AdHocTask, PlannedTask, ScheduledTask, Task, TaskState
from framework.performance.monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class EnhancedTaskScheduler(BaseTaskScheduler):
    """
    Enhanced task scheduler with async orchestration capabilities.
    
    Maintains backward compatibility while adding:
    - Async task orchestration with dependency management
    - Concurrency controls and resource management
    - Performance-adaptive scheduling
    - Multi-agent coordination
    """

    def __init__(self):
        super().__init__()
        self._orchestrator: AsyncTaskOrchestrator | None = None
        self._async_enabled = False
        self._initialization_lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
        self._pending_async_tasks: dict[str, dict[str, Any]] = {}
        self._task_mapping: dict[str, str] = {}  # scheduler task id -> orchestration task id

        # Performance tracking
        self._performance_monitor = get_performance_monitor()
        self._execution_stats = {
            'sync_executions': 0,
            'async_executions': 0,
            'concurrent_executions': 0,
            'fallbacks_to_sync': 0,
            'total_time_saved': 0.0
        }

        logger.info("EnhancedTaskScheduler initialized")

    async def initialize_async_mode(self):
        """Initialize async orchestration mode."""
        if self._async_enabled:
            return

        config = get_orchestration_config()

        if not config.enabled:
            logger.info("Async orchestration disabled by configuration")
            return

        try:
            self._orchestrator = await get_orchestrator(
                max_concurrent_tasks=config.max_concurrent_tasks,
                default_task_timeout=config.default_task_timeout_seconds,
                enable_performance_monitoring=config.enable_performance_monitoring
            )

            self._async_enabled = True
            logger.info("Async orchestration mode initialized")

        except Exception as e:
            logger.error(f"Failed to initialize async mode: {e}")
            if should_use_sync_fallback():
                logger.info("Falling back to sync mode")
            else:
                raise

    async def enhanced_tick(self) -> dict[str, Any]:
        """
        Enhanced tick method with async orchestration support.
        
        Returns metrics about the tick execution.
        """
        start_time = time.time()
        execution_info = {
            'mode': 'sync',
            'tasks_processed': 0,
            'concurrent_tasks': 0,
            'errors': [],
            'execution_time': 0.0
        }

        try:
            # Check if we should use async mode
            if is_orchestration_enabled() and not should_use_sync_fallback():
                if not self._async_enabled:
                    await self.initialize_async_mode()

                if self._async_enabled:
                    execution_info = await self._async_tick()
                else:
                    execution_info = await self._sync_tick()
            else:
                execution_info = await self._sync_tick()

        except Exception as e:
            logger.error(f"Error in enhanced tick: {e}")
            execution_info['errors'].append(str(e))

            # Fallback to sync if enabled
            if should_use_sync_fallback() and execution_info['mode'] != 'sync':
                logger.info("Falling back to sync mode due to error")
                execution_info = await self._sync_tick()
                self._execution_stats['fallbacks_to_sync'] += 1

        finally:
            execution_info['execution_time'] = time.time() - start_time

        return execution_info

    async def _async_tick(self) -> dict[str, Any]:
        """Process due tasks using async orchestration."""
        execution_info = {
            'mode': 'async',
            'tasks_processed': 0,
            'concurrent_tasks': 0,
            'errors': [],
            'execution_time': 0.0
        }

        if not self._orchestrator:
            raise RuntimeError("Async orchestrator not initialized")

        # Get due tasks
        due_tasks = self._tasks.get_due_tasks()

        if not due_tasks:
            return execution_info

        # Group tasks for potential concurrent execution
        task_groups = self._group_tasks_for_execution(due_tasks)

        concurrent_submissions = []

        for group in task_groups:
            for task in group:
                try:
                    # Convert scheduler task to managed task
                    managed_task = self._convert_to_managed_task(task)

                    # Submit to orchestrator
                    orchestration_task_id = await self._orchestrator.submit_task(
                        managed_task,
                        dependencies=self._get_task_dependencies(task),
                        priority=self._get_task_priority(task),
                        timeout_seconds=self._get_task_timeout(task),
                        assigned_agent=self._get_task_agent(task)
                    )

                    # Track mapping
                    self._task_mapping[task.uuid] = orchestration_task_id

                    # Create monitoring coroutine
                    monitor_coro = self._monitor_async_task(task, orchestration_task_id)
                    concurrent_submissions.append(monitor_coro)

                    execution_info['tasks_processed'] += 1

                except Exception as e:
                    error_msg = f"Failed to submit task {task.name}: {e}"
                    logger.error(error_msg)
                    execution_info['errors'].append(error_msg)

        # Wait for all submissions to complete monitoring setup
        if concurrent_submissions:
            execution_info['concurrent_tasks'] = len(concurrent_submissions)

            # Start all monitoring tasks but don't wait for completion
            # (they will handle task lifecycle independently)
            for coro in concurrent_submissions:
                asyncio.create_task(coro)

            self._execution_stats['async_executions'] += 1
            self._execution_stats['concurrent_executions'] += execution_info['concurrent_tasks']

        return execution_info

    async def _sync_tick(self) -> dict[str, Any]:
        """Process due tasks using original sync method."""
        execution_info = {
            'mode': 'sync',
            'tasks_processed': 0,
            'concurrent_tasks': 0,
            'errors': [],
            'execution_time': 0.0
        }

        # Call parent tick method
        await super().tick()

        # Count processed tasks (approximation)
        due_tasks = self._tasks.get_due_tasks()
        execution_info['tasks_processed'] = len(due_tasks)

        self._execution_stats['sync_executions'] += 1

        return execution_info

    async def _monitor_async_task(self, scheduler_task: Task, orchestration_task_id: str):
        """Monitor an async task and update scheduler task state."""
        try:
            # Wait for task completion
            result = await self._orchestrator.wait_for_task(orchestration_task_id)

            # Update scheduler task
            self.update_task(
                scheduler_task.uuid,
                state=TaskState.FINISHED,
                last_result=str(result) if result else "Completed"
            )

            # Call success hook
            await scheduler_task.on_success(str(result) if result else "Completed")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Async task {scheduler_task.name} failed: {error_msg}")

            # Update scheduler task
            self.update_task(
                scheduler_task.uuid,
                state=TaskState.FINISHED,
                last_result=f"Error: {error_msg}"
            )

            # Call error hook
            await scheduler_task.on_error(error_msg)

        finally:
            # Call finish hook
            await scheduler_task.on_finish()

            # Clean up mapping
            self._task_mapping.pop(scheduler_task.uuid, None)

    def _group_tasks_for_execution(self, tasks: list[Task]) -> list[list[Task]]:
        """Group tasks that can be executed concurrently."""
        # Simple implementation - could be enhanced with dependency analysis
        config = get_orchestration_config()
        max_group_size = min(config.max_concurrent_tasks, len(tasks))

        groups = []
        current_group = []

        for task in tasks:
            current_group.append(task)

            if len(current_group) >= max_group_size:
                groups.append(current_group)
                current_group = []

        if current_group:
            groups.append(current_group)

        return groups

    def _convert_to_managed_task(self, scheduler_task: Task) -> ManagedTask:
        """Convert a scheduler task to a managed task."""
        # Map task categories
        category_mapping = {
            'system': TaskCategory.SYSTEM,
            'analysis': TaskCategory.ANALYSIS,
            'research': TaskCategory.RESEARCH,
            'coding': TaskCategory.CODING,
            'creative': TaskCategory.CREATIVE,
            'communication': TaskCategory.COMMUNICATION
        }

        # Infer category from task properties
        category = TaskCategory.OTHER
        if hasattr(scheduler_task, 'prompt'):
            prompt_lower = scheduler_task.prompt.lower()
            for keyword, cat in category_mapping.items():
                if keyword in prompt_lower:
                    category = cat
                    break

        # Create managed task
        managed_task = ManagedTask(
            id=scheduler_task.uuid,
            title=scheduler_task.name,
            description=getattr(scheduler_task, 'prompt', scheduler_task.name),
            category=category,
            status=TaskStatus.PENDING,
            created_at=scheduler_task.created_at
        )

        return managed_task

    def _get_task_dependencies(self, task: Task) -> list[str]:
        """Extract task dependencies."""
        # For now, no explicit dependencies in scheduler tasks
        # This could be enhanced to analyze task content or use explicit dependency fields
        return []

    def _get_task_priority(self, task: Task) -> int:
        """Get task priority."""
        # Default priority, could be enhanced with task-specific priority logic
        return 0

    def _get_task_timeout(self, task: Task) -> float | None:
        """Get task timeout."""
        config = get_orchestration_config()
        return config.default_task_timeout_seconds

    def _get_task_agent(self, task: Task) -> str | None:
        """Get assigned agent for task."""
        # Could be extracted from task context or configuration
        return None

    async def submit_async_task(self,
                               task: ScheduledTask | AdHocTask | PlannedTask,
                               dependencies: list[str] | None = None,
                               priority: int = 0,
                               assigned_agent: str | None = None) -> str:
        """
        Submit a task for async execution with orchestration.
        
        Args:
            task: The task to execute
            dependencies: List of task IDs this task depends on
            priority: Task priority
            assigned_agent: Specific agent assignment
            
        Returns:
            Orchestration task ID for tracking
        """
        if not self._async_enabled:
            await self.initialize_async_mode()

        if not self._orchestrator:
            raise RuntimeError("Async orchestration not available")

        # Convert to managed task
        managed_task = self._convert_to_managed_task(task)

        # Submit to orchestrator
        orchestration_task_id = await self._orchestrator.submit_task(
            managed_task,
            dependencies=dependencies,
            priority=priority,
            assigned_agent=assigned_agent
        )

        # Track mapping
        self._task_mapping[task.uuid] = orchestration_task_id

        # Add to scheduler
        self.add_task(task)

        # Start monitoring
        asyncio.create_task(self._monitor_async_task(task, orchestration_task_id))

        logger.info(f"Submitted async task {task.name} with orchestration ID {orchestration_task_id}")

        return orchestration_task_id

    async def wait_for_async_task(self, task_uuid: str, timeout: float | None = None) -> Any:
        """Wait for an async task to complete."""
        orchestration_task_id = self._task_mapping.get(task_uuid)

        if not orchestration_task_id:
            raise ValueError(f"No async task found for UUID {task_uuid}")

        if not self._orchestrator:
            raise RuntimeError("Async orchestration not available")

        return await self._orchestrator.wait_for_task(orchestration_task_id, timeout)

    async def cancel_async_task(self, task_uuid: str) -> bool:
        """Cancel an async task."""
        orchestration_task_id = self._task_mapping.get(task_uuid)

        if not orchestration_task_id:
            return False

        if not self._orchestrator:
            return False

        success = await self._orchestrator.cancel_task(orchestration_task_id)

        if success:
            # Update scheduler task
            self.update_task(task_uuid, state=TaskState.FINISHED, last_result="Cancelled")
            self._task_mapping.pop(task_uuid, None)

        return success

    async def get_orchestration_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics including orchestration data."""
        base_metrics = {
            'total_scheduler_tasks': len(self.get_tasks()),
            'execution_stats': self._execution_stats.copy(),
            'async_enabled': self._async_enabled,
            'orchestration_available': self._orchestrator is not None
        }

        if self._orchestrator:
            orchestration_metrics = await self._orchestrator.get_orchestration_metrics()
            base_metrics['orchestration'] = orchestration_metrics

        return base_metrics

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        return self._execution_stats.copy()


# Enhanced singleton pattern
_enhanced_scheduler: EnhancedTaskScheduler | None = None

def get_enhanced_scheduler() -> EnhancedTaskScheduler:
    """Get the enhanced scheduler singleton."""
    global _enhanced_scheduler
    if _enhanced_scheduler is None:
        _enhanced_scheduler = EnhancedTaskScheduler()
    return _enhanced_scheduler

async def run_enhanced_tick() -> dict[str, Any]:
    """Run an enhanced tick with orchestration support."""
    scheduler = get_enhanced_scheduler()
    return await scheduler.enhanced_tick()

# Compatibility functions
async def tick_with_orchestration():
    """Tick with orchestration support - compatibility function."""
    return await run_enhanced_tick()

def get_scheduler() -> EnhancedTaskScheduler:
    """Override the original get_scheduler to return enhanced version."""
    return get_enhanced_scheduler()
