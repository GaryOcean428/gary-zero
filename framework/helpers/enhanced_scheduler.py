"""
Enhanced scheduler integration for hierarchical planning and async orchestration.

Provides an enhanced scheduler that can operate in both sync and async modes,
with seamless integration with hierarchical planners and AsyncTaskOrchestrator,
enabling automatic plan execution, monitoring, and improved concurrency.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

# Async orchestration & scheduling imports (Copilot preferred)
from framework.helpers.async_orchestrator import (
    AsyncTaskOrchestrator,
    get_orchestrator,
)

# Hierarchical planning imports
from framework.helpers.hierarchical_planner import (
    HierarchicalPlan,
    HierarchicalPlanner,
    PlanStatus,
    Subtask,
    SubtaskStatus,
)
from framework.helpers.orchestration_config import (
    get_orchestration_config,
    is_orchestration_enabled,
    should_use_sync_fallback,
)
from framework.helpers.plan_evaluation import EvaluationLoop
from framework.helpers.planner_config import PlannerSettings
from framework.helpers.task_management import TaskScheduler as BaseTaskScheduler
from framework.helpers.task_manager import Task as ManagedTask
from framework.helpers.task_manager import TaskCategory, TaskStatus
from framework.helpers.task_models import PlannedTask, TaskPlan, TaskState
from framework.performance.monitor import get_performance_monitor

logger = logging.getLogger(__name__)

# -- PLAN EXECUTION MONITOR (Hierarchical planning, evaluation & feedback) --


class PlanExecutionMonitor:
    """Monitors plan execution and handles evaluation feedback."""

    def __init__(self, planner: HierarchicalPlanner):
        self.planner = planner
        self.evaluation_loop = EvaluationLoop()
        self.task_to_plan_mapping: dict[str, str] = {}  # task_uuid -> plan_id
        self.task_to_subtask_mapping: dict[str, str] = {}  # task_uuid -> subtask_id

    def register_plan_execution(
        self, plan_id: str, task_mappings: dict[str, str]
    ) -> None:
        for task_uuid, subtask_id in task_mappings.items():
            self.task_to_plan_mapping[task_uuid] = plan_id
            self.task_to_subtask_mapping[task_uuid] = subtask_id

    async def handle_task_completion(self, task_uuid: str, result: str) -> None:
        if task_uuid not in self.task_to_plan_mapping:
            return
        plan_id = self.task_to_plan_mapping[task_uuid]
        subtask_id = self.task_to_subtask_mapping[task_uuid]
        plan = self.planner.get_plan(plan_id)
        if not plan:
            logger.warning(f"Plan {plan_id} not found for completed task {task_uuid}")
            return
        subtask = plan.get_subtask_by_id(subtask_id)
        if not subtask:
            logger.warning(f"Subtask {subtask_id} not found in plan {plan_id}")
            return
        # Evaluate subtask completion
        success = self.evaluation_loop.process_subtask_completion(plan, subtask, result)
        if success:
            logger.info(f"Subtask '{subtask.name}' completed successfully")
            await self._check_plan_completion(plan)
        else:
            logger.info(f"Subtask '{subtask.name}' required plan adjustment")
            await self._handle_plan_adjustment(plan)

    async def _check_plan_completion(self, plan: HierarchicalPlan) -> None:
        if plan.is_complete():
            plan.status = PlanStatus.COMPLETED
            plan.updated_at = datetime.now(UTC)
            logger.info(f"Plan '{plan.id}' completed successfully")
        elif plan.has_failed_subtasks():
            failed_count = sum(
                1 for s in plan.subtasks if s.status == SubtaskStatus.FAILED
            )
            if failed_count > len(plan.subtasks) // 2:
                plan.status = PlanStatus.FAILED
                logger.warning(
                    f"Plan '{plan.id}' failed with {failed_count} failed subtasks"
                )

    async def _handle_plan_adjustment(self, plan: HierarchicalPlan) -> None:
        from framework.helpers.task_management import TaskScheduler

        scheduler = TaskScheduler.get()
        new_tasks = []
        for subtask in plan.subtasks:
            if (
                subtask.status == SubtaskStatus.PENDING
                and subtask.id not in self.task_to_subtask_mapping.values()
            ):
                new_tasks.append(subtask)
        if new_tasks:
            await self._schedule_subtasks(plan, new_tasks, scheduler)
            logger.info(f"Scheduled {len(new_tasks)} new subtasks for plan adjustment")

    async def _schedule_subtasks(
        self, plan: HierarchicalPlan, subtasks: list[Subtask], scheduler
    ) -> None:
        base_time = datetime.now(UTC)
        for i, subtask in enumerate(subtasks):
            execution_time = base_time + timedelta(seconds=30 + (i * 15))
            task_plan = TaskPlan.create(todo=[execution_time])
            planned_task = PlannedTask.create(
                name=f"Subtask: {subtask.name}",
                system_prompt="You are an autonomous agent executing a subtask as part of a hierarchical plan.",
                prompt=f"Execute this subtask: {subtask.description}\n\nRecommended tool: {subtask.tool_name or 'auto-select'}",
                plan=task_plan,
                context_id=plan.context_id,
            )
            scheduler.add_task(planned_task)
            self.task_to_plan_mapping[planned_task.uuid] = plan.id
            self.task_to_subtask_mapping[planned_task.uuid] = subtask.id


# -- ENHANCED HIERARCHICAL SCHEDULER (Hierarchical Planning) --


class EnhancedHierarchicalScheduler:
    """Enhanced scheduler that integrates hierarchical planning with TaskScheduler."""

    def __init__(self):
        self.planner = HierarchicalPlanner()
        self.monitor = PlanExecutionMonitor(self.planner)
        self.config = PlannerSettings.get_config()

    def create_and_execute_plan(
        self, objective: str, context_id: str | None = None, auto_execute: bool = True
    ) -> HierarchicalPlan:
        self.planner.config = self.config
        plan = self.planner.create_plan(objective, context_id)
        if auto_execute and self.config.auto_planning_enabled:
            self.execute_plan_enhanced(plan.id)
        return plan

    def execute_plan_enhanced(self, plan_id: str) -> bool:
        from framework.helpers.task_management import TaskScheduler

        plan = self.planner.get_plan(plan_id)
        if not plan:
            logger.error(f"Plan not found: {plan_id}")
            return False
        plan.status = PlanStatus.IN_PROGRESS
        plan.updated_at = datetime.now(UTC)
        scheduler = TaskScheduler.get()
        task_mappings = {}
        base_time = datetime.now(UTC)
        for i, subtask in enumerate(plan.subtasks):
            execution_time = self._calculate_subtask_timing(plan, subtask, base_time)
            task_plan = TaskPlan.create(todo=[execution_time])
            enhanced_prompt = self._create_enhanced_prompt(subtask, plan.objective)
            planned_task = PlannedTask.create(
                name=f"Subtask: {subtask.name}",
                system_prompt="You are an autonomous agent executing a subtask as part of a hierarchical plan. Focus on producing high-quality, detailed output that can be evaluated and built upon.",
                prompt=enhanced_prompt,
                plan=task_plan,
                context_id=plan.context_id,
            )
            scheduler.add_task(planned_task)
            task_mappings[planned_task.uuid] = subtask.id
        self.monitor.register_plan_execution(plan_id, task_mappings)
        logger.info(
            f"Started enhanced execution of plan '{plan_id}' with {len(plan.subtasks)} subtasks"
        )
        return True

    def _calculate_subtask_timing(
        self, plan: HierarchicalPlan, subtask: Subtask, base_time: datetime
    ) -> datetime:
        if not subtask.dependencies:
            return base_time
        max_depth = 0
        for dep_id in subtask.dependencies:
            dep_subtask = plan.get_subtask_by_id(dep_id)
            if dep_subtask:
                depth = self._get_subtask_depth(plan, dep_subtask) + 1
                max_depth = max(max_depth, depth)
        delay_minutes = max_depth * 5
        return base_time + timedelta(minutes=delay_minutes)

    def _get_subtask_depth(self, plan: HierarchicalPlan, subtask: Subtask) -> int:
        if not subtask.dependencies:
            return 0
        max_depth = 0
        for dep_id in subtask.dependencies:
            dep_subtask = plan.get_subtask_by_id(dep_id)
            if dep_subtask:
                depth = self._get_subtask_depth(plan, dep_subtask) + 1
                max_depth = max(max_depth, depth)
        return max_depth

    def _create_enhanced_prompt(self, subtask: Subtask, objective: str) -> str:
        prompt = f"""You are executing a subtask as part of achieving this objective: {objective}

