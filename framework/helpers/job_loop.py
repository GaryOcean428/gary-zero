import asyncio
import time

from framework.helpers import errors, runtime
from framework.helpers.print_style import PrintStyle
from framework.helpers.task_scheduler import TaskScheduler

SLEEP_TIME = 60

keep_running = True
pause_time = 0


async def run_loop():
    while True:
        if runtime.is_development():
            # Signal to container that the job loop should be paused
            # if we are runing a development instance to avoid duble-running the jobs
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
        await asyncio.sleep(
            SLEEP_TIME
        )  # TODO! - if we lower it under 1min, it can run a 5min job multiple times in it's target minute


async def scheduler_tick():
    # Get the task scheduler instance and print detailed debug info
    scheduler = TaskScheduler.get()
    # Run the scheduler tick
    await scheduler.tick()


def pause_loop():
    global keep_running, pause_time
    keep_running = False
    pause_time = time.time()


def resume_loop():
    global keep_running, pause_time
    keep_running = True
    pause_time = 0
