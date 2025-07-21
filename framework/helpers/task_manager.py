"""Task management system for Gary-Zero.

This module provides task tracking, decomposition, categorization, and orchestration
capabilities for managing complex, long-running tasks.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from framework.helpers import settings


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCategory(Enum):
    """Task category types."""
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    SYSTEM = "system"
    CREATIVE = "creative"
    OTHER = "other"


@dataclass
class Task:
    """Individual task representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.OTHER
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_id: Optional[str] = None
    subtask_ids: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    assigned_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    estimated_duration: Optional[int] = None  # in minutes
    actual_duration: Optional[int] = None  # in minutes


@dataclass
class TaskUpdate:
    """Task update event."""
    task_id: str
    timestamp: datetime
    status: TaskStatus
    progress: float
    message: str
    agent_id: Optional[str] = None


class TaskManager:
    """Central task management system."""
    
    _instance: Optional['TaskManager'] = None
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_updates: List[TaskUpdate] = []
        self.active_tasks: Set[str] = set()
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
        # Enable database persistence
        self.persistence_enabled = True
        self._db: Optional[Any] = None
        
        # Load existing tasks from database
        self._load_from_database()
    
    @property
    def database(self):
        """Get the task database instance."""
        if self._db is None:
            try:
                from framework.helpers.task_persistence import get_task_database
                self._db = get_task_database()
            except ImportError:
                self.persistence_enabled = False
                print("Warning: Task persistence not available")
        return self._db
    
    def _load_from_database(self):
        """Load existing tasks from database."""
        if not self.persistence_enabled:
            return
        
        try:
            db = self.database
            if db:
                tasks = db.load_all_tasks()
                for task in tasks:
                    # Convert from persistence Task to current Task format
                    current_task = Task(
                        id=task.id,
                        title=task.title,
                        description=task.description,
                        status=TaskStatus(task.status.value),
                        category=TaskCategory(task.category.value) if task.category else TaskCategory.OTHER,
                        created_at=task.created_at or datetime.now(timezone.utc),
                        started_at=task.started_at,
                        completed_at=task.completed_at,
                        assigned_agent=task.agent_id,
                        context=task.metadata or {},
                        progress=task.progress
                    )
                    
                    self.tasks[current_task.id] = current_task
                    
                    # Organize tasks by status
                    if current_task.status == TaskStatus.IN_PROGRESS:
                        self.active_tasks.add(current_task.id)
                    elif current_task.status == TaskStatus.COMPLETED:
                        self.completed_tasks.add(current_task.id)
                    elif current_task.status == TaskStatus.FAILED:
                        self.failed_tasks.add(current_task.id)
                
                print(f"Loaded {len(tasks)} tasks from database")
        except Exception as e:
            print(f"Error loading tasks from database: {e}")
    
    def _save_to_database(self, task: Task):
        """Save a task to database."""
        if not self.persistence_enabled:
            return
        
        try:
            db = self.database
            if db:
                # Convert from current Task to persistence Task format
                from framework.helpers.task_persistence import Task as PersistenceTask, TaskStatus as PersistenceTaskStatus, TaskCategory as PersistenceTaskCategory
                
                persistence_task = PersistenceTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    category=PersistenceTaskCategory(task.category.value),
                    status=PersistenceTaskStatus(task.status.value),
                    priority=task.priority.value if hasattr(task.priority, 'value') else 1,
                    progress=task.progress,
                    created_at=task.created_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    context_id=task.context.get('context_id'),
                    agent_id=task.assigned_agent,
                    parent_id=task.parent_id,
                    subtask_ids=list(task.subtask_ids),
                    metadata=task.context
                )
                
                db.save_task(persistence_task)
        except Exception as e:
            print(f"Error saving task to database: {e}")
    
    def _save_update_to_database(self, update: TaskUpdate):
        """Save a task update to database."""
        if not self.persistence_enabled:
            return
        
        try:
            db = self.database
            if db:
                db.save_task_update(update)
        except Exception as e:
            print(f"Error saving task update to database: {e}")
        
    @classmethod
    def get_instance(cls) -> 'TaskManager':
        """Get the singleton task manager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        category: TaskCategory = TaskCategory.OTHER,
        parent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            parent_id=parent_id,
            context=context or {}
        )
        
        self.tasks[task.id] = task
        
        # Add to parent's subtasks if applicable
        if parent_id and parent_id in self.tasks:
            self.tasks[parent_id].subtask_ids.add(task.id)
        
        # Save to database
        self._save_to_database(task)
        
        self._log_task_event(task.id, "Task created", TaskStatus.PENDING)
        return task
    
    def decompose_task(self, task_id: str, subtasks: List[Dict[str, Any]]) -> List[Task]:
        """Decompose a task into subtasks."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        created_subtasks = []
        for subtask_data in subtasks:
            subtask = self.create_task(
                title=subtask_data.get("title", ""),
                description=subtask_data.get("description", ""),
                priority=TaskPriority(subtask_data.get("priority", TaskPriority.MEDIUM.value)),
                category=TaskCategory(subtask_data.get("category", TaskCategory.OTHER.value)),
                parent_id=task_id,
                context=subtask_data.get("context", {})
            )
            created_subtasks.append(subtask)
        
        self._log_task_event(task_id, f"Task decomposed into {len(created_subtasks)} subtasks", self.tasks[task_id].status)
        return created_subtasks
    
    def start_task(self, task_id: str, agent_id: Optional[str] = None) -> None:
        """Start a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        task.assigned_agent = agent_id
        task.updated_at = datetime.now(timezone.utc)
        
        self.active_tasks.add(task_id)
        
        # Save to database
        self._save_to_database(task)
        
        self._log_task_event(task_id, "Task started", TaskStatus.IN_PROGRESS, agent_id)
    
    def update_task_progress(self, task_id: str, progress: float, message: str = "") -> None:
        """Update task progress."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.progress = max(0.0, min(1.0, progress))
        task.updated_at = datetime.now(timezone.utc)
        
        # Save to database
        self._save_to_database(task)
        
        self._log_task_event(task_id, message or f"Progress updated to {progress:.1%}", task.status)
    
    def complete_task(self, task_id: str, result: Optional[str] = None) -> None:
        """Complete a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.progress = 1.0
        task.updated_at = datetime.now(timezone.utc)
        
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds() / 60
            task.actual_duration = int(duration)
        
        if result:
            task.context["result"] = result
        
        self.active_tasks.discard(task_id)
        self.completed_tasks.add(task_id)
        
        # Save to database
        self._save_to_database(task)
        
        self._log_task_event(task_id, "Task completed", TaskStatus.COMPLETED)
        
        # Check if parent task should be completed
        if task.parent_id:
            self._check_parent_completion(task.parent_id)
    
    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.updated_at = datetime.now(timezone.utc)
        task.context["error"] = error
        
        self.active_tasks.discard(task_id)
        self.failed_tasks.add(task_id)
        
        # Save to database
        self._save_to_database(task)
        
        self._log_task_event(task_id, f"Task failed: {error}", TaskStatus.FAILED)
    
    def pause_task(self, task_id: str) -> None:
        """Pause a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.PAUSED
        task.updated_at = datetime.now(timezone.utc)
        
        self.active_tasks.discard(task_id)
        self._log_task_event(task_id, "Task paused", TaskStatus.PAUSED)
    
    def resume_task(self, task_id: str) -> None:
        """Resume a paused task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now(timezone.utc)
            self.active_tasks.add(task_id)
            self._log_task_event(task_id, "Task resumed", TaskStatus.IN_PROGRESS)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_tasks_by_category(self, category: TaskCategory) -> List[Task]:
        """Get all tasks in a specific category."""
        return [task for task in self.tasks.values() if task.category == category]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_active_tasks(self) -> List[Task]:
        """Get all currently active tasks."""
        return [self.tasks[task_id] for task_id in self.active_tasks if task_id in self.tasks]
    
    def get_long_running_tasks(self) -> List[Task]:
        """Get tasks that have been running longer than the threshold."""
        current_settings = settings.get_settings()
        threshold_minutes = current_settings.get("long_task_threshold_minutes", 10)
        current_time = datetime.now(timezone.utc)
        
        long_running = []
        for task in self.get_active_tasks():
            if task.started_at:
                duration = (current_time - task.started_at).total_seconds() / 60
                if duration > threshold_minutes:
                    long_running.append(task)
        
        return long_running
    
    def categorize_task(self, task_id: str, description: str) -> TaskCategory:
        """Automatically categorize a task based on its description."""
        # Simple keyword-based categorization
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["code", "debug", "implement", "function", "class", "program"]):
            return TaskCategory.CODING
        elif any(keyword in description_lower for keyword in ["research", "investigate", "find", "search", "study"]):
            return TaskCategory.RESEARCH
        elif any(keyword in description_lower for keyword in ["analyze", "review", "examine", "evaluate"]):
            return TaskCategory.ANALYSIS
        elif any(keyword in description_lower for keyword in ["write", "create", "design", "generate"]):
            return TaskCategory.CREATIVE
        elif any(keyword in description_lower for keyword in ["system", "configure", "setup", "install"]):
            return TaskCategory.SYSTEM
        else:
            return TaskCategory.OTHER
    
    def _check_parent_completion(self, parent_id: str) -> None:
        """Check if a parent task should be completed based on subtask status."""
        if parent_id not in self.tasks:
            return
        
        parent_task = self.tasks[parent_id]
        subtasks = [self.tasks[sid] for sid in parent_task.subtask_ids if sid in self.tasks]
        
        if not subtasks:
            return
        
        # Check if all subtasks are completed
        all_completed = all(subtask.status == TaskStatus.COMPLETED for subtask in subtasks)
        if all_completed and parent_task.status != TaskStatus.COMPLETED:
            self.complete_task(parent_id, "All subtasks completed")
    
    def _log_task_event(self, task_id: str, message: str, status: TaskStatus, agent_id: Optional[str] = None) -> None:
        """Log a task event."""
        update = TaskUpdate(
            task_id=task_id,
            timestamp=datetime.now(timezone.utc),
            status=status,
            progress=self.tasks[task_id].progress if task_id in self.tasks else 0.0,
            message=message,
            agent_id=agent_id
        )
        self.task_updates.append(update)
        
        # Save update to database
        self._save_update_to_database(update)
        
        # Print to console for debugging (lazy import to avoid circular dependencies)
        try:
            from framework.helpers.print_style import PrintStyle
            PrintStyle(font_color="cyan", padding=True).print(f"[TaskManager] {message} (Task: {task_id[:8]})")
        except ImportError:
            print(f"[TaskManager] {message} (Task: {task_id[:8]})")
    
    def get_task_hierarchy(self, task_id: str) -> Dict[str, Any]:
        """Get the complete hierarchy for a task."""
        if task_id not in self.tasks:
            return {}
        
        task = self.tasks[task_id]
        result = {
            "task": task,
            "subtasks": []
        }
        
        for subtask_id in task.subtask_ids:
            if subtask_id in self.tasks:
                result["subtasks"].append(self.get_task_hierarchy(subtask_id))
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task management statistics."""
        total_tasks = len(self.tasks)
        active_tasks = len(self.active_tasks)
        completed_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        
        # Category distribution
        category_counts = {}
        for category in TaskCategory:
            category_counts[category.value] = len(self.get_tasks_by_category(category))
        
        # Status distribution
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(self.get_tasks_by_status(status))
        
        return {
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "category_distribution": category_counts,
            "status_distribution": status_counts,
            "long_running_tasks": len(self.get_long_running_tasks())
        }


# Global task manager instance
def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    return TaskManager.get_instance()