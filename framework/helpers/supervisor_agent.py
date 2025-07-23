"""Supervisor agent for orchestrating tasks and managing long-running processes.

This module provides coordination and oversight capabilities for complex
multi-agent workflows, parallel processing, and long-running tasks.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from framework.helpers import settings
from framework.helpers.task_manager import Task, TaskManager, TaskPriority, TaskStatus


@dataclass
class AgentPool:
    """Pool of available agents for parallel execution."""
    coding_agents: list[Any] = field(default_factory=list)
    utility_agents: list[Any] = field(default_factory=list)
    browser_agents: list[Any] = field(default_factory=list)
    general_agents: list[Any] = field(default_factory=list)

    def get_available_agent(self, task_type: str = "general") -> Any | None:
        """Get an available agent for the specified task type."""
        pool_map = {
            "coding": self.coding_agents,
            "utility": self.utility_agents,
            "browser": self.browser_agents,
            "general": self.general_agents
        }

        pool = pool_map.get(task_type, self.general_agents)
        # In a real implementation, this would check agent availability
        return pool[0] if pool else None

    def add_agent(self, agent: Any, agent_type: str = "general"):
        """Add an agent to the appropriate pool."""
        pool_map = {
            "coding": self.coding_agents,
            "utility": self.utility_agents,
            "browser": self.browser_agents,
            "general": self.general_agents
        }

        pool = pool_map.get(agent_type, self.general_agents)
        if agent not in pool:
            pool.append(agent)


@dataclass
class ParallelExecution:
    """Configuration for parallel task execution."""
    max_concurrent_tasks: int = 3
    enable_load_balancing: bool = True
    priority_scheduling: bool = True
    resource_monitoring: bool = True


def _safe_print(message: str, color: str = "default") -> None:
    """Safe print function that falls back to regular print if PrintStyle unavailable."""
    try:
        from framework.helpers.print_style import PrintStyle
        _safe_print(message)
    except ImportError:
        print(f"[{color.upper()}] {message}")


class SupervisorAgent:
    """Supervisor agent for orchestrating multiple agents and managing tasks with parallel processing."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.task_manager = TaskManager.get_instance()
        self.agent_pool = AgentPool()
        self.parallel_config = ParallelExecution(
            max_concurrent_tasks=self.config.get("max_concurrent_tasks", 3),
            enable_load_balancing=self.config.get("enable_load_balancing", True),
            priority_scheduling=self.config.get("priority_scheduling", True)
        )
        self.active_orchestrations: set[str] = set()
        self.handoff_strategies: dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.parallel_config.max_concurrent_tasks)
        self.running_tasks: dict[str, asyncio.Task] = {}

        # Performance monitoring
        self.performance_metrics = {
            "total_tasks_orchestrated": 0,
            "parallel_executions": 0,
            "average_completion_time": 0.0,
            "success_rate": 0.0
        }

    async def orchestrate_parallel_tasks(self, task_ids: list[str]) -> dict[str, Any]:
        """Orchestrate multiple tasks in parallel."""
        _safe_print(f"[Supervisor] Starting parallel orchestration of {len(task_ids)} tasks", "blue")

        self.performance_metrics["parallel_executions"] += 1
        start_time = time.time()

        # Group tasks by type and priority
        grouped_tasks = self._group_tasks_for_parallel_execution(task_ids)

        # Execute tasks in parallel with load balancing
        results = await self._execute_tasks_parallel(grouped_tasks)

        # Update performance metrics
        execution_time = time.time() - start_time
        self._update_performance_metrics(execution_time, results)

        return {
            "status": "completed",
            "execution_time": execution_time,
            "task_results": results,
            "parallel_count": len(task_ids)
        }

    async def _execute_tasks_parallel(self, grouped_tasks: dict[str, list[str]]) -> dict[str, Any]:
        """Execute grouped tasks in parallel."""
        all_tasks = []
        results = {}

        # Create coroutines for each task group
        for task_type, task_ids in grouped_tasks.items():
            for task_id in task_ids:
                # Create async task for each item
                async_task = asyncio.create_task(
                    self._execute_single_task_async(task_id, task_type)
                )
                all_tasks.append((task_id, async_task))
                self.running_tasks[task_id] = async_task

        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.parallel_config.max_concurrent_tasks)

        async def limited_execution(task_id: str, task_coro: asyncio.Task):
            async with semaphore:
                try:
                    result = await task_coro
                    return task_id, result
                except Exception as e:
                    return task_id, {"error": str(e), "status": "failed"}
                finally:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]

        # Wait for all tasks to complete
        completed_tasks = await asyncio.gather(
            *[limited_execution(task_id, task_coro) for task_id, task_coro in all_tasks],
            return_exceptions=True
        )

        # Process results
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                _safe_print(f"[Supervisor] Task execution failed: {task_result}", "red")
            else:
                task_id, result = task_result
                results[task_id] = result

        return results

    async def _execute_single_task_async(self, task_id: str, task_type: str) -> dict[str, Any]:
        """Execute a single task asynchronously."""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found", "status": "failed"}

        try:
            _safe_print(f"[Supervisor] Executing task {task_id[:8]} ({task_type})", "cyan")

            # Get appropriate agent from pool
            agent = self.agent_pool.get_available_agent(task_type)
            if not agent:
                # Fallback to general orchestration
                return await self._fallback_task_execution(task_id)

            # Start task execution monitoring
            start_time = time.time()
            self.task_manager.start_task(task_id, f"supervisor_{task_type}")

            # Simulate task execution (in real implementation, this would call agent methods)
            await asyncio.sleep(0.1)  # Simulate async work

            # Update progress
            self.task_manager.update_task_progress(task_id, 0.5, "Task in progress")
            await asyncio.sleep(0.1)  # More async work

            # Complete task
            execution_time = time.time() - start_time
            self.task_manager.complete_task(task_id, f"Task completed in {execution_time:.2f}s")

            return {
                "status": "completed",
                "execution_time": execution_time,
                "agent_type": task_type
            }

        except Exception as e:
            self.task_manager.fail_task(task_id, str(e))
            return {"error": str(e), "status": "failed"}

    async def _fallback_task_execution(self, task_id: str) -> dict[str, Any]:
        """Fallback execution when no specialized agent is available."""
        try:
            _safe_print(f"[Supervisor] Using fallback execution for task {task_id[:8]}", "yellow")

            # Basic task execution without specialized agent
            start_time = time.time()
            self.task_manager.start_task(task_id, "supervisor_fallback")

            # Simulate work
            await asyncio.sleep(0.2)

            # Complete
            execution_time = time.time() - start_time
            self.task_manager.complete_task(task_id, f"Fallback execution completed in {execution_time:.2f}s")

            return {
                "status": "completed",
                "execution_time": execution_time,
                "agent_type": "fallback"
            }

        except Exception as e:
            self.task_manager.fail_task(task_id, str(e))
            return {"error": str(e), "status": "failed"}

    def _group_tasks_for_parallel_execution(self, task_ids: list[str]) -> dict[str, list[str]]:
        """Group tasks by type and priority for optimal parallel execution."""
        grouped = {
            "coding": [],
            "utility": [],
            "browser": [],
            "general": []
        }

        for task_id in task_ids:
            task = self.task_manager.get_task(task_id)
            if task:
                # Categorize task based on content
                task_type = self._determine_task_type(task)
                grouped[task_type].append(task_id)
            else:
                grouped["general"].append(task_id)

        # Sort by priority within each group
        if self.parallel_config.priority_scheduling:
            for task_type in grouped:
                grouped[task_type] = self._sort_by_priority(grouped[task_type])

        return grouped

    def _determine_task_type(self, task: Task) -> str:
        """Determine the type of task for appropriate agent assignment."""
        description_lower = task.description.lower()
        title_lower = task.title.lower()

        # Check for coding-related keywords
        if any(keyword in description_lower or keyword in title_lower
               for keyword in ["code", "program", "function", "debug", "implement", "script"]):
            return "coding"

        # Check for browser-related keywords
        elif any(keyword in description_lower or keyword in title_lower
                 for keyword in ["browser", "web", "page", "click", "navigate", "scrape"]):
            return "browser"

        # Check for utility keywords
        elif any(keyword in description_lower or keyword in title_lower
                 for keyword in ["analyze", "process", "convert", "calculate", "utility"]):
            return "utility"

        else:
            return "general"

    def _sort_by_priority(self, task_ids: list[str]) -> list[str]:
        """Sort task IDs by their priority."""
        tasks_with_priority = []

        for task_id in task_ids:
            task = self.task_manager.get_task(task_id)
            if task:
                # Convert priority to numeric value for sorting
                priority_value = self._priority_to_numeric(task.priority)
                tasks_with_priority.append((task_id, priority_value))

        # Sort by priority (higher priority first)
        tasks_with_priority.sort(key=lambda x: x[1], reverse=True)

        return [task_id for task_id, _ in tasks_with_priority]

    def _priority_to_numeric(self, priority) -> int:
        """Convert task priority to numeric value."""
        priority_map = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        return priority_map.get(priority, 2)  # Default to medium

    def _update_performance_metrics(self, execution_time: float, results: dict[str, Any]):
        """Update performance metrics after task execution."""
        successful_tasks = sum(1 for result in results.values()
                             if result.get("status") == "completed")
        total_tasks = len(results)

        # Update success rate
        if total_tasks > 0:
            current_success_rate = successful_tasks / total_tasks
            # Moving average
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["success_rate"] * 0.8 +
                current_success_rate * 0.2
            )

        # Update average completion time
        self.performance_metrics["average_completion_time"] = (
            self.performance_metrics["average_completion_time"] * 0.8 +
            execution_time * 0.2
        )

        self.performance_metrics["total_tasks_orchestrated"] += total_tasks

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()

    def get_active_tasks_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self.running_tasks)

    def stop_all_tasks(self):
        """Stop all currently running tasks."""
        for task_id, async_task in self.running_tasks.items():
            if not async_task.done():
                async_task.cancel()
                _safe_print(f"[Supervisor] Cancelled task {task_id[:8]}", "yellow")

        self.running_tasks.clear()

    def register_agent(self, agent: Any, agent_type: str = "general"):
        """Register an agent with the supervisor."""
        self.agent_pool.add_agent(agent, agent_type)
        _safe_print(f"[Supervisor] Registered {agent_type} agent", "green")

    async def orchestrate_task(self, task_id: str) -> dict[str, Any]:
        """Orchestrate the execution of a complex task."""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        _safe_print(f"[Supervisor] Orchestrating task: {task.title}", "green")

        # Check if task needs decomposition
        if self._should_decompose_task(task):
            await self._decompose_and_delegate(task)
        else:
            await self._assign_to_appropriate_agent(task)

        # Monitor task execution
        return await self._monitor_task_execution(task_id)

    async def handle_long_running_task(self, task_id: str) -> None:
        """Handle a task that has been running for a long time."""
        task = self.task_manager.get_task(task_id)
        if not task:
            return

        _safe_print(f"[Supervisor] Handling long-running task: {task.title}", "yellow")

        # Assess task progress
        if task.progress < 0.1:  # Very little progress
            await self._reassess_task_strategy(task)
        elif task.progress < 0.5:  # Some progress but slow
            await self._provide_guidance(task)
        else:  # Good progress, just monitor
            await self._continue_monitoring(task)

    async def coordinate_parallel_agents(self, task_ids: list[str]) -> dict[str, Any]:
        """Coordinate multiple agents working on different tasks in parallel."""
        current_settings = settings.get_settings()
        max_parallel = current_settings.get("max_parallel_agents", 3)

        if len(task_ids) > max_parallel:
            _safe_print(f"[Supervisor] Limiting parallel tasks to {max_parallel} (requested {len(task_ids)})", "orange")
            task_ids = task_ids[:max_parallel]

        _safe_print(f"[Supervisor] Coordinating {len(task_ids)} parallel tasks", "blue")

        # Start all tasks in parallel
        coordination_tasks = []
        for task_id in task_ids:
            coordination_tasks.append(self.orchestrate_task(task_id))

        # Wait for all tasks to complete
        results = await asyncio.gather(*coordination_tasks, return_exceptions=True)

        return {
            "completed_tasks": len([r for r in results if not isinstance(r, Exception)]),
            "failed_tasks": len([r for r in results if isinstance(r, Exception)]),
            "results": results
        }

    async def implement_handoff_strategy(self, task_id: str, from_agent: str, to_agent: str, context: dict[str, Any]) -> bool:
        """Implement a task handoff between agents."""
        task = self.task_manager.get_task(task_id)
        if not task:
            return False

        _safe_print(f"[Supervisor] Implementing handoff for task {task.title}: {from_agent} -> {to_agent}", "purple")

        # Pause the task
        self.task_manager.pause_task(task_id)

        # Create handoff context
        handoff_context = {
            "previous_agent": from_agent,
            "progress": task.progress,
            "context": task.context,
            "handoff_reason": context.get("reason", "Strategic handoff"),
            "handoff_time": datetime.now(UTC).isoformat()
        }

        # Update task assignment
        task.assigned_agent = to_agent
        task.context.update(handoff_context)

        # Resume with new agent
        self.task_manager.resume_task(task_id)

        return True

    def get_global_view(self) -> dict[str, Any]:
        """Get a global view of all tasks and agent activities."""
        stats = self.task_manager.get_statistics()
        long_running = self.task_manager.get_long_running_tasks()
        active_tasks = self.task_manager.get_active_tasks()

        return {
            "statistics": stats,
            "long_running_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "duration_minutes": self._get_task_duration(task),
                    "progress": task.progress,
                    "assigned_agent": task.assigned_agent
                }
                for task in long_running
            ],
            "active_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "progress": task.progress,
                    "assigned_agent": task.assigned_agent
                }
                for task in active_tasks
            ],
            "orchestrations": len(self.active_orchestrations),
            "managed_agents": len(self.managed_agents)
        }

    async def reprompt_agent(self, task_id: str, guidance: str) -> None:
        """Reprompt an agent with additional guidance."""
        task = self.task_manager.get_task(task_id)
        if not task or not task.assigned_agent:
            return

        _safe_print(f"[Supervisor] Reprompting agent for task: {task.title}", "cyan")

        # Create guidance message
        guidance_message = {
            "message": f"""
            Task Guidance from Supervisor:
            
            Task: {task.title}
            Current Progress: {task.progress:.1%}
            
            Guidance: {guidance}
            
            Please continue with the task, taking this guidance into account.
            If you're stuck or need clarification, please ask for help.
            """
        }

        # Send guidance to the appropriate agent context
        # This would need to be integrated with the actual agent system
        self.task_manager.update_task_progress(
            task_id,
            task.progress,
            f"Supervisor provided guidance: {guidance[:50]}..."
        )

    def _should_decompose_task(self, task: Task) -> bool:
        """Determine if a task should be decomposed into subtasks."""
        current_settings = settings.get_settings()
        decomposition_enabled = current_settings.get("task_decomposition_enabled", True)

        if not decomposition_enabled:
            return False

        # Decompose if:
        # 1. Task description is very long (>500 chars)
        # 2. Task contains multiple distinct actions
        # 3. Task is estimated to take more than threshold time

        if len(task.description) > 500:
            return True

        # Check for multiple action words
        action_words = ["create", "implement", "analyze", "research", "write", "design", "test", "deploy"]
        action_count = sum(1 for word in action_words if word in task.description.lower())

        if action_count > 2:
            return True

        if task.estimated_duration and task.estimated_duration > 30:  # > 30 minutes
            return True

        return False

    async def _decompose_and_delegate(self, task: Task) -> None:
        """Decompose a task and delegate subtasks."""
        # This would use an LLM to analyze the task and break it down
        # For now, we'll create a simple example decomposition

        subtask_data = [
            {
                "title": f"Subtask 1 of {task.title}",
                "description": f"First part of: {task.description[:100]}...",
                "category": task.category.value,
                "priority": task.priority.value
            },
            {
                "title": f"Subtask 2 of {task.title}",
                "description": f"Second part of: {task.description[:100]}...",
                "category": task.category.value,
                "priority": task.priority.value
            }
        ]

        subtasks = self.task_manager.decompose_task(task.id, subtask_data)

        # Start each subtask
        for subtask in subtasks:
            await self._assign_to_appropriate_agent(subtask)

    async def _assign_to_appropriate_agent(self, task: Task) -> None:
        """Assign a task to the most appropriate agent."""
        # Determine best agent type based on task category
        agent_type = self._get_best_agent_type(task)

        # For now, we'll just start the task and assign a generic agent ID
        agent_id = f"{agent_type}_agent_{int(time.time())}"
        self.task_manager.start_task(task.id, agent_id)

    def _get_best_agent_type(self, task: Task) -> str:
        """Determine the best agent type for a task."""
        current_settings = settings.get_settings()

        if task.category.value == "coding" and current_settings.get("coding_agent_enabled", True):
            return "coding"
        elif task.category.value == "research":
            return "research"
        elif task.category.value == "analysis":
            return "analysis"
        else:
            return "utility"

    async def _monitor_task_execution(self, task_id: str) -> dict[str, Any]:
        """Monitor the execution of a task."""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        self.active_orchestrations.add(task_id)

        try:
            # Monitor until completion or timeout
            current_settings = settings.get_settings()
            timeout_minutes = current_settings.get("task_timeout_minutes", 30)
            start_time = time.time()

            while task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.PAUSED]:
                await asyncio.sleep(5)  # Check every 5 seconds

                # Check for timeout
                elapsed_minutes = (time.time() - start_time) / 60
                if elapsed_minutes > timeout_minutes:
                    await self._handle_task_timeout(task_id)
                    break

                # Check if it's become a long-running task
                if elapsed_minutes > current_settings.get("long_task_threshold_minutes", 10):
                    await self.handle_long_running_task(task_id)

                # Refresh task state
                task = self.task_manager.get_task(task_id)
                if not task:
                    break

            return {
                "status": task.status.value,
                "progress": task.progress,
                "duration_minutes": elapsed_minutes
            }

        finally:
            self.active_orchestrations.discard(task_id)

    async def _reassess_task_strategy(self, task: Task) -> None:
        """Reassess the strategy for a task with little progress."""
        _safe_print(f"[Supervisor] Reassessing strategy for task: {task.title}", "orange")

        # Check if task should be decomposed
        if not task.subtask_ids and self._should_decompose_task(task):
            await self._decompose_and_delegate(task)
        else:
            # Try different agent assignment
            current_agent = task.assigned_agent
            new_agent_type = "utility" if "coding" in current_agent else "coding"
            new_agent_id = f"{new_agent_type}_agent_{int(time.time())}"

            await self.implement_handoff_strategy(
                task.id,
                current_agent,
                new_agent_id,
                {"reason": "Strategy reassessment due to slow progress"}
            )

    async def _provide_guidance(self, task: Task) -> None:
        """Provide guidance to an agent working on a task."""
        guidance = f"""
        Task has been running for a while with {task.progress:.1%} progress.
        Please review your approach and consider:
        1. Breaking down remaining work into smaller steps
        2. Asking for clarification if requirements are unclear
        3. Using different tools or methods if current approach isn't working
        """
        await self.reprompt_agent(task.id, guidance)

    async def _continue_monitoring(self, task: Task) -> None:
        """Continue monitoring a task that's making good progress."""
        self.task_manager.update_task_progress(
            task.id,
            task.progress,
            "Supervisor: Good progress, continuing monitoring"
        )

    async def _handle_task_timeout(self, task_id: str) -> None:
        """Handle a task that has exceeded its timeout."""
        _safe_print(f"[Supervisor] Task timeout exceeded: {task_id}", "red")

        task = self.task_manager.get_task(task_id)
        if task:
            self.task_manager.fail_task(
                task_id,
                f"Task exceeded timeout of {settings.get_settings().get('task_timeout_minutes', 30)} minutes"
            )

    def _get_task_duration(self, task: Task) -> float:
        """Get the current duration of a task in minutes."""
        if not task.started_at:
            return 0.0

        current_time = datetime.now(UTC)
        duration = (current_time - task.started_at).total_seconds() / 60
        return round(duration, 1)


