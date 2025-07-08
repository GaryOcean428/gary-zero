"""Task model definitions for the scheduler system."""

# Standard library imports
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Optional, Union

# Third-party imports
try:
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    # nest_asyncio is optional - used for nested event loops
    pass

try:
    import pytz
except ImportError:
    # pytz is optional - used for timezone handling
    pytz = None

try:
    from crontab import CronTab
except ImportError:
    # crontab is optional - used for cron schedule parsing
    CronTab = None

from pydantic import BaseModel, Field

# Local imports
from framework.helpers.localization import Localization
from framework.helpers.print_style import PrintStyle


class TaskState(str, Enum):
    """Enumeration of possible task states."""

    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"


class TaskType(str, Enum):
    """Enumeration of task types."""

    AD_HOC = "adhoc"
    SCHEDULED = "scheduled"
    PLANNED = "planned"


class TaskSchedule(BaseModel):
    """Cron-style task schedule configuration."""

    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    weekday: str = "*"
    timezone: str = Field(default_factory=lambda: Localization.get().get_timezone())

    def to_crontab(self) -> str:
        """Convert to crontab format string."""
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"


class TaskPlan(BaseModel):
    """Task plan for managing planned task execution."""

    todo: list[datetime] = Field(default_factory=list)
    in_progress: datetime | None = None
    done: list[datetime] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        todo: list[datetime] = None,
        in_progress: datetime | None = None,
        done: list[datetime] = None,
    ) -> "TaskPlan":
        """Create a new TaskPlan instance."""
        return cls(
            todo=todo or [],
            in_progress=in_progress,
            done=done or [],
        )

    def add_todo(self, launch_time: datetime) -> None:
        """Add a launch time to the todo list."""
        if launch_time not in self.todo:
            self.todo.append(launch_time)
            self.todo.sort()

    def set_in_progress(self, launch_time: datetime) -> None:
        """Mark a launch time as in progress."""
        if launch_time in self.todo:
            self.todo.remove(launch_time)
        self.in_progress = launch_time

    def set_done(self, launch_time: datetime) -> None:
        """Mark a launch time as done."""
        if launch_time == self.in_progress:
            self.in_progress = None
        if launch_time not in self.done:
            self.done.append(launch_time)
            self.done.sort()

    def get_next_launch_time(self) -> datetime | None:
        """Get the next scheduled launch time."""
        if self.todo:
            return min(self.todo)
        return None

    def should_launch(self) -> bool:
        """Check if the task should launch now."""
        if self.in_progress is not None:
            return False

        next_launch = self.get_next_launch_time()
        if next_launch is None:
            return False

        return datetime.now(timezone.utc) >= next_launch


class BaseTask(BaseModel):
    """Base class for all task types."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: Optional[str] = Field(default=None)
    state: TaskState = Field(default=TaskState.IDLE)
    name: str = Field()
    system_prompt: str
    prompt: str
    attachments: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_run: datetime | None = None
    last_result: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context_id:
            self.context_id = self.uuid
        self._lock = threading.RLock()

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        **kwargs,
    ) -> None:
        """Update task properties."""
        with self._lock:
            if name is not None:
                self.name = name
            if state is not None:
                self.state = state
            if system_prompt is not None:
                self.system_prompt = system_prompt
            if prompt is not None:
                self.prompt = prompt
            if attachments is not None:
                self.attachments = attachments
            if last_run is not None:
                self.last_run = last_run
            if last_result is not None:
                self.last_result = last_result
            if context_id is not None:
                self.context_id = context_id

            self.updated_at = datetime.now(timezone.utc)

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Check if task should run based on schedule. Override in subclasses."""
        return False

    def get_next_run(self) -> datetime | None:
        """Get next scheduled run time. Override in subclasses."""
        return None

    def get_next_run_minutes(self) -> int | None:
        """Get minutes until next run. Works with overridden get_next_run()."""
        next_run = self.get_next_run()
        if next_run is None:
            return None

        now = datetime.now(timezone.utc)
        return int((next_run - now).total_seconds() / 60)

    async def on_run(self):
        """Called when task starts running. Override in subclasses."""
        pass

    async def on_finish(self):
        """Called when task finishes. Override in subclasses."""
        pass

    async def on_error(self, error: str):
        """Called when task encounters an error. Override in subclasses."""
        pass

    async def on_success(self, result: str):
        """Called when task completes successfully. Override in subclasses."""
        pass


