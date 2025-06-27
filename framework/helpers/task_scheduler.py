"""Task scheduler for managing and executing scheduled, ad-hoc, and planned tasks."""

# Re-export all components from the modular structure for backward compatibility
from framework.helpers.task_management import (
    SCHEDULER_FOLDER,
    SchedulerTaskList,
    TaskScheduler,
)
from framework.helpers.task_models import (
    AdHocTask,
    BaseTask,
    PlannedTask,
    ScheduledTask,
    Task,
    TaskPlan,
    TaskSchedule,
    TaskState,
    TaskType,
)
from framework.helpers.task_serialization import (
    deserialize_task,
    parse_datetime,
    parse_task_plan,
    parse_task_schedule,
    serialize_datetime,
    serialize_task,
    serialize_task_plan,
    serialize_task_schedule,
    serialize_tasks,
)


# Keep the main scheduler instance accessible for backward compatibility
def get_scheduler() -> TaskScheduler:
    """Get the global task scheduler instance."""
    return TaskScheduler.get()


# Keep the main task list accessible for backward compatibility
def get_task_list() -> SchedulerTaskList:
    """Get the global task list instance."""
    return SchedulerTaskList.get()


# Legacy compatibility exports
__all__ = [
    # Enums
    "TaskState",
    "TaskType",
    # Models
    "TaskSchedule",
    "TaskPlan",
    "BaseTask",
    "AdHocTask",
    "ScheduledTask",
    "PlannedTask",
    "Task",
    # Serialization
    "serialize_datetime",
    "parse_datetime",
    "serialize_task_schedule",
    "parse_task_schedule",
    "serialize_task_plan",
    "parse_task_plan",
    "serialize_task",
    "serialize_tasks",
    "deserialize_task",
    # Management
    "SchedulerTaskList",
    "TaskScheduler",
    "SCHEDULER_FOLDER",
    # Convenience functions
    "get_scheduler",
    "get_task_list",
]