SUBTASK: {subtask.name}
DESCRIPTION: {subtask.description}
RECOMMENDED TOOL: {subtask.tool_name or "Select the most appropriate tool"}

IMPORTANT EXECUTION GUIDELINES:
1. Produce detailed, high-quality output that can be evaluated and used by subsequent subtasks
2. If using search tools, include specific URLs and sources
3. If analyzing content, provide structured summaries with key points
4. If creating content, ensure it's well-formatted and comprehensive
5. If encountering errors, provide clear explanation and suggest alternatives

Your output will be evaluated for quality, completeness, and usefulness for achieving the overall objective.
Focus on creating output that clearly demonstrates successful completion of the subtask."""
        return prompt

    def get_enhanced_plan_status(self, plan_id: str) -> dict[str, Any] | None:
        basic_status = self.planner.get_plan_progress(plan_id)
        if not basic_status:
            return None
        plan = self.planner.get_plan(plan_id)
        if not plan:
            return basic_status
        basic_status.update(
            {
                "evaluation_enabled": self.config.verification_enabled,
                "retry_enabled": self.config.retry_failed_subtasks,
                "auto_planning": self.config.auto_planning_enabled,
                "subtask_details": [
                    {
                        "id": subtask.id,
                        "name": subtask.name,
                        "status": subtask.status,
                        "tool": subtask.tool_name,
                        "dependencies": len(subtask.dependencies),
                        "started_at": subtask.started_at.isoformat()
                        if subtask.started_at
                        else None,
                        "completed_at": subtask.completed_at.isoformat()
                        if subtask.completed_at
                        else None,
                        "result_preview": subtask.result[:100] + "..."
                        if subtask.result and len(subtask.result) > 100
                        else subtask.result,
                        "error": subtask.error,
                    }
                    for subtask in plan.subtasks
                ],
            }
        )
        return basic_status

    def update_configuration(self, **kwargs) -> dict[str, Any]:
        self.config = PlannerSettings.update_config(**kwargs)
        self.planner.config = self.config
        return PlannerSettings.get_settings_dict()

    async def handle_task_completion_callback(
        self, task_uuid: str, result: str
    ) -> None:
        await self.monitor.handle_task_completion(task_uuid, result)


# -- ENHANCED TASK SCHEDULER WITH ASYNC ORCHESTRATION --


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
        self._initialization_lock = (
            asyncio.Lock() if asyncio.get_event_loop().is_running() else None
        )
        self._pending_async_tasks: dict[str, dict[str, Any]] = {}
        self._task_mapping: dict[
            str, str
        ] = {}  # scheduler task id -> orchestration task id
        self._performance_monitor = get_performance_monitor()
        self._execution_stats = {
            "sync_executions": 0,
            "async_executions": 0,
            "concurrent_executions": 0,
            "fallbacks_to_sync": 0,
            "total_time_saved": 0.0,
        }
        logger.info("EnhancedTaskScheduler initialized")

    async def initialize_async_mode(self):
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
                enable_performance_monitoring=config.enable_performance_monitoring,
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
        start_time = time.time()
        execution_info = {
            "mode": "sync",
            "tasks_processed": 0,
            "concurrent_tasks": 0,
            "errors": [],
            "execution_time": 0.0,
        }
        try:
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
            execution_info["errors"].append(str(e))
            if should_use_sync_fallback() and execution_info["mode"] != "sync":
                logger.info("Falling back to sync mode due to error")
                execution_info = await self._sync_tick()
                self._execution_stats["fallbacks_to_sync"] += 1
        finally:
            execution_info["execution_time"] = time.time() - start_time
        return execution_info

    async def _async_tick(self) -> dict[str, Any]:
        execution_info = {
            "mode": "async",
            "tasks_processed": 0,
            "concurrent_tasks": 0,
            "errors": [],
            "execution_time": 0.0,
        }
        if not self._orchestrator:
            raise RuntimeError("Async orchestrator not initialized")
        due_tasks = self._tasks.get_due_tasks()
        if not due_tasks:
            return execution_info
        task_groups = self._group_tasks_for_execution(due_tasks)
        concurrent_submissions = []
        for group in task_groups:
            for task in group:
                try:
                    managed_task = self._convert_to_managed_task(task)
                    orchestration_task_id = await self._orchestrator.submit_task(
                        managed_task,
                        dependencies=self._get_task_dependencies(task),
                        priority=self._get_task_priority(task),
                        timeout_seconds=self._get_task_timeout(task),
                        assigned_agent=self._get_task_agent(task),
                    )
                    self._task_mapping[task.uuid] = orchestration_task_id
                    monitor_coro = self._monitor_async_task(task, orchestration_task_id)
                    concurrent_submissions.append(monitor_coro)
                    execution_info["tasks_processed"] += 1
                except Exception as e:
                    error_msg = f"Failed to submit task {task.name}: {e}"
                    logger.error(error_msg)
                    execution_info["errors"].append(error_msg)
        if concurrent_submissions:
            execution_info["concurrent_tasks"] = len(concurrent_submissions)
            for coro in concurrent_submissions:
                asyncio.create_task(coro)
            self._execution_stats["async_executions"] += 1
            self._execution_stats["concurrent_executions"] += execution_info[
                "concurrent_tasks"
            ]
        return execution_info

    async def _sync_tick(self) -> dict[str, Any]:
        execution_info = {
            "mode": "sync",
            "tasks_processed": 0,
            "concurrent_tasks": 0,
            "errors": [],
            "execution_time": 0.0,
        }
        await super().tick()
        due_tasks = self._tasks.get_due_tasks()
        execution_info["tasks_processed"] = len(due_tasks)
        self._execution_stats["sync_executions"] += 1
        return execution_info

    async def _monitor_async_task(
        self, scheduler_task: Any, orchestration_task_id: str
    ):
        try:
            result = await self._orchestrator.wait_for_task(orchestration_task_id)
            self.update_task(
                scheduler_task.uuid,
                state=TaskState.FINISHED,
                last_result=str(result) if result else "Completed",
            )
            await scheduler_task.on_success(str(result) if result else "Completed")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Async task {scheduler_task.name} failed: {error_msg}")
            self.update_task(
                scheduler_task.uuid,
                state=TaskState.FINISHED,
                last_result=f"Error: {error_msg}",
            )
            await scheduler_task.on_error(error_msg)
        finally:
            await scheduler_task.on_finish()
            self._task_mapping.pop(scheduler_task.uuid, None)

    def _group_tasks_for_execution(self, tasks: list[Any]) -> list[list[Any]]:
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

    def _convert_to_managed_task(self, scheduler_task: Any) -> ManagedTask:
        category_mapping = {
            "system": TaskCategory.SYSTEM,
            "analysis": TaskCategory.ANALYSIS,
            "research": TaskCategory.RESEARCH,
            "coding": TaskCategory.CODING,
            "creative": TaskCategory.CREATIVE,
            "communication": TaskCategory.COMMUNICATION,
        }
        category = TaskCategory.OTHER
        if hasattr(scheduler_task, "prompt"):
            prompt_lower = scheduler_task.prompt.lower()
            for keyword, cat in category_mapping.items():
                if keyword in prompt_lower:
                    category = cat
                    break
        managed_task = ManagedTask(
            id=scheduler_task.uuid,
            title=scheduler_task.name,
            description=getattr(scheduler_task, "prompt", scheduler_task.name),
            category=category,
            status=TaskStatus.PENDING,
            created_at=scheduler_task.created_at,
        )
        return managed_task

    def _get_task_dependencies(self, task: Any) -> list[str]:
        # For now, no explicit dependencies in scheduler tasks
        return []

    def _get_task_priority(self, task: Any) -> int:
        # Default priority, could be enhanced with task-specific priority logic
        return 0

    def _get_task_timeout(self, task: Any) -> float | None:
        config = get_orchestration_config()
        return config.default_task_timeout_seconds

    def _get_task_agent(self, task: Any) -> str | None:
        # Could be extracted from task context or configuration
        return None

    async def submit_async_task(
        self,
        task: Any,
        dependencies: list[str] | None = None,
        priority: int = 0,
        assigned_agent: str | None = None,
    ) -> str:
        if not self._async_enabled:
            await self.initialize_async_mode()
        if not self._orchestrator:
            raise RuntimeError("Async orchestration not available")
        managed_task = self._convert_to_managed_task(task)
        orchestration_task_id = await self._orchestrator.submit_task(
            managed_task,
            dependencies=dependencies,
            priority=priority,
            assigned_agent=assigned_agent,
        )
        self._task_mapping[task.uuid] = orchestration_task_id
        self.add_task(task)
        asyncio.create_task(self._monitor_async_task(task, orchestration_task_id))
        logger.info(
            f"Submitted async task {task.name} with orchestration ID {orchestration_task_id}"
        )
        return orchestration_task_id

    async def wait_for_async_task(
        self, task_uuid: str, timeout: float | None = None
    ) -> Any:
        orchestration_task_id = self._task_mapping.get(task_uuid)
        if not orchestration_task_id:
            raise ValueError(f"No async task found for UUID {task_uuid}")
        if not self._orchestrator:
            raise RuntimeError("Async orchestration not available")
        return await self._orchestrator.wait_for_task(orchestration_task_id, timeout)

    async def cancel_async_task(self, task_uuid: str) -> bool:
        orchestration_task_id = self._task_mapping.get(task_uuid)
        if not orchestration_task_id or not self._orchestrator:
            return False
        success = await self._orchestrator.cancel_task(orchestration_task_id)
        if success:
            self.update_task(
                task_uuid, state=TaskState.FINISHED, last_result="Cancelled"
            )
            self._task_mapping.pop(task_uuid, None)
        return success

    async def get_orchestration_metrics(self) -> dict[str, Any]:
        base_metrics = {
            "total_scheduler_tasks": len(self.get_tasks()),
            "execution_stats": self._execution_stats.copy(),
            "async_enabled": self._async_enabled,
            "orchestration_available": self._orchestrator is not None,
        }
        if self._orchestrator:
            orchestration_metrics = await self._orchestrator.get_orchestration_metrics()
            base_metrics["orchestration"] = orchestration_metrics
        return base_metrics

    def get_execution_stats(self) -> dict[str, Any]:
        return self._execution_stats.copy()


# Enhanced singleton pattern
_enhanced_scheduler: EnhancedTaskScheduler | None = None


def get_enhanced_scheduler() -> EnhancedTaskScheduler:
    global _enhanced_scheduler
    if _enhanced_scheduler is None:
        _enhanced_scheduler = EnhancedTaskScheduler()
    return _enhanced_scheduler


async def run_enhanced_tick() -> dict[str, Any]:
    scheduler = get_enhanced_scheduler()
    return await scheduler.enhanced_tick()


# Compatibility functions
async def tick_with_orchestration():
    return await run_enhanced_tick()


def get_scheduler() -> EnhancedTaskScheduler:
    return get_enhanced_scheduler()
