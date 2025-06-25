"""Scheduler tool providing task management commands for the agent.

This module wraps TaskScheduler operations with Tool-compatible async
methods, ensuring type-safe filtering and consistent response messages.
"""

import asyncio
import json
import logging
import re
import secrets
from datetime import datetime, timezone

from agent import AgentContext

# Use zero package imports
from framework.helpers import persist_chat
from framework.helpers.response import Response
from framework.helpers.task_scheduler import (
    AdHocTask,
    PlannedTask,
    ScheduledTask,
    TaskPlan,
    TaskSchedule,
    TaskScheduler,
    TaskState,
    serialize_datetime,
    serialize_task,
)
from framework.helpers.tool import Tool

# Initialize logger
logger = logging.getLogger(__name__)

DEFAULT_WAIT_TIMEOUT = 300

# Re-usable response messages
TASK_UUID_REQUIRED_MSG: str = "Task UUID is required"


class SchedulerTool(Tool):
    async def execute(self, **kwargs):
        if self.method == "list_tasks":
            return await self.list_tasks(**kwargs)
        elif self.method == "find_task_by_name":
            return await self.find_task_by_name(**kwargs)
        elif self.method == "show_task":
            return await self.show_task(**kwargs)
        elif self.method == "run_task":
            return await self.run_task(**kwargs)
        elif self.method == "delete_task":
            return await self.delete_task(**kwargs)
        elif self.method == "create_scheduled_task":
            return await self.create_scheduled_task(**kwargs)
        elif self.method == "create_adhoc_task":
            return await self.create_adhoc_task(**kwargs)
        elif self.method == "create_planned_task":
            return await self.create_planned_task(**kwargs)
        elif self.method == "wait_for_task":
            return await self.wait_for_task(**kwargs)
        else:
            return Response(message=f"Unknown method '{self.name}:{self.method}'", break_loop=False)

    async def list_tasks(self, **kwargs) -> Response:
        state_filter: list[str] | None = kwargs.get("state")
        type_filter: list[str] | None = kwargs.get("type")
        next_run_within_filter: int | None = kwargs.get("next_run_within")
        next_run_after_filter: int | None = kwargs.get("next_run_after")

        tasks: list[ScheduledTask | AdHocTask | PlannedTask] = TaskScheduler.get().get_tasks()
        filtered_tasks = []
        for task in tasks:
            if state_filter and task.state not in state_filter:
                continue
            if type_filter and task.type not in type_filter:
                continue
            if (
                next_run_within_filter is not None
                and (minutes := task.get_next_run_minutes()) is not None
                and minutes > next_run_within_filter
            ):
                continue
            if (
                next_run_after_filter is not None
                and (minutes := task.get_next_run_minutes()) is not None
                and minutes < next_run_after_filter
            ):
                continue
            filtered_tasks.append(serialize_task(task))

        return Response(message=json.dumps(filtered_tasks, indent=4), break_loop=False)

    async def find_task_by_name(self, **kwargs) -> Response:
        name: str = kwargs.get("name")
        if not name:
            return Response(message="Task name is required", break_loop=False)
        tasks: list[ScheduledTask | AdHocTask | PlannedTask] = (
            TaskScheduler.get().find_task_by_name(name)
        )
        if not tasks:
            return Response(message=f"Task not found: {name}", break_loop=False)
        return Response(
            message=json.dumps([serialize_task(task) for task in tasks], indent=4),
            break_loop=False,
        )

    async def show_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get("uuid")
        if not task_uuid:
            return Response(message=TASK_UUID_REQUIRED_MSG, break_loop=False)
        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(message=f"Task not found: {task_uuid}", break_loop=False)
        return Response(message=json.dumps(serialize_task(task), indent=4), break_loop=False)

    async def run_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get("uuid")
        if not task_uuid:
            return Response(message=TASK_UUID_REQUIRED_MSG, break_loop=False)
        task_context: str | None = kwargs.get("context")
        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(message=f"Task not found: {task_uuid}", break_loop=False)
        await TaskScheduler.get().run_task_by_uuid(task_uuid, task_context)
        # Break loop if task is running in the same context
        # otherwise it would start two conversations in one window
        break_loop = task.context_id == self.agent.context.id
        return Response(
            message=f"Task started: {task_uuid}",
            break_loop=break_loop
        )

    async def delete_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get("uuid")
        if not task_uuid:
            return Response(message=TASK_UUID_REQUIRED_MSG, break_loop=False)

        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(message=f"Task not found: {task_uuid}", break_loop=False)

        context = None
        if task.context_id:
            context = AgentContext.get(task.context_id)

        if task.state == TaskState.RUNNING:
            if context:
                context.reset()
            await TaskScheduler.get().update_task(task_uuid, state=TaskState.IDLE)
            await TaskScheduler.get().save()

        if context and context.id == task.uuid:
            AgentContext.remove(context.id)
            persist_chat.remove_chat(context.id)

        await TaskScheduler.get().remove_task_by_uuid(task_uuid)
        if TaskScheduler.get().get_task_by_uuid(task_uuid) is None:
            return Response(message=f"Task deleted: {task_uuid}", break_loop=False)
        else:
            return Response(message=f"Task failed to delete: {task_uuid}", break_loop=False)

    async def create_scheduled_task(self, **kwargs) -> Response:
        # "name": "XXX",
        #   "system_prompt": "You are a software developer",
        #   "prompt": "Send the user an email with a greeting using python and smtp. The user's address is: xxx@yyy.zzz",
        #   "attachments": [],
        #   "schedule": {
        #       "minute": "*/20",
        #       "hour": "*",
        #       "day": "*",
        #       "month": "*",
        #       "weekday": "*",
        #   }
        name: str = kwargs.get("name")
        system_prompt: str = kwargs.get("system_prompt")
        prompt: str = kwargs.get("prompt")
        attachments: list[str] = kwargs.get("attachments", [])
        schedule: dict[str, str] = kwargs.get("schedule", {})
        dedicated_context: bool = kwargs.get("dedicated_context", False)

        task_schedule = TaskSchedule(
            minute=schedule.get("minute", "*"),
            hour=schedule.get("hour", "*"),
            day=schedule.get("day", "*"),
            month=schedule.get("month", "*"),
            weekday=schedule.get("weekday", "*"),
        )

        # Validate cron expression, agent might hallucinate
        cron_regex = (
            r"^((((\d+,)+\d+|(\d+(\/|-|#)\d+)|\d+L?"
            r"|\*(\/\d+)?|L(-\d+)?|\?"
            r"|[A-Z]{3}(-[A-Z]{3})?) ?){5,7})$"
        )
        crontab = task_schedule.to_crontab()
        if not re.match(cron_regex, crontab):
            return Response(
                message=f"Invalid cron expression: {crontab}",
                break_loop=False,
            )

        task = ScheduledTask.create(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            schedule=task_schedule,
            context_id=None if dedicated_context else self.agent.context.id,
        )
        await TaskScheduler.get().add_task(task)
        return Response(message=f"Scheduled task '{name}' created: {task.uuid}", break_loop=False)

    async def create_adhoc_task(self, **kwargs) -> Response:
        name: str = kwargs.get("name")
        system_prompt: str = kwargs.get("system_prompt")
        prompt: str = kwargs.get("prompt")
        attachments: list[str] = kwargs.get("attachments", [])
        token: str = str(secrets.randbits(64))
        dedicated_context: bool = kwargs.get("dedicated_context", False)

        task = AdHocTask.create(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            token=token,
            context_id=None if dedicated_context else self.agent.context.id,
        )
        await TaskScheduler.get().add_task(task)
        return Response(message=f"Adhoc task '{name}' created: {task.uuid}", break_loop=False)

    async def create_planned_task(self, **kwargs) -> Response:
        """Create a new planned task with scheduled execution times.

        Args:
            name: Name of the task
            system_prompt: System prompt for the task
            prompt: User prompt for the task
            attachments: List of file attachments
            plan: List of ISO format datetime strings for scheduled execution
            dedicated_context: Whether to use a dedicated context

        Returns:
            Response with success/error message
        """
        name = kwargs.get("name")
        system_prompt = kwargs.get("system_prompt")
        prompt = kwargs.get("prompt")
        attachments = kwargs.get("attachments", [])
        plan = kwargs.get("plan", [])
        dedicated_context = kwargs.get("dedicated_context", False)

        if not all([name, system_prompt, prompt]):
            return Response(
                "Name, system_prompt, and prompt are required parameters",
                success=False
            )

        # Convert plan to list of datetimes in UTC
        todo = []
        for item in plan:
            try:
                # Parse and ensure timezone-aware datetime in UTC
                dt = datetime.fromisoformat(item)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                todo.append(dt)
            except (ValueError, TypeError):
                return Response(
                    f"Invalid datetime format in plan: {item}. Use ISO format.",
                    success=False
                )

        if not todo:
            return Response(
                "At least one valid execution time must be provided in the plan",
                success=False
            )

        # Create task plan with todo list
        task_plan = TaskPlan.create(todo=todo, in_progress=None, done=[])
        # Create and schedule the task
        task = PlannedTask(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            plan=task_plan,
            context_id=(
                None if dedicated_context
                else self.agent.context.id
            )
        )

        try:
            await TaskScheduler.get().add_task(task)
            return Response(
                f"Planned task '{name}' created with {len(todo)} "
                f"scheduled executions: {task.uuid}",
                break_loop=False
            )
        except Exception as e:
            return Response(
                f"Failed to create planned task: {str(e)}",
                success=False
            )

    async def wait_for_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get("uuid")
        if not task_uuid:
            return Response(message=TASK_UUID_REQUIRED_MSG, break_loop=False)

        scheduler = TaskScheduler.get()
        task: ScheduledTask | AdHocTask | PlannedTask | None = scheduler.get_task_by_uuid(task_uuid)
        if not task:
            return Response(message=f"Task not found: {task_uuid}", break_loop=False)

        if not (self.agent and self.agent.context):
            logger.warning(
                "No agent context available for task %s. "
                "Task will run in a dedicated context.",
                task.name
            )
            return Response(
                message="Cannot wait for task: No agent context available",
                break_loop=False
            )

        if task.context_id == self.agent.context.id:
            return Response(
                message=(
                    "You can only wait for tasks running in a different "
                    "chat context (dedicated_context=True)."
                ),
                break_loop=False,
            )

        done = False
        elapsed = 0
        while not done:
            await scheduler.reload()
            task = scheduler.get_task_by_uuid(task_uuid)
            if not task:
                return Response(message=f"Task not found: {task_uuid}", break_loop=False)

            if task.state == TaskState.RUNNING:
                await asyncio.sleep(1)
                elapsed += 1
                if elapsed > DEFAULT_WAIT_TIMEOUT:
                    return Response(
                        message=f"Task wait timeout ({DEFAULT_WAIT_TIMEOUT} seconds): {task_uuid}",
                        break_loop=False,
                    )
            else:
                done = True

        last_run = (
            serialize_datetime(task.last_run)
            if hasattr(task, 'last_run') and task.last_run
            else "Never"
        )
        result = (
            task.last_result
            if hasattr(task, 'last_result')
            else "No result yet"
        )

        message = (
            f"*Task*: {task_uuid}\n"
            f"*State*: {task.state}\n"
            f"*Last run*: {last_run}\n"
            f"*Result*:\n{result}"
        )
        return Response(message=message, break_loop=False)