class AdHocTask(BaseTask):
    """Ad-hoc task that runs once when triggered."""

    type: Literal[TaskType.AD_HOC] = TaskType.AD_HOC
    token: str = Field(default_factory=lambda: str(uuid.uuid4().int))

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        token: str,
        attachments: list[str] = None,
        context_id: str | None = None,
    ) -> "AdHocTask":
        """Create a new AdHocTask instance."""
        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            token=token,
            attachments=attachments or [],
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        token: str | None = None,
        **kwargs,
    ) -> None:
        """Update ad-hoc task properties."""
        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            **kwargs,
        )
        if token is not None:
            self.token = token


class ScheduledTask(BaseTask):
    """Scheduled task that runs based on cron-style schedule."""

    type: Literal[TaskType.SCHEDULED] = TaskType.SCHEDULED
    schedule: TaskSchedule

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        schedule: TaskSchedule,
        attachments: list[str] = None,
        context_id: str | None = None,
        task_timezone: str | None = None,
    ) -> "ScheduledTask":
        """Create a new ScheduledTask instance."""
        if task_timezone:
            schedule.timezone = task_timezone
        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            schedule=schedule,
            attachments=attachments or [],
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        schedule: TaskSchedule | None = None,
        **kwargs,
    ) -> None:
        """Update scheduled task properties."""
        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            **kwargs,
        )
        if schedule is not None:
            self.schedule = schedule

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Check if task should run based on cron schedule."""
        try:
            # Create cron object from schedule
            cron = CronTab(self.schedule.to_crontab())

            # Get timezone
            tz = pytz.timezone(self.schedule.timezone)
            now = datetime.now(tz)

            # Check if we should run now
            delay = cron.next(now=now, default_utc=False)
            return delay <= frequency_seconds

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error checking schedule for task {self.name}: {str(e)}"
            )
            return False

    def get_next_run(self) -> datetime | None:
        """Get next scheduled run time."""
        try:
            cron = CronTab(self.schedule.to_crontab())
            tz = pytz.timezone(self.schedule.timezone)
            now = datetime.now(tz)

            # Get next run time and convert to UTC
            next_run_local = cron.next(now=now, default_utc=False, return_datetime=True)
            return next_run_local.astimezone(timezone.utc)

        except Exception:
            return None


class PlannedTask(BaseTask):
    """Planned task that runs at specific planned times."""

    type: Literal[TaskType.PLANNED] = TaskType.PLANNED
    plan: TaskPlan

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        plan: TaskPlan,
        attachments: list[str] = None,
        context_id: str | None = None,
    ) -> "PlannedTask":
        """Create a new PlannedTask instance."""
        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            plan=plan,
            attachments=attachments or [],
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        plan: TaskPlan | None = None,
        **kwargs,
    ) -> None:
        """Update planned task properties."""
        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            **kwargs,
        )
        if plan is not None:
            self.plan = plan

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Check if task should run based on plan."""
        return self.plan.should_launch()

    def get_next_run(self) -> datetime | None:
        """Get next planned run time."""
        return self.plan.get_next_launch_time()

    async def on_run(self):
        """Called when planned task starts running."""
        next_launch = self.plan.get_next_launch_time()
        if next_launch:
            self.plan.set_in_progress(next_launch)

    async def on_finish(self):
        """Called when planned task finishes."""
        if self.plan.in_progress:
            self.plan.set_done(self.plan.in_progress)

    async def on_success(self, result: str):
        """Called when planned task completes successfully."""
        await self.on_finish()

    async def on_error(self, error: str):
        """Called when planned task encounters an error."""
        await self.on_finish()


# Type alias for all task types
Task = Annotated[Union[ScheduledTask, AdHocTask, PlannedTask], Field(discriminator="type")]
