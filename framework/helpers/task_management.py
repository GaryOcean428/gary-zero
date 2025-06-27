"""Task management classes for the scheduler system."""

# Standard library imports
import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Any, Callable, ClassVar, Optional, Union

# Third-party imports
from pydantic import BaseModel, Field, PrivateAttr

# Local imports
from agent import AgentContext, UserMessage
from framework.helpers.defer import DeferredTask
from framework.helpers.files import get_abs_path, make_dirs, read_file, write_file
from framework.helpers.localization import Localization
from framework.helpers.persist_chat import save_tmp_chat
from framework.helpers.print_style import PrintStyle
from framework.helpers.task_models import (
    AdHocTask,
    BaseTask,
    PlannedTask,
    ScheduledTask,
    Task,
    TaskState,
)
from framework.helpers.task_serialization import deserialize_task, serialize_tasks

SCHEDULER_FOLDER = "tmp/scheduler"


class SchedulerTaskList(BaseModel):
    """Manages the list of all scheduled tasks."""
    tasks: list[Task] = Field(default_factory=list)
    __instance: ClassVar[Optional["SchedulerTaskList"]] = PrivateAttr(default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    @classmethod
    def get(cls) -> "SchedulerTaskList":
        """Get the singleton instance."""
        if cls.__instance is None:
            cls.__instance = cls()
            cls.__instance.reload()
        return cls.__instance

    def reload(self) -> None:
        """Reload tasks from disk."""
        with self._lock:
            tasks_file = get_abs_path(f"{SCHEDULER_FOLDER}/tasks.json")
            
            if not read_file(tasks_file):
                self.tasks = []
                self.save()
                return
            
            try:
                tasks_data = json.loads(read_file(tasks_file))
                self.tasks = []
                
                for task_data in tasks_data:
                    try:
                        # Handle both string and dict task_data
                        if isinstance(task_data, str):
                            # Skip string entries that aren't valid task data
                            continue
                        elif isinstance(task_data, dict):
                            task = deserialize_task(task_data)
                            self.tasks.append(task)
                        else:
                            # Skip unknown data types
                            continue
                    except Exception as e:
                        # Get UUID safely for error reporting
                        task_uuid = "unknown"
                        if isinstance(task_data, dict):
                            task_uuid = task_data.get('uuid', 'unknown')
                        
                        PrintStyle(font_color="red", padding=True).print(
                            f"Error loading task {task_uuid}: {str(e)}"
                        )
                        
            except Exception as e:
                PrintStyle(font_color="red", padding=True).print(
                    f"Error loading tasks: {str(e)}"
                )
                self.tasks = []

    def add_task(self, task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> None:
        """Add a task to the list."""
        with self._lock:
            # Remove existing task with same UUID if exists
            self.tasks = [t for t in self.tasks if t.uuid != task.uuid]
            self.tasks.append(task)
            self.save()

    def save(self) -> None:
        """Save tasks to disk."""
        with self._lock:
            make_dirs(SCHEDULER_FOLDER)
            tasks_file = get_abs_path(f"{SCHEDULER_FOLDER}/tasks.json")
            
            try:
                serialized_tasks = serialize_tasks(self.tasks)
                write_file(tasks_file, json.dumps(serialized_tasks, indent=2))
            except Exception as e:
                PrintStyle(font_color="red", padding=True).print(
                    f"Error saving tasks: {str(e)}"
                )

    def update_task_by_uuid(
        self,
        task_uuid: str,
        updater_func: Callable[[Union[ScheduledTask, AdHocTask, PlannedTask]], None],
        verify_func: Callable[[Union[ScheduledTask, AdHocTask, PlannedTask]], bool] = (
            lambda task: True
        ),
    ) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """
        Atomically update a task by UUID using the provided updater function.

        The updater_func should take the task as an argument and perform any necessary updates.
        This method ensures that the task is updated and saved atomically, preventing race
        conditions.

        Returns the updated task or None if not found.
        """
        with self._lock:
            for task in self.tasks:
                if task.uuid == task_uuid and verify_func(task):
                    updater_func(task)
                    self.save()
                    return task
            return None

    def get_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Get all tasks."""
        with self._lock:
            return self.tasks.copy()

    def get_tasks_by_context_id(
        self, context_id: str, only_running: bool = False
    ) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Get tasks by context ID."""
        with self._lock:
            result = []
            for task in self.tasks:
                if task.context_id == context_id:
                    if not only_running or task.state == TaskState.RUNNING:
                        result.append(task)
            return result

    def get_due_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Get tasks that are due to run."""
        with self._lock:
            due_tasks = []
            for task in self.tasks:
                if task.state != TaskState.RUNNING and task.check_schedule():
                    due_tasks.append(task)
            return due_tasks

    def get_task_by_uuid(
        self, task_uuid: str
    ) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """Get a task by UUID."""
        with self._lock:
            for task in self.tasks:
                if task.uuid == task_uuid:
                    return task
            return None

    def get_task_by_name(self, name: str) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """Get the first task with the given name."""
        with self._lock:
            for task in self.tasks:
                if task.name == name:
                    return task
            return None

    def find_task_by_name(self, name: str) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Find all tasks with the given name."""
        with self._lock:
            return [task for task in self.tasks if task.name == name]

    def remove_task_by_uuid(self, task_uuid: str) -> bool:
        """Remove a task by UUID."""
        with self._lock:
            original_count = len(self.tasks)
            self.tasks = [task for task in self.tasks if task.uuid != task_uuid]
            
            if len(self.tasks) < original_count:
                self.save()
                return True
            return False

    def remove_task_by_name(self, name: str) -> bool:
        """Remove all tasks with the given name."""
        with self._lock:
            original_count = len(self.tasks)
            self.tasks = [task for task in self.tasks if task.name != name]
            
            if len(self.tasks) < original_count:
                self.save()
                return True
            return False


class TaskScheduler:
    """Main task scheduler for managing and executing tasks."""
    _instance = None

    def __init__(self):
        # Only initialize if this is a new instance
        if not hasattr(self, "_initialized"):
            self._tasks = SchedulerTaskList.get()
            self._printer = PrintStyle(italic=True, font_color="green", padding=False)
            self._initialized = True

    @classmethod
    def get(cls) -> "TaskScheduler":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reload(self) -> None:
        """Reload tasks from storage."""
        self._tasks.reload()

    def get_tasks(self) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Get all tasks."""
        return self._tasks.get_tasks()

    def get_tasks_by_context_id(
        self, context_id: str, only_running: bool = False
    ) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Get tasks by context ID."""
        return self._tasks.get_tasks_by_context_id(context_id, only_running)

    def add_task(self, task: Union[ScheduledTask, AdHocTask, PlannedTask]) -> None:
        """Add a task to the scheduler."""
        self._tasks.add_task(task)

    def remove_task_by_uuid(self, task_uuid: str) -> bool:
        """Remove a task by UUID."""
        return self._tasks.remove_task_by_uuid(task_uuid)

    def remove_task_by_name(self, name: str) -> bool:
        """Remove all tasks with the given name."""
        return self._tasks.remove_task_by_name(name)

    def get_task_by_uuid(
        self, task_uuid: str
    ) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """Get a task by UUID."""
        return self._tasks.get_task_by_uuid(task_uuid)

    def get_task_by_name(self, name: str) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """Get the first task with the given name."""
        return self._tasks.get_task_by_name(name)

    def find_task_by_name(self, name: str) -> list[Union[ScheduledTask, AdHocTask, PlannedTask]]:
        """Find all tasks with the given name."""
        return self._tasks.find_task_by_name(name)

    async def tick(self) -> None:
        """Check for and run due tasks."""
        due_tasks = self._tasks.get_due_tasks()
        
        for task in due_tasks:
            self._printer.print(f"Running scheduled task: {task.name}")
            
            # Run task in background
            DeferredTask.create(
                self._run_task_wrapper,
                task.uuid,
                None,  # task_context
            )

    def run_task_by_uuid(self, task_uuid: str, task_context: str | None = None) -> bool:
        """Run a task by UUID."""
        task = self.get_task_by_uuid(task_uuid)
        if not task:
            return False
        
        self._printer.print(f"Running task: {task.name}")
        
        # Run task in background
        DeferredTask.create(
            self._run_task_wrapper,
            task_uuid,
            task_context,
        )
        return True

    def run_task_by_name(self, name: str, task_context: str | None = None) -> bool:
        """Run the first task with the given name."""
        task = self.get_task_by_name(name)
        if not task:
            return False
        
        return self.run_task_by_uuid(task.uuid, task_context)

    def save(self) -> None:
        """Save all tasks to storage."""
        self._tasks.save()

    def update_task_checked(
        self,
        task_uuid: str,
        verify_func: Callable[
            [Union[ScheduledTask, AdHocTask, PlannedTask]], bool
        ] = lambda task: True,
        **update_params,
    ) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """
        Atomically update a task by UUID with the provided parameters.
        This prevents race conditions when multiple processes update tasks concurrently.

        Returns the updated task or None if not found.
        """
        def _update_task(task):
            task.update(**update_params)

        return self._tasks.update_task_by_uuid(task_uuid, _update_task, verify_func)

    def update_task(
        self, task_uuid: str, **update_params
    ) -> Union[ScheduledTask, AdHocTask, PlannedTask] | None:
        """Update a task by UUID with the provided parameters."""
        return self.update_task_checked(task_uuid, **update_params)

    def __new_context(
        self, task: Union[ScheduledTask, AdHocTask, PlannedTask]
    ) -> AgentContext:
        """Create a new agent context for task execution."""
        from initialize import initialize_agent
        agent = initialize_agent()
        
        context = AgentContext(
            agent=agent,
            context_id=task.context_id,
            system_prompt=task.system_prompt,
        )
        
        return context

    def _get_chat_context(
        self, task: Union[ScheduledTask, AdHocTask, PlannedTask]
    ) -> AgentContext:
        """Get or create chat context for the task."""
        try:
            from initialize import initialize_agent
            agent = initialize_agent()
            context = agent.load_context(task.context_id)
            
            if context is None:
                context = self.__new_context(task)
                
            return context
            
        except Exception as e:
            self._printer.print(f"Error loading context, creating new one: {str(e)}")
            return self.__new_context(task)

    def _persist_chat(
        self, task: Union[ScheduledTask, AdHocTask, PlannedTask], context: AgentContext
    ) -> None:
        """Persist chat context after task execution."""
        try:
            # Save context
            context.agent.save_context(context)
            
            # Save temporary chat
            save_tmp_chat(context.context_id, context.chat_history)
            
        except Exception as e:
            self._printer.print(f"Error persisting chat: {str(e)}")

    async def _run_task(
        self,
        task: Union[ScheduledTask, AdHocTask, PlannedTask],
        task_context: str | None = None,
    ) -> None:
        """Execute a task asynchronously."""
        try:
            # Update task state to running
            self.update_task(task.uuid, state=TaskState.RUNNING, last_run=datetime.now(timezone.utc))
            
            # Call task's on_run hook
            await task.on_run()
            
            # Get chat context
            context = self._get_chat_context(task)
            
            # Create user message
            message_content = task.prompt
            if task_context:
                message_content = f"{task_context}\n\n{message_content}"
            
            user_message = UserMessage(content=message_content, attachments=task.attachments)
            
            # Execute task
            response = await context.agent.message_loop_async(user_message, context)
            
            # Update task with result
            self.update_task(
                task.uuid,
                state=TaskState.FINISHED,
                last_result=response.content if response else "No response",
            )
            
            # Call success hook
            await task.on_success(response.content if response else "No response")
            
            # Persist chat context
            self._persist_chat(task, context)
            
        except Exception as e:
            error_msg = str(e)
            self._printer.print(f"Error running task {task.name}: {error_msg}")
            
            # Update task with error
            self.update_task(
                task.uuid,
                state=TaskState.FINISHED,
                last_result=f"Error: {error_msg}",
            )
            
            # Call error hook
            await task.on_error(error_msg)
        
        finally:
            # Call finish hook
            await task.on_finish()

    def _run_task_wrapper(self, task_uuid: str, task_context: str | None = None) -> None:
        """Wrapper to run task in asyncio event loop."""
        task = self.get_task_by_uuid(task_uuid)
        if not task:
            return
        
        try:
            # Create and run the task
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self._run_task(task, task_context))
            
        except Exception as e:
            self._printer.print(f"Error in task wrapper: {str(e)}")
        finally:
            try:
                loop.close()
            except Exception:
                pass

    def serialize_all_tasks(self) -> list[dict[str, Any]]:
        """
        Serialize all tasks in the scheduler to a list of dictionaries.
        """
        return serialize_tasks(self.get_tasks())

    def serialize_task(self, task_id: str) -> dict[str, Any] | None:
        """
        Serialize a specific task in the scheduler by UUID.
        Returns None if task is not found.
        """
        from framework.helpers.task_serialization import serialize_task
        
        task = self.get_task_by_uuid(task_id)
        if task:
            return serialize_task(task)
        return None