# Global supervisor agent instance
_supervisor_instance: SupervisorAgent | None = None


def get_supervisor_agent(config: dict[str, Any] | None = None) -> SupervisorAgent:
    """Get the global supervisor agent instance."""
    global _supervisor_instance
    if _supervisor_instance is None:
        # Initialize with default config if none provided
        if config is None:
            try:
                from framework.helpers import settings
                current_settings = settings.get_settings()
                config = {
                    "monitoring_interval": current_settings.get("supervisor_monitoring_interval", 30),
                    "max_retries": current_settings.get("supervisor_max_retries", 3),
                    "enable_handoffs": current_settings.get("supervisor_enable_handoffs", True),
                    "enable_parallel_execution": current_settings.get("supervisor_enable_parallel", False)
                }
            except Exception:
                # Fallback to minimal default config
                config = {
                    "monitoring_interval": 30,
                    "max_retries": 3,
                    "enable_handoffs": True,
                    "enable_parallel_execution": False
                }
        _supervisor_instance = SupervisorAgent(config)
    return _supervisor_instance


def initialize_supervisor_agent(config: dict[str, Any]) -> SupervisorAgent:
    """Initialize the supervisor agent with configuration."""
    global _supervisor_instance
    _supervisor_instance = SupervisorAgent(config)
    return _supervisor_instance
