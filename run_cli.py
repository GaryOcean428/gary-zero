import asyncio
import os
import sys
import threading
import time

from ansio import application_keypad
from ansio.input import InputEvent, get_input_event

import framework.helpers.timed_input as timed_input
from agent import AgentContext, UserMessage
from initialize import initialize_agent
from framework.helpers.dotenv import load_dotenv
from framework.helpers.print_style import PrintStyle

_global_context: AgentContext = None  # type: ignore
_input_lock = threading.Lock()


# Main conversation loop
async def chat(agent_context: AgentContext):

    # start the conversation loop
    while True:
        # ask user for message
        with _input_lock:
            timeout = agent_context.agent0.get_data("timeout")  # how long the agent is willing to wait
            if not timeout:  # if agent wants to wait for user input forever
                PrintStyle(
                    background_color="#6C3483",
                    font_color="white",
                    bold=True,
                    padding=True,
                ).print("User message ('e' to leave):")
                if sys.platform != "win32":
                    pass  # this fixes arrow keys in terminal
                user_input = input("> ")
                PrintStyle(font_color="white", padding=False, log_only=True).print(
                    f"> {user_input}"
                )

            else:  # otherwise wait for user input with a timeout
                PrintStyle(
                    background_color="#6C3483",
                    font_color="white",
                    bold=True,
                    padding=True,
                ).print(f"User message ({timeout}s timeout, 'w' to wait, 'e' to leave):")
                if sys.platform != "win32":
                    pass  # this fixes arrow keys in terminal
                # user_input = timed_input("> ", timeout=timeout)
                user_input = timeout_input("> ", timeout=timeout)

                if not user_input:
                    user_input = agent_context.agent0.read_prompt("fw.msg_timeout.md")
                    PrintStyle(font_color="white", padding=False).stream(f"{user_input}")
                else:
                    user_input = user_input.strip()
                    if user_input.lower() == "w":  # the user needs more time
                        user_input = input("> ").strip()
                    PrintStyle(font_color="white", padding=False, log_only=True).print(
                        f"> {user_input}"
                    )

        # exit the conversation when the user types 'e'
        if user_input.lower() == "e":
            break

        # send message to agent0,
        assistant_response = await agent_context.communicate(UserMessage(user_input, [])).result()

        # print agent0 response
        PrintStyle(font_color="white", background_color="#1D8348", bold=True, padding=True).print(
            f"{agent_context.agent0.agent_name}: reponse:"
        )
        PrintStyle(font_color="white").print(f"{assistant_response}")


# User intervention during agent streaming
def intervention():
    if _global_context.streaming_agent and not _global_context.paused:
        _global_context.paused = True  # stop agent streaming
        PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print(
            "User intervention ('e' to leave, empty to continue):"
        )

        if sys.platform != "win32":
            pass  # this fixes arrow keys in terminal
        user_input = input("> ").strip()
        PrintStyle(font_color="white", padding=False, log_only=True).print(f"> {user_input}")

        if user_input.lower() == "e":
            os._exit(0)  # exit the conversation when the user types 'exit'
        if user_input:
            _global_context.streaming_agent.intervention = UserMessage(
                user_input, []
            )  # set intervention message if non-empty
        _global_context.paused = False  # continue agent streaming


# Capture keyboard input to trigger user intervention
def capture_keys():
    intervent = False
    while True:
        if intervent:
            intervention()
        intervent = False
        time.sleep(0.1)

        if _global_context.streaming_agent:
            # with raw_input, application_keypad, mouse_input:
            with _input_lock, application_keypad:
                event: InputEvent | None = get_input_event(timeout=0.1)
                if event and (event.shortcut.isalpha() or event.shortcut.isspace()):
                    intervent = True
                    continue


# User input with timeout
def timeout_input(prompt, timeout=10):
    return timed_input.timeout_input(prompt=prompt, timeout=timeout)


def run():
    global _global_context
    PrintStyle.standard("Initializing framework...")

    # load env vars
    load_dotenv()

    # initialize context
    config = initialize_agent()
    _global_context = AgentContext(config)

    # Start the key capture thread for user intervention during agent streaming
    threading.Thread(target=capture_keys, daemon=True).start()

    # start the chat
    asyncio.run(chat(_global_context))


if __name__ == "__main__":
    PrintStyle.standard(
        "!!! run_cli.py is now discontinued. run_ui.py serves as both UI and API endpoint !!!"
    )
    run()
