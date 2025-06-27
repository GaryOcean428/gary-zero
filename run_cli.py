import asyncio
import os
import sys
import threading

from ansio import application_keypad
from ansio.input import InputEvent, get_input_event

from agent import AgentContext, UserMessage
from framework.helpers.dotenv import load_dotenv
from framework.helpers.print_style import PrintStyle
from framework.helpers.timed_input import timeout_input
from initialize import initialize_agent

_input_lock = threading.Lock()


class GlobalState:
    """Container for shared state to avoid global variables."""
    def __init__(self):
        self.context: AgentContext = None
        self.lock = threading.Lock()


# Global state instance
_state = GlobalState()


# Main conversation loop
async def chat(agent_context: AgentContext):

    # start the conversation loop
    while True:
        # ask user for message
        with _input_lock:
            # how long the agent is willing to wait
            timeout = agent_context.agent0.get_data("timeout")
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
                user_input = timeout_input(
                    "> ", timeout
                )  # Wait for input with timeout
                if not user_input:
                    user_input = ""
                    PrintStyle(font_color="white", padding=False, log_only=True).print(
                        f"> [timeout] {user_input}"
                    )
                else:
                    PrintStyle(
                        font_color="white", padding=False, log_only=True
                    ).print(f"> {user_input}")

        # exit the conversation when the user types 'exit'
        if user_input.lower() == "e" or user_input.lower() == "exit":
            break

        # let the user wait when they type 'w'
        if user_input.lower() == "w" or user_input.lower() == "wait":
            continue

        # send message to agent0,
        # agent0 decides whether to use another agent or tool
        response = await agent_context.communicate(UserMessage(user_input, []))

        # print agent response
        PrintStyle(font_color="green", bold=True).print("\n" + response + "\n")


# User intervention during agent streaming
def intervention():
    """Handle user intervention during agent streaming"""
    if _state.context and _state.context.streaming_agent and not _state.context.paused:
        _state.context.paused = True  # stop agent streaming
        PrintStyle(
            background_color="#006621",
            font_color="white",
            bold=True,
            padding=True,
        ).print("User intervention ('e' to leave, empty to continue):")

        user_input = input("> ")
        PrintStyle(font_color="white", padding=False, log_only=True).print(
            f"> {user_input}"
        )
        if user_input.lower() == "e" or user_input.lower() == "exit":
            os._exit(0)  # exit the conversation when the user types 'exit'
        if user_input:
            _state.context.streaming_agent.intervention = UserMessage(
                user_input, []
            )

        _state.context.paused = False  # continue agent streaming


# Capture keyboard input to trigger user intervention
def capture_keys():
    """Capture keyboard input for intervention"""
    with application_keypad(sys.stdin):
        while True:
            event = get_input_event(timeout=1)
            if isinstance(event, InputEvent):
                if event.key.lower() == "i" and _state.context and _state.context.streaming_agent:
                    intervention()
                if event.key.lower() == "e":
                    os._exit(0)
                if event.key.lower() == "q":
                    os._exit(0)


def run():
    """Main entry point for CLI application"""
    PrintStyle.standard("Initializing framework...")

    # load env vars
    load_dotenv()

    # initialize context
    config = initialize_agent()
    _state.context = AgentContext(config)

    # keyboard capture in separate thread
    threading.Thread(target=capture_keys, daemon=True).start()

    # start the conversation
    asyncio.run(chat(_state.context))


if __name__ == "__main__":
    PrintStyle.standard(
        "!!! run_cli.py is now discontinued. run_ui.py serves as both UI and API endpoint !!!"
    )
    run()
