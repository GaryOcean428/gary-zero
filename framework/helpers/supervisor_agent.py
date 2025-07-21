"""Supervisor agent for orchestrating tasks and managing long-running processes.

This module provides coordination and oversight capabilities for complex
multi-agent workflows and long-running tasks.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from framework.helpers import settings
from framework.helpers.task_manager import TaskManager, Task, TaskStatus, TaskPriority


def _safe_print(message: str, color: str = "default") -> None:
    """Safe print function that falls back to regular print if PrintStyle unavailable."""
    try:
        from framework.helpers.print_style import PrintStyle
        _safe_print(message)
    except ImportError:
        print(f"[{color.upper()}] {message}")


class SupervisorAgent:
    """Supervisor agent for orchestrating multiple agents and managing tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.task_manager = TaskManager.get_instance()
        self.managed_agents: Dict[str, Any] = {}  # Changed from Agent to Any
        self.active_orchestrations: Set[str] = set()
        self.handoff_strategies: Dict[str, Any] = {}
        
    async def orchestrate_task(self, task_id: str) -> Dict[str, Any]:
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
    
    async def coordinate_parallel_agents(self, task_ids: List[str]) -> Dict[str, Any]:
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
    
    async def implement_handoff_strategy(self, task_id: str, from_agent: str, to_agent: str, context: Dict[str, Any]) -> bool:
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
            "handoff_time": datetime.now(timezone.utc).isoformat()
        }
        
        # Update task assignment
        task.assigned_agent = to_agent
        task.context.update(handoff_context)
        
        # Resume with new agent
        self.task_manager.resume_task(task_id)
        
        return True
    
    def get_global_view(self) -> Dict[str, Any]:
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
    
    async def _monitor_task_execution(self, task_id: str) -> Dict[str, Any]:
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
        
        current_time = datetime.now(timezone.utc)
        duration = (current_time - task.started_at).total_seconds() / 60
        return round(duration, 1)


# Global supervisor agent instance
_supervisor_instance: Optional[SupervisorAgent] = None


def get_supervisor_agent(config: Optional[Dict[str, Any]] = None) -> SupervisorAgent:
    """Get the global supervisor agent instance."""
    global _supervisor_instance
    if _supervisor_instance is None and config:
        _supervisor_instance = SupervisorAgent(config)
    return _supervisor_instance


def initialize_supervisor_agent(config: Dict[str, Any]) -> SupervisorAgent:
    """Initialize the supervisor agent with configuration."""
    global _supervisor_instance
    _supervisor_instance = SupervisorAgent(config)
    return _supervisor_instance