import asyncio
import time
from datetime import datetime, timedelta

from framework.helpers import errors, runtime
from framework.helpers.print_style import PrintStyle
from framework.helpers.task_scheduler import TaskScheduler

# Optimized sleep time - reduced from 60s to allow more frequent checking
# while preventing duplicate execution of scheduled tasks
SLEEP_TIME = 30  # Check every 30 seconds instead of 60
MIN_TASK_INTERVAL = 60  # Minimum interval between same task executions

keep_running = True
pause_time = 0
last_task_runs = {}  # Track last execution times to prevent duplicates


async def run_loop():
    """Optimized main job loop with duplicate prevention."""
    while True:
        if runtime.is_development():
            # Signal to container that the job loop should be paused
            # if we are running a development instance to avoid double-running the jobs
            try:
                await runtime.call_development_function(pause_loop)
            except Exception as e:
                PrintStyle().error(
                    "Failed to pause job loop by development instance: "
                    + errors.error_text(e)
                )
        
        if not keep_running and (time.time() - pause_time) > (SLEEP_TIME * 2):
            resume_loop()
        
        if keep_running:
            try:
                await scheduler_tick()
            except Exception as e:
                PrintStyle().error(errors.format_error(e))
        
        await asyncio.sleep(SLEEP_TIME)


async def scheduler_tick():
    """Enhanced scheduler tick with duplicate execution prevention."""
    global last_task_runs
    
    # Get the task scheduler instance
    scheduler = TaskScheduler.get()
    
    # Get due tasks and filter out recently executed ones
    due_tasks = []
    try:
        all_due_tasks = scheduler._tasks.get_due_tasks()
        current_time = time.time()
        
        for task in all_due_tasks:
            task_key = f"{task.name}:{task.uuid}"
            last_run = last_task_runs.get(task_key, 0)
            
            # Only include task if it hasn't run recently
            if (current_time - last_run) >= MIN_TASK_INTERVAL:
                due_tasks.append(task)
                last_task_runs[task_key] = current_time
            else:
                # Log skipped duplicate
                PrintStyle().print(
                    f"Skipping recently executed task: {task.name} "
                    f"(last run {int(current_time - last_run)}s ago)"
                )
        
        # Clean up old entries (older than 10 minutes)
        cleanup_time = current_time - 600
        last_task_runs = {
            k: v for k, v in last_task_runs.items() 
            if v > cleanup_time
        }
        
    except Exception as e:
        PrintStyle().error(f"Error getting due tasks: {errors.error_text(e)}")
        return
    
    # Execute filtered due tasks
    if due_tasks:
        PrintStyle().print(f"Running {len(due_tasks)} due tasks")
        
        for task in due_tasks:
            try:
                PrintStyle().print(f"Executing task: {task.name}")
                await scheduler._run_task(task)
            except Exception as e:
                PrintStyle().error(
                    f"Error executing task {task.name}: {errors.error_text(e)}"
                )
    
    # Run the original scheduler tick for any additional processing
    try:
        await scheduler.tick()
    except Exception as e:
        PrintStyle().error(f"Scheduler tick error: {errors.error_text(e)}")


def pause_loop():
    global keep_running, pause_time
    keep_running = False
    pause_time = time.time()


def resume_loop():
    global keep_running, pause_time
    keep_running = True
    pause_time = 0
