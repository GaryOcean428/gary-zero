"""Task scheduler for managing and executing scheduled, ad-hoc, and planned tasks."""

# Re-export all components from the modular structure for backward compatibility
from framework.helpers.task_models import (
    TaskState,
    TaskType,
    TaskSchedule,
    TaskPlan,
    BaseTask,
    AdHocTask,
    ScheduledTask,
    PlannedTask,
    Task,
)

from framework.helpers.task_serialization import (
    serialize_datetime,
    parse_datetime,
    serialize_task_schedule,
    parse_task_schedule,
    serialize_task_plan,
    parse_task_plan,
    serialize_task,
    serialize_tasks,
    deserialize_task,
)

from framework.helpers.task_management import (
    SchedulerTaskList,
    TaskScheduler,
    SCHEDULER_FOLDER,
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
    'TaskState',
    'TaskType',
    
    # Models
    'TaskSchedule',
    'TaskPlan', 
    'BaseTask',
    'AdHocTask',
    'ScheduledTask',
    'PlannedTask',
    'Task',
    
    # Serialization
    'serialize_datetime',
    'parse_datetime',
    'serialize_task_schedule',
    'parse_task_schedule',
    'serialize_task_plan',
    'parse_task_plan',
    'serialize_task',
    'serialize_tasks',
    'deserialize_task',
    
    # Management
    'SchedulerTaskList',
    'TaskScheduler',
    'SCHEDULER_FOLDER',
    
    # Convenience functions
    'get_scheduler',
    'get_task_list',
]
