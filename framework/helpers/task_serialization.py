"""Task serialization and deserialization utilities."""

# Standard library imports
from datetime import datetime, timezone
from typing import Any, Optional, TypeVar, Union

# Local imports
from framework.helpers.localization import Localization
from framework.helpers.task_models import (
    AdHocTask,
    PlannedTask,
    ScheduledTask,
    TaskPlan,
    TaskSchedule,
)


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Serialize a datetime object to ISO format string in the user's timezone.

    This uses the Localization singleton to convert the datetime to the user's timezone
    before serializing it to an ISO format string for frontend display.

    Returns None if the input is None.
    """
    if dt is None:
        return None

    localization = Localization.get()
    local_dt = localization.to_user_timezone(dt)
    return local_dt.isoformat()


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO format datetime string with timezone awareness.

    This converts from the localized ISO format returned by serialize_datetime
    back to a datetime object with proper timezone handling.

    Returns None if dt_str is None.
    """
    if dt_str is None:
        return None

    try:
        # Parse the ISO format datetime string
        dt = datetime.fromisoformat(dt_str)

        # If it's naive, assume it's in user's timezone and convert to UTC
        if dt.tzinfo is None:
            localization = Localization.get()
            dt = localization.from_user_timezone(dt)

        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def serialize_task_schedule(schedule: TaskSchedule) -> dict[str, str]:
    """Convert TaskSchedule to a standardized dictionary format."""
    return {
        "minute": schedule.minute,
        "hour": schedule.hour,
        "day": schedule.day,
        "month": schedule.month,
        "weekday": schedule.weekday,
        "timezone": schedule.timezone,
    }


def parse_task_schedule(schedule_data: dict[str, str]) -> TaskSchedule:
    """Parse dictionary into TaskSchedule with validation."""
    return TaskSchedule(
        minute=schedule_data.get("minute", "*"),
        hour=schedule_data.get("hour", "*"),
        day=schedule_data.get("day", "*"),
        month=schedule_data.get("month", "*"),
        weekday=schedule_data.get("weekday", "*"),
        timezone=schedule_data.get("timezone", Localization.get().get_timezone()),
    )


def serialize_task_plan(plan: TaskPlan) -> dict[str, Any]:
    """Convert TaskPlan to a standardized dictionary format."""
    return {
        "todo": [serialize_datetime(dt) for dt in plan.todo],
        "in_progress": serialize_datetime(plan.in_progress),
        "done": [serialize_datetime(dt) for dt in plan.done],
    }


def parse_task_plan(plan_data: dict[str, Any]) -> TaskPlan:
    """Parse dictionary into TaskPlan with validation."""
    todo_list = []
    if "todo" in plan_data and isinstance(plan_data["todo"], list):
        for dt_str in plan_data["todo"]:
            parsed_dt = parse_datetime(dt_str)
            if parsed_dt:
                todo_list.append(parsed_dt)

    in_progress = None
    if "in_progress" in plan_data:
        in_progress = parse_datetime(plan_data["in_progress"])

    done_list = []
    if "done" in plan_data and isinstance(plan_data["done"], list):
        for dt_str in plan_data["done"]:
            parsed_dt = parse_datetime(dt_str)
            if parsed_dt:
                done_list.append(parsed_dt)

    return TaskPlan(
        todo=todo_list,
        in_progress=in_progress,
        done=done_list,
    )


T = TypeVar("T", bound=Union[ScheduledTask, AdHocTask, PlannedTask])


def serialize_task(
    task: Union[ScheduledTask, AdHocTask, PlannedTask],
) -> dict[str, Any]:
    """
    Standardized serialization for task objects with proper handling of all complex types.
    """
    base_data = {
        "uuid": task.uuid,
        "context_id": task.context_id,
        "state": task.state,
        "name": task.name,
        "system_prompt": task.system_prompt,
        "prompt": task.prompt,
        "attachments": task.attachments,
        "created_at": serialize_datetime(task.created_at),
        "updated_at": serialize_datetime(task.updated_at),
        "last_run": serialize_datetime(task.last_run),
        "last_result": task.last_result,
        "type": task.type,
    }

    # Add type-specific fields
    if isinstance(task, ScheduledTask):
        base_data["schedule"] = serialize_task_schedule(task.schedule)
    elif isinstance(task, AdHocTask):
        base_data["token"] = task.token
    elif isinstance(task, PlannedTask):
        base_data["plan"] = serialize_task_plan(task.plan)

    return base_data


def serialize_tasks(
    tasks: list[Union[ScheduledTask, AdHocTask, PlannedTask]],
) -> list[dict[str, Any]]:
    """
    Serialize a list of tasks to a list of dictionaries.
    """
    return [serialize_task(task) for task in tasks]


def deserialize_task(task_data: dict[str, Any], task_class: Optional[type[T]] = None) -> T:
    """
    Deserialize dictionary into appropriate task object with validation.
    If task_class is provided, uses that type. Otherwise determines type from data.
    """
    # Parse common fields
    base_fields = {
        "uuid": task_data.get("uuid"),
        "context_id": task_data.get("context_id"),
        "state": task_data.get("state"),
        "name": task_data.get("name"),
        "system_prompt": task_data.get("system_prompt", ""),
        "prompt": task_data.get("prompt", ""),
        "attachments": task_data.get("attachments", []),
        "created_at": parse_datetime(task_data.get("created_at")),
        "updated_at": parse_datetime(task_data.get("updated_at")),
        "last_run": parse_datetime(task_data.get("last_run")),
        "last_result": task_data.get("last_result"),
    }

    # Determine task type
    task_type = task_data.get("type")
    if task_class:
        target_class = task_class
    elif task_type == "scheduled":
        target_class = ScheduledTask
    elif task_type == "adhoc":
        target_class = AdHocTask
    elif task_type == "planned":
        target_class = PlannedTask
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    # Add type-specific fields
    if target_class == ScheduledTask:
        if "schedule" in task_data:
            base_fields["schedule"] = parse_task_schedule(task_data["schedule"])
        else:
            base_fields["schedule"] = TaskSchedule()
    elif target_class == AdHocTask:
        base_fields["token"] = task_data.get("token", "")
    elif target_class == PlannedTask:
        if "plan" in task_data:
            base_fields["plan"] = parse_task_plan(task_data["plan"])
        else:
            base_fields["plan"] = TaskPlan()

    # Filter out None values for optional fields
    filtered_fields = {k: v for k, v in base_fields.items() if v is not None}

    return target_class(**filtered_fields)
