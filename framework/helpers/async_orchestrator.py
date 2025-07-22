"""
Asynchronous Task Orchestration System

Provides async event-driven orchestration with dependency management, 
concurrency controls, and adaptive scheduling capabilities.
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import weakref

from framework.performance.monitor import get_performance_monitor
from framework.performance.async_utils import BackgroundTaskManager, TaskStatus as AsyncTaskStatus
from framework.helpers.task_manager import TaskManager, TaskStatus, TaskCategory, Task as ManagedTask

logger = logging.getLogger(__name__)


class OrchestrationStatus(Enum):
    """Orchestration-specific task status."""
    PENDING = "pending"
    WAITING_DEPENDENCIES = "waiting_dependencies"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""
    dependent_task_id: str
    dependency_task_id: str
    dependency_type: str = "completion"  # completion, data, resource
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentResource:
    """Resource allocation tracking for agents."""
    agent_id: str
    max_concurrent_tasks: int = 3
    current_task_count: int = 0
    max_requests_per_minute: int = 60
    current_requests: deque = field(default_factory=deque)
    reserved_memory_mb: float = 0.0
    max_memory_mb: float = 1024.0


@dataclass 
class OrchestrationTask:
    """Enhanced task with orchestration metadata."""
    id: str
    managed_task: ManagedTask
    status: OrchestrationStatus = OrchestrationStatus.PENDING
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    priority: int = 0
    timeout_seconds: Optional[float] = None
    assigned_agent: Optional[str] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 2
    
    # Async execution context
    async_task: Optional[asyncio.Task] = None
    future: Optional[asyncio.Future] = None


class AsyncTaskOrchestrator:
    """
    Main orchestration engine for async task management with dependency resolution,
    concurrency controls, and adaptive scheduling.
    """
    
    def __init__(self, 
                 max_concurrent_tasks: int = 10,
                 default_task_timeout: float = 300.0,
                 enable_performance_monitoring: bool = True):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_task_timeout = default_task_timeout
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Core orchestration state
        self.tasks: Dict[str, OrchestrationTask] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Execution state
        self.ready_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, OrchestrationTask] = {}
        self.completed_tasks: Dict[str, OrchestrationTask] = {}
        self.failed_tasks: Dict[str, OrchestrationTask] = {}
        
        # Agent resource management
        self.agent_resources: Dict[str, AgentResource] = {}
        self.default_agent_limits = {
            'max_concurrent_tasks': 3,
            'max_requests_per_minute': 60,
            'max_memory_mb': 1024.0
        }
        
        # Concurrency control
        self.orchestration_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.task_lock = asyncio.Lock()
        
        # Integration components
        self.task_manager = TaskManager.get_instance()
        self.performance_monitor = get_performance_monitor() if enable_performance_monitoring else None
        self.background_manager = BackgroundTaskManager(max_concurrent=max_concurrent_tasks)
        
        # Orchestration control
        self.is_running = False
        self.orchestration_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'dependency_cycles_detected': 0,
            'timeout_violations': 0,
            'resource_constraints_hit': 0
        }
        
        logger.info("AsyncTaskOrchestrator initialized")
    
    async def start(self):
        """Start the orchestration engine."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start performance monitoring if enabled
        if self.performance_monitor:
            await self.performance_monitor.start()
        
        # Start main orchestration loop
        self.orchestration_task = asyncio.create_task(self._orchestration_loop())
        
        logger.info("AsyncTaskOrchestrator started")
    
    async def stop(self):
        """Stop the orchestration engine gracefully."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Cancel orchestration task
        if self.orchestration_task:
            self.orchestration_task.cancel()
            try:
                await self.orchestration_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        await self._cancel_all_running_tasks()
        
        # Shutdown background manager
        await self.background_manager.shutdown()
        
        # Stop performance monitoring
        if self.performance_monitor:
            await self.performance_monitor.stop()
        
        logger.info("AsyncTaskOrchestrator stopped")
    
    async def submit_task(self, 
                         task: ManagedTask,
                         dependencies: Optional[List[str]] = None,
                         priority: int = 0,
                         timeout_seconds: Optional[float] = None,
                         assigned_agent: Optional[str] = None) -> str:
        """
        Submit a task for orchestrated execution.
        
        Args:
            task: The managed task to execute
            dependencies: List of task IDs this task depends on
            priority: Task priority (higher = more important)
            timeout_seconds: Task timeout override
            assigned_agent: Specific agent to assign to
            
        Returns:
            Task ID for tracking
        """
        async with self.task_lock:
            # Create orchestration task
            orchestration_task = OrchestrationTask(
                id=task.id,
                managed_task=task,
                priority=priority,
                timeout_seconds=timeout_seconds or self.default_task_timeout,
                assigned_agent=assigned_agent,
                dependencies=set(dependencies or []),
                future=asyncio.Future()
            )
            
            # Add to orchestration state
            self.tasks[task.id] = orchestration_task
            
            # Build dependency graph
            if dependencies:
                await self._add_dependencies(task.id, dependencies)
            
            # Update metrics
            self.metrics['tasks_submitted'] += 1
            
            # Check if task is ready to run
            if await self._is_task_ready(task.id):
                orchestration_task.status = OrchestrationStatus.READY
                await self.ready_queue.put(orchestration_task)
            else:
                orchestration_task.status = OrchestrationStatus.WAITING_DEPENDENCIES
            
            logger.info(f"Task {task.id} submitted with {len(dependencies or [])} dependencies")
            
            return task.id
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a specific task to complete and return its result."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        orchestration_task = self.tasks[task_id]
        
        try:
            result = await asyncio.wait_for(orchestration_task.future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task {task_id}")
            raise
        except Exception as e:
            logger.error(f"Error waiting for task {task_id}: {e}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task."""
        async with self.task_lock:
            if task_id not in self.tasks:
                return False
            
            orchestration_task = self.tasks[task_id]
            
            # Cancel async task if running
            if orchestration_task.async_task:
                orchestration_task.async_task.cancel()
            
            # Update status
            orchestration_task.status = OrchestrationStatus.CANCELLED
            
            # Complete future with cancellation
            if not orchestration_task.future.done():
                orchestration_task.future.cancel()
            
            # Remove from running tasks
            self.running_tasks.pop(task_id, None)
            
            # Update dependents
            await self._handle_task_completion(task_id, cancelled=True)
            
            logger.info(f"Task {task_id} cancelled")
            return True
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a task."""
        if task_id not in self.tasks:
            return None
        
        orchestration_task = self.tasks[task_id]
        
        return {
            'id': task_id,
            'status': orchestration_task.status.value,
            'priority': orchestration_task.priority,
            'dependencies': list(orchestration_task.dependencies),
            'dependents': list(orchestration_task.dependents),
            'assigned_agent': orchestration_task.assigned_agent,
            'start_time': orchestration_task.start_time,
            'completion_time': orchestration_task.completion_time,
            'retry_count': orchestration_task.retry_count,
            'has_error': orchestration_task.error is not None,
            'timeout_seconds': orchestration_task.timeout_seconds
        }
    
    async def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration metrics."""
        async with self.task_lock:
            # Basic counts
            total_tasks = len(self.tasks)
            running_count = len(self.running_tasks)
            completed_count = len(self.completed_tasks)
            failed_count = len(self.failed_tasks)
            
            # Status distribution
            status_counts = defaultdict(int)
            for task in self.tasks.values():
                status_counts[task.status.value] += 1
            
            # Agent utilization
            agent_utilization = {}
            for agent_id, resource in self.agent_resources.items():
                agent_utilization[agent_id] = {
                    'current_tasks': resource.current_task_count,
                    'max_tasks': resource.max_concurrent_tasks,
                    'utilization_percent': (resource.current_task_count / resource.max_concurrent_tasks) * 100,
                    'memory_usage_mb': resource.reserved_memory_mb,
                    'recent_requests': len([
                        req for req in resource.current_requests 
                        if time.time() - req < 60
                    ])
                }
            
            # Performance data
            performance_summary = {}
            if self.performance_monitor:
                performance_summary = self.performance_monitor.get_performance_summary(300)  # Last 5 minutes
            
            return {
                'total_tasks': total_tasks,
                'running_tasks': running_count,
                'completed_tasks': completed_count,
                'failed_tasks': failed_count,
                'ready_queue_size': self.ready_queue.qsize(),
                'status_distribution': dict(status_counts),
                'agent_utilization': agent_utilization,
                'performance': performance_summary,
                'orchestration_metrics': self.metrics.copy(),
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'is_running': self.is_running
            }
    
    # Private implementation methods
    
    async def _orchestration_loop(self):
        """Main orchestration loop - processes ready tasks."""
        logger.info("Orchestration loop started")
        
        while self.is_running:
            try:
                # Process ready tasks
                await self._process_ready_tasks()
                
                # Check for dependency resolution
                await self._check_dependency_resolution()
                
                # Monitor resource usage and adjust if needed
                if self.performance_monitor:
                    await self._adaptive_scheduling_check()
                
                # Brief pause to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(1)  # Prevent rapid error loops
        
        logger.info("Orchestration loop stopped")
    
    async def _process_ready_tasks(self):
        """Process tasks that are ready to run."""
        try:
            # Get ready task with timeout to avoid blocking
            orchestration_task = await asyncio.wait_for(
                self.ready_queue.get(), 
                timeout=0.1
            )
            
            # Check resource availability
            if await self._can_start_task(orchestration_task):
                await self._start_task_execution(orchestration_task)
            else:
                # Put back in queue for later
                await self.ready_queue.put(orchestration_task)
                
        except asyncio.TimeoutError:
            # No ready tasks - this is normal
            pass
        except Exception as e:
            logger.error(f"Error processing ready tasks: {e}")
    
    async def _can_start_task(self, orchestration_task: OrchestrationTask) -> bool:
        """Check if a task can start based on resource constraints."""
        # Check global concurrency limit
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return False
        
        # Check agent-specific limits
        if orchestration_task.assigned_agent:
            agent_resource = await self._get_agent_resource(orchestration_task.assigned_agent)
            
            # Check concurrent task limit
            if agent_resource.current_task_count >= agent_resource.max_concurrent_tasks:
                self.metrics['resource_constraints_hit'] += 1
                return False
            
            # Check request rate limit (last minute)
            current_time = time.time()
            recent_requests = [
                req for req in agent_resource.current_requests 
                if current_time - req < 60
            ]
            
            if len(recent_requests) >= agent_resource.max_requests_per_minute:
                self.metrics['resource_constraints_hit'] += 1
                return False
        
        return True
    
    async def _start_task_execution(self, orchestration_task: OrchestrationTask):
        """Start executing a ready task."""
        task_id = orchestration_task.id
        
        async with self.task_lock:
            # Update status
            orchestration_task.status = OrchestrationStatus.RUNNING
            orchestration_task.start_time = datetime.now(timezone.utc)
            
            # Move to running tasks
            self.running_tasks[task_id] = orchestration_task
            
            # Update agent resource usage
            if orchestration_task.assigned_agent:
                agent_resource = await self._get_agent_resource(orchestration_task.assigned_agent)
                agent_resource.current_task_count += 1
                agent_resource.current_requests.append(time.time())
                
                # Trim old requests
                current_time = time.time()
                agent_resource.current_requests = deque([
                    req for req in agent_resource.current_requests 
                    if current_time - req < 60
                ])
        
        # Start task execution
        try:
            orchestration_task.async_task = asyncio.create_task(
                self._execute_task_with_timeout(orchestration_task)
            )
            
            logger.info(f"Started execution of task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to start task {task_id}: {e}")
            await self._handle_task_failure(orchestration_task, e)
    
    async def _execute_task_with_timeout(self, orchestration_task: OrchestrationTask):
        """Execute a task with timeout handling."""
        task_id = orchestration_task.id
        
        try:
            # Create task execution coroutine
            execution_coro = self._execute_managed_task(orchestration_task.managed_task)
            
            # Execute with timeout
            if orchestration_task.timeout_seconds:
                result = await asyncio.wait_for(
                    execution_coro, 
                    timeout=orchestration_task.timeout_seconds
                )
            else:
                result = await execution_coro
            
            # Handle successful completion
            await self._handle_task_success(orchestration_task, result)
            
        except asyncio.TimeoutError:
            logger.warning(f"Task {task_id} timed out after {orchestration_task.timeout_seconds}s")
            orchestration_task.status = OrchestrationStatus.TIMEOUT
            self.metrics['timeout_violations'] += 1
            await self._handle_task_failure(orchestration_task, TimeoutError("Task execution timeout"))
            
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            orchestration_task.status = OrchestrationStatus.CANCELLED
            await self._cleanup_task_execution(orchestration_task)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed with error: {e}")
            await self._handle_task_failure(orchestration_task, e)
    
    async def _execute_managed_task(self, managed_task: ManagedTask) -> Any:
        """Execute the actual managed task - placeholder for real implementation."""
        # This would integrate with the actual task execution system
        # For now, simulate work
        await asyncio.sleep(0.1)  # Simulate task execution
        return f"Result for task {managed_task.id}"
    
    async def _handle_task_success(self, orchestration_task: OrchestrationTask, result: Any):
        """Handle successful task completion."""
        task_id = orchestration_task.id
        
        async with self.task_lock:
            # Update task state
            orchestration_task.status = OrchestrationStatus.COMPLETED
            orchestration_task.completion_time = datetime.now(timezone.utc)
            orchestration_task.result = result
            
            # Complete future
            if not orchestration_task.future.done():
                orchestration_task.future.set_result(result)
            
            # Move to completed tasks
            self.running_tasks.pop(task_id, None)
            self.completed_tasks[task_id] = orchestration_task
            
            # Update managed task
            orchestration_task.managed_task.status = TaskStatus.COMPLETED
            orchestration_task.managed_task.progress = 1.0
            
            # Update metrics
            self.metrics['tasks_completed'] += 1
            
            # Cleanup resources
            await self._cleanup_task_execution(orchestration_task)
        
        # Handle dependent tasks
        await self._handle_task_completion(task_id)
        
        logger.info(f"Task {task_id} completed successfully")
    
    async def _handle_task_failure(self, orchestration_task: OrchestrationTask, error: Exception):
        """Handle task failure with retry logic."""
        task_id = orchestration_task.id
        
        async with self.task_lock:
            orchestration_task.error = error
            orchestration_task.retry_count += 1
            
            # Check if we should retry
            if orchestration_task.retry_count <= orchestration_task.max_retries:
                logger.info(f"Retrying task {task_id} (attempt {orchestration_task.retry_count})")
                
                # Reset for retry
                orchestration_task.status = OrchestrationStatus.READY
                orchestration_task.start_time = None
                orchestration_task.async_task = None
                
                # Put back in ready queue
                await self.ready_queue.put(orchestration_task)
                
                # Move out of running tasks
                self.running_tasks.pop(task_id, None)
                
            else:
                # Final failure
                orchestration_task.status = OrchestrationStatus.FAILED
                orchestration_task.completion_time = datetime.now(timezone.utc)
                
                # Complete future with error
                if not orchestration_task.future.done():
                    orchestration_task.future.set_exception(error)
                
                # Move to failed tasks
                self.running_tasks.pop(task_id, None)
                self.failed_tasks[task_id] = orchestration_task
                
                # Update managed task
                orchestration_task.managed_task.status = TaskStatus.FAILED
                
                # Update metrics
                self.metrics['tasks_failed'] += 1
                
                logger.error(f"Task {task_id} failed permanently after {orchestration_task.retry_count} attempts")
                
                # Handle dependent tasks (they may need to be cancelled)
                await self._handle_task_completion(task_id, failed=True)
            
            # Cleanup resources
            await self._cleanup_task_execution(orchestration_task)
    
    async def _cleanup_task_execution(self, orchestration_task: OrchestrationTask):
        """Clean up resources after task execution."""
        # Update agent resource usage
        if orchestration_task.assigned_agent:
            agent_resource = await self._get_agent_resource(orchestration_task.assigned_agent)
            agent_resource.current_task_count = max(0, agent_resource.current_task_count - 1)
    
    async def _handle_task_completion(self, task_id: str, failed: bool = False, cancelled: bool = False):
        """Handle task completion and check dependent tasks."""
        dependents = self.reverse_dependency_graph.get(task_id, set())
        
        for dependent_id in dependents:
            if dependent_id in self.tasks:
                dependent_task = self.tasks[dependent_id]
                
                if failed or cancelled:
                    # Cancel dependent tasks if dependency failed/cancelled
                    await self.cancel_task(dependent_id)
                else:
                    # Check if dependent task is now ready
                    if await self._is_task_ready(dependent_id):
                        dependent_task.status = OrchestrationStatus.READY
                        await self.ready_queue.put(dependent_task)
    
    async def _is_task_ready(self, task_id: str) -> bool:
        """Check if a task is ready to run (all dependencies completed)."""
        if task_id not in self.tasks:
            return False
        
        orchestration_task = self.tasks[task_id]
        
        # Check if already running/completed
        if orchestration_task.status not in (OrchestrationStatus.PENDING, OrchestrationStatus.WAITING_DEPENDENCIES):
            return False
        
        # Check all dependencies
        for dep_id in orchestration_task.dependencies:
            # If dependency hasn't been submitted yet, task is not ready
            if dep_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep_id]
            # Dependency must be completed for task to be ready
            if dep_task.status != OrchestrationStatus.COMPLETED:
                return False
        
        return True
    
    async def _add_dependencies(self, task_id: str, dependencies: List[str]):
        """Add dependencies to the task graph."""
        # Check for cycles
        if await self._would_create_cycle(task_id, dependencies):
            self.metrics['dependency_cycles_detected'] += 1
            raise ValueError(f"Adding dependencies would create a cycle for task {task_id}")
        
        # Add to dependency graphs
        for dep_id in dependencies:
            self.dependency_graph[task_id].add(dep_id)
            self.reverse_dependency_graph[dep_id].add(task_id)
            
            # Update dependent references
            if dep_id in self.tasks:
                self.tasks[dep_id].dependents.add(task_id)
    
    async def _would_create_cycle(self, task_id: str, dependencies: List[str]) -> bool:
        """Check if adding dependencies would create a cycle using DFS."""
        # Build temporary graph
        temp_graph = defaultdict(set)
        for tid, deps in self.dependency_graph.items():
            temp_graph[tid] = deps.copy()
        
        # Add new dependencies
        for dep_id in dependencies:
            temp_graph[task_id].add(dep_id)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True  # Cycle detected
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in temp_graph.get(node, set()):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes for cycles
        for node in temp_graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    async def _check_dependency_resolution(self):
        """Check for tasks that may have become ready due to dependency completion."""
        async with self.task_lock:
            for task_id, orchestration_task in self.tasks.items():
                if orchestration_task.status == OrchestrationStatus.WAITING_DEPENDENCIES:
                    if await self._is_task_ready(task_id):
                        orchestration_task.status = OrchestrationStatus.READY
                        await self.ready_queue.put(orchestration_task)
    
    async def _adaptive_scheduling_check(self):
        """Check performance metrics and adjust scheduling behavior."""
        if not self.performance_monitor:
            return
        
        # Get recent performance data
        performance_summary = self.performance_monitor.get_performance_summary(60)  # Last minute
        
        resource_usage = performance_summary.get('resource_usage', {})
        current_usage = resource_usage.get('current', {})
        
        cpu_percent = current_usage.get('cpu_percent', 0)
        memory_percent = current_usage.get('memory_percent', 0)
        
        # Adjust concurrency based on resource usage
        if cpu_percent > 80 or memory_percent > 80:
            # Reduce concurrency under high load
            new_limit = max(1, int(self.max_concurrent_tasks * 0.7))
            if new_limit != self.max_concurrent_tasks:
                logger.info(f"Reducing concurrency limit to {new_limit} due to high resource usage")
                # Note: We can't easily change semaphore size, so we'll track this separately
                
        elif cpu_percent < 50 and memory_percent < 50:
            # Can potentially increase concurrency under light load
            # This would require more sophisticated logic and configuration
            pass
    
    async def _get_agent_resource(self, agent_id: str) -> AgentResource:
        """Get or create agent resource tracking."""
        if agent_id not in self.agent_resources:
            self.agent_resources[agent_id] = AgentResource(
                agent_id=agent_id,
                **self.default_agent_limits
            )
        return self.agent_resources[agent_id]
    
    async def _cancel_all_running_tasks(self):
        """Cancel all currently running tasks."""
        tasks_to_cancel = list(self.running_tasks.keys())
        
        for task_id in tasks_to_cancel:
            await self.cancel_task(task_id)


# Global orchestrator instance
_global_orchestrator: Optional[AsyncTaskOrchestrator] = None

async def get_orchestrator(
    max_concurrent_tasks: int = 10,
    default_task_timeout: float = 300.0,
    enable_performance_monitoring: bool = True
) -> AsyncTaskOrchestrator:
    """Get or create the global orchestrator instance."""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = AsyncTaskOrchestrator(
            max_concurrent_tasks=max_concurrent_tasks,
            default_task_timeout=default_task_timeout,
            enable_performance_monitoring=enable_performance_monitoring
        )
        await _global_orchestrator.start()
    
    return _global_orchestrator

async def shutdown_orchestrator():
    """Shutdown the global orchestrator instance."""
    global _global_orchestrator
    
    if _global_orchestrator:
        await _global_orchestrator.stop()
        _global_orchestrator = None