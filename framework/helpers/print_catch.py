import asyncio
import io
import sys
from collections.abc import Awaitable, Callable
from typing import Any


def capture_prints_async(
    func: Callable[..., Awaitable[Any]], *args, **kwargs
) -> tuple[Awaitable[Any], Callable[[], str]]:
    # Create a StringIO object to capture the output
    captured_output = io.StringIO()
    original_stdout = sys.stdout

    # Define a function to get the current captured output
    def get_current_output() -> str:
        return captured_output.getvalue()

    async def wrapped_func() -> Any:
        try:
            # Redirect sys.stdout to the StringIO object
            sys.stdout = captured_output
            # Await the provided function
            return await func(*args, **kwargs)
        finally:
            # Restore the original sys.stdout
            sys.stdout = original_stdout

    # Return the wrapped awaitable and the output retriever
    return asyncio.create_task(wrapped_func()), get_current_output
