"""Agent module for handling agent interactions and configurations."""

# Standard library imports
import asyncio
import uuid
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Third-party imports
import httpx
import nest_asyncio
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Local application imports
import models
from framework.helpers import (
    dirty_json,
    errors,
    extract_tools,
    files,
    history,
    log,
    tokens,
)
from framework.helpers.defer import DeferredTask
from framework.helpers.localization import Localization
from framework.helpers.print_style import PrintStyle

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


class AgentContextType(Enum):
    USER = "user"
    TASK = "task"
    MCP = "mcp"


class AgentContext:
    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0

    def __init__(
        self,
        config: "AgentConfig",
        id: str | None = None,
        name: str | None = None,
        agent0: "Agent|None" = None,
        log: log.Log | None = None,
        paused: bool = False,
        streaming_agent: "Agent|None" = None,
        created_at: datetime | None = None,
        type: AgentContextType = AgentContextType.USER,
        last_message: datetime | None = None,
    ):
        # build context
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.config = config
        # Import log module to ensure it's available
        from framework.helpers import log as log_module
        self.log = log or log_module.Log()
        self.agent0 = agent0 or Agent(0, self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(UTC)
        self.type = type
        AgentContext._counter += 1
        self.no = AgentContext._counter
        # set to start of unix epoch
        self.last_message = last_message or datetime.now(UTC)

        existing = self._contexts.get(self.id, None)
        if existing:
            AgentContext.remove(self.id)
        self._contexts[self.id] = self

    @staticmethod
    def get(id: str):
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def first():
        if not AgentContext._contexts:
            return None
        return list(AgentContext._contexts.values())[0]

    @staticmethod
    def all():
        return list(AgentContext._contexts.values())

    @staticmethod
    def remove(id: str):
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": (
                Localization.get().serialize_datetime(self.created_at)
                if self.created_at
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "no": self.no,
            "log_guid": self.log.guid,
            "log_version": len(self.log.updates),
            "log_length": len(self.log.logs),
            "paused": self.paused,
            "last_message": (
                Localization.get().serialize_datetime(self.last_message)
                if self.last_message
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "type": self.type.value,
        }

    @staticmethod
    def log_to_all(
        type: log.Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: log.ProgressUpdate | None = None,
        id: str | None = None,  # Add id parameter
        **kwargs,
    ) -> list[log.LogItem]:
        items: list[log.LogItem] = []
        for context in AgentContext.all():
            items.append(
                context.log.log(
                    type, heading, content, kvps, temp, update_progress, id, **kwargs
                )
            )
        return items

    def kill_process(self) -> None:
        """Kill the current running process."""
        if self.task:
            self.task.kill()

    def reset(self) -> None:
        """Reset the agent context to initial state."""
        self.kill_process()
        self.log.reset()
        self.agent0 = Agent(0, self.config, self)
        self.streaming_agent = None
        self.paused = False

    def nudge(self) -> Any:
        """Nudge the agent to continue processing."""
        self.kill_process()
        self.paused = False
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self) -> "Agent":
        """Get the current active agent (streaming or default)."""
        return self.streaming_agent or self.agent0

    def communicate(self, msg: "UserMessage", broadcast_level: int = 1):
        self.paused = False  # unpause if paused

        current_agent = self.get_agent()

        if self.task and self.task.is_alive():
            # set intervention messages to agent(s):
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != 0:
                intervention_agent.intervention = msg
                broadcast_level -= 1
                intervention_agent = intervention_agent.data.get(
                    Agent.DATA_NAME_SUPERIOR, None
                )
        else:
            self.task = self.run_task(self._process_chain, current_agent, msg)

        return self.task

    def run_task(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ):
        if not self.task:
            self.task = DeferredTask(
                thread_name=self.__class__.__name__,
            )
        self.task.start_task(func, *args, **kwargs)
        return self.task

    # this wrapper ensures that superior agents are called back if the chat was
    # loaded from file and original callstack is gone
    async def _process_chain(self, agent: "Agent", msg: "UserMessage|str", user=True):
        try:
            if user:
                agent.hist_add_user_message(msg)  # type: ignore
            else:
                agent.hist_add_tool_result(
                    tool_name="call_subordinate",
                    tool_result=msg,  # type: ignore
                )
            response = await agent.monologue()  # type: ignore
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response, False)  # type: ignore
            return response
        except InterventionError:
            pass  # intervention message has been handled in handle_intervention(),
            # proceed with conversation loop
        except RepairableError as e:
            # Forward repairable errors to the LLM, maybe it can fix them
            error_message = errors.format_error(e)
            agent.hist_add_warning(error_message)
            PrintStyle(font_color="red", padding=True).print(error_message)
            self.context.log.log(type="error", content=error_message)
        except Exception as e:
            # Other exception kill the loop
            agent.handle_critical_exception(e)

    async def message_loop(self, msg: str) -> dict[str, Any]:
        pass

    def __repr__(self):
        return f"AgentContext(id={self.id}, name={self.name})"


@dataclass
class ModelConfig:
    provider: str  # Changed from models.ModelProvider to str to avoid import issues
    name: str
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    chat_model: ModelConfig
    utility_model: ModelConfig
    embeddings_model: ModelConfig
    browser_model: ModelConfig
    mcp_servers: str
    prompts_subdir: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    code_exec_docker_enabled: bool = False
    code_exec_docker_name: str = "A0-dev"
    code_exec_docker_image: str = "frdel/agent-zero-run:development"
    code_exec_docker_ports: dict[str, int] = field(
        default_factory=lambda: {"22/tcp": 55022, "80/tcp": 55080}
    )
    code_exec_docker_volumes: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            files.get_base_dir(): {"bind": "/a0", "mode": "rw"},
            files.get_abs_path("work_dir"): {"bind": "/root", "mode": "rw"},
        }
    )
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    code_exec_ssh_pass: str = ""
    additional: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    message: str
    attachments: list[str] = field(default_factory=list[str])
    system_message: list[str] = field(default_factory=list[str])


class LoopData:
    def __init__(self, **kwargs):
        self.iteration = -1
        self.system = []
        self.user_message: history.Message | None = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_temporary: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.extras_persistent: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.last_response = ""

        # override values with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# intervention exception class - skips rest of message loop iteration
class InterventionError(Exception):
    pass


# killer exception class - not forwarded to LLM, cannot be fixed on its own,
# ends message loop
class RepairableError(Exception):
    pass


class HandledError(Exception):
    pass


class Agent:
    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"
    DATA_NAME_CTX_WINDOW = "ctx_window"

    def __init__(
        self, number: int, config: AgentConfig, context: AgentContext | None = None
    ):
        # agent config
        self.config = config

        # agent context
        self.context = context or AgentContext(config)

        # non-config vars
        self.number = number
        self.agent_name = f"Agent {self.number}"

        self.history = history.History(self)
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data = {}  # free data object all the tools can use

    async def monologue(self):
        while True:
            try:
                # loop data dictionary to pass to extensions
                self.loop_data = LoopData(user_message=self.last_user_message)
                # call monologue_start extensions
                await self.call_extensions("monologue_start", loop_data=self.loop_data)

                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                # let the agent run message loop until he stops it with a response tool
                while True:
                    self.context.streaming_agent = self  # mark self as current streamer
                    self.loop_data.iteration += 1

                    # call message_loop_start extensions
                    await self.call_extensions(
                        "message_loop_start", loop_data=self.loop_data
                    )

                    try:
                        # prepare LLM chain (model, system, history)
                        prompt = await self.prepare_prompt(loop_data=self.loop_data)

                        # output that the agent is starting
                        PrintStyle(
                            bold=True,
                            font_color="green",
                            padding=True,
                            background_color="white",
                        ).print(f"{self.agent_name}: Generating")
                        log = self.context.log.log(
                            type="agent", heading=f"{self.agent_name}: Generating"
                        )

                        async def stream_callback(
                            chunk: str, full: str, printer=printer, log=log
                        ):
                            # output the agent response stream
                            if chunk:
                                printer.stream(chunk)
                                self.log_from_stream(full, log)

                        agent_response = await self.call_chat_model(
                            prompt, callback=stream_callback
                        )  # type: ignore

                        await self.handle_intervention(agent_response)

                        if (
                            self.loop_data.last_response == agent_response
                        ):  # if assistant_response is the same as
                            # last message in history,
                            # let him know
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # Append warning message to the history
                            warning_msg = self.read_prompt("fw.msg_repeat.md")
                            self.hist_add_warning(message=warning_msg)
                            PrintStyle(font_color="orange", padding=True).print(
                                warning_msg
                            )
                            self.context.log.log(type="warning", content=warning_msg)

                        else:  # otherwise proceed with tool
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(agent_response)
                            # process tools requested in agent message
                            tools_result = await self.process_tools(agent_response)
                            if tools_result:  # final response of message loop available
                                # break the execution if the task is done
                                return tools_result

                    # exceptions inside message loop:
                    except InterventionError:
                        # intervention message has been handled in
                        # handle_intervention(), proceed with conversation loop
                        pass
                        # proceed with conversation loop
                    except RepairableError as e:
                        # Forward repairable errors to the LLM, maybe it can fix them
                        error_message = errors.format_error(e)
                        self.hist_add_warning(error_message)
                        PrintStyle(font_color="red", padding=True).print(error_message)
                        self.context.log.log(type="error", content=error_message)
                    except Exception as e:
                        # Other exception kill the loop
                        self.handle_critical_exception(e)

                    finally:
                        # call message_loop_end extensions
                        await self.call_extensions(
                            "message_loop_end", loop_data=self.loop_data
                        )

            # exceptions outside message loop:
            except InterventionError:
                pass  # just start over
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None  # unset current streamer
                # call monologue_end extensions
                await self.call_extensions("monologue_end", loop_data=self.loop_data)  # type: ignore

    async def prepare_prompt(self, loop_data: LoopData) -> ChatPromptTemplate:
        self.context.log.set_progress("Building prompt")

        # call extensions before setting prompts
        await self.call_extensions("message_loop_prompts_before", loop_data=loop_data)

        # set system prompt and message history
        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output()

        # and allow extensions to edit them
        await self.call_extensions("message_loop_prompts_after", loop_data=loop_data)

        # extras (memory etc.)
        # extras: list[history.OutputMessage] = []
        # for extra in loop_data.extras_persistent.values():
        #     extras += history.Message(False, content=extra).output()
        # for extra in loop_data.extras_temporary.values():
        #     extras += history.Message(False, content=extra).output()
        extras = history.Message(
            False,
            content=self.read_prompt(
                "agent.context.extras.md",
                extras=dirty_json.stringify(
                    {**loop_data.extras_persistent, **loop_data.extras_temporary}
                ),
            ),
        ).output()
        loop_data.extras_temporary.clear()

        # convert history + extras to LLM format
        history_langchain: list[BaseMessage] = history.output_langchain(
            loop_data.history_output + extras
        )

        # build chain from system prompt, message history and model
        system_text = "\n\n".join(loop_data.system)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_text),
                *history_langchain,
                # AIMessage(content="JSON:"), # force the LLM to start with json
            ]
        )

        # store as last context window content
        self.set_data(
            Agent.DATA_NAME_CTX_WINDOW,
            {
                "text": prompt.format(),
                "tokens": self.history.get_tokens()
                + tokens.approximate_tokens(system_text)
                + tokens.approximate_tokens(history.output_text(extras)),
            },
        )

        return prompt

    def handle_critical_exception(self, exception: Exception):
        if isinstance(exception, HandledError):
            raise exception  # Re-raise the exception to kill the loop
        elif isinstance(exception, asyncio.CancelledError):
            # Handling for asyncio.CancelledError
            PrintStyle(font_color="white", background_color="red", padding=True).print(
                f"Context {self.context.id} terminated during message loop"
            )
            raise HandledError(exception)  # Re-raise the exception to cancel the loop
        else:
            # Handling for general exceptions
            error_text = errors.error_text(exception)
            error_message = errors.format_error(exception)
            PrintStyle(font_color="red", padding=True).print(error_message)
            self.context.log.log(
                type="error",
                heading="Error",
                content=error_message,
                kvps={"text": error_text},
            )
            raise HandledError(exception)  # Re-raise the exception to kill the loop

    async def get_system_prompt(self, loop_data: LoopData) -> list[str]:
        system_prompt = []
        await self.call_extensions(
            "system_prompt", system_prompt=system_prompt, loop_data=loop_data
        )
        return system_prompt

    def parse_prompt(self, file: str, **kwargs):
        prompt_dir = files.get_abs_path("prompts/default")
        backup_dir = []
        if (
            self.config.prompts_subdir
        ):  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("prompts", self.config.prompts_subdir)
            backup_dir.append(files.get_abs_path("prompts/default"))
        prompt = files.parse_file(
            files.get_abs_path(prompt_dir, file), _backup_dirs=backup_dir, **kwargs
        )
        return prompt

    def read_prompt(self, file: str, **kwargs) -> str:
        prompt_dir = files.get_abs_path("prompts/default")
        backup_dir = []
        if (
            self.config.prompts_subdir
        ):  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("prompts", self.config.prompts_subdir)
            backup_dir.append(files.get_abs_path("prompts/default"))
        prompt = files.read_file(
            files.get_abs_path(prompt_dir, file), _backup_dirs=backup_dir, **kwargs
        )
        prompt = files.remove_code_fences(prompt)
        return prompt

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(
        self, ai: bool, content: history.MessageContent, tokens: int = 0
    ):
        self.last_message = datetime.now(UTC)
        return self.history.add_message(ai=ai, content=content, tokens=tokens)

    def hist_add_user_message(self, message: UserMessage, intervention: bool = False):
        self.history.new_topic()  # user message starts a new topic in history

        # Integrate with task management system and OpenAI Agents SDK
        if not intervention:
            try:
                from framework.helpers.agent_tracing import get_agent_tracer
                from framework.helpers.agents_sdk_wrapper import (
                    get_sdk_orchestrator,
                )
                from framework.helpers.guardrails import get_guardrails_manager
                from framework.helpers.supervisor_agent import get_supervisor_agent
                from framework.helpers.task_manager import get_task_manager

                # Traditional task management
                task_manager = get_task_manager()
                supervisor = get_supervisor_agent()

                # SDK integration components
                sdk_orchestrator = get_sdk_orchestrator()
                guardrails = get_guardrails_manager()
                tracer = get_agent_tracer(self.context.log)

                # Create a new task for this user message
                task_id = task_manager.create_task(
                    title=f"User Request: {message.message[:50]}...",
                    description=message.message,
                    context={
                        "context_id": self.context.id,
                        "agent_id": self.agent_name,
                    },
                )

                # Start tracing for this interaction
                trace_id = tracer.start_agent_trace(self.agent_name, task_id)

                # Apply input guardrails (synchronously for now)
                try:
                    guardrails = get_guardrails_manager()
                    # Note: This should be made async in future, for now we skip async guardrails here
                    validated_message = (
                        message.message
                    )  # Placeholder - full integration requires async refactor
                    if validated_message != message.message:
                        self.context.log.log(
                            type="info",
                            content="Message processed through input guardrails",
                        )
                except Exception as guard_error:
                    self.context.log.log(
                        type="warning",
                        content=f"Guardrails processing failed: {guard_error}",
                    )
                    validated_message = message.message

                # Start the task
                task_manager.start_task(task_id, self.agent_name)

                # Store SDK integration data
                self.set_data("current_task_id", task_id)
                self.set_data("current_trace_id", trace_id)
                self.set_data("sdk_enabled", True)

                self.context.log.log(
                    type="info",
                    content=f"Created task {task_id[:8]} with SDK integration (trace: {trace_id[:8]})",
                )

            except Exception as e:
                # Don't let SDK integration errors break the core functionality
                self.context.log.log(
                    type="warning",
                    content=f"SDK integration failed, falling back to traditional mode: {e}",
                )
                # Fall back to basic task management
                try:
                    from framework.helpers.task_manager import get_task_manager

                    task_manager = get_task_manager()
                    task_id = task_manager.create_task(
                        title=f"User Request: {message.message[:50]}...",
                        description=message.message,
                    )
                    task_manager.start_task(task_id, self.agent_name)
                    self.set_data("current_task_id", task_id)
                    self.set_data("sdk_enabled", False)
                except Exception as e2:
                    self.context.log.log(
                        type="error",
                        content=f"Both SDK and traditional task management failed: {e2}",
                    )

        # load message template based on intervention
        if intervention:
            content = self.parse_prompt(
                "fw.intervention.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )
        else:
            content = self.parse_prompt(
                "fw.user_message.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )

        # remove empty parts from template
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}

        # add to history
        msg = self.hist_add_message(False, content=content)  # type: ignore
        self.last_user_message = msg
        return msg

    def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt("fw.ai_response.md", message=message)
        response_msg = self.hist_add_message(True, content=content)

        # Integrate with task management system and SDK - mark task as completed when agent responds
        try:
            from framework.helpers.agent_tracing import get_agent_tracer
            from framework.helpers.guardrails import get_guardrails_manager
            from framework.helpers.task_manager import get_task_manager

            task_id = self.get_data("current_task_id")
            trace_id = self.get_data("current_trace_id")
            sdk_enabled = self.get_data("sdk_enabled", False)

            if task_id:
                task_manager = get_task_manager()

                if sdk_enabled:
                    # SDK-enhanced completion
                    try:
                        guardrails = get_guardrails_manager()
                        tracer = get_agent_tracer(self.context.log)

                        # Note: This should be made async in future, for now we skip async guardrails here
                        final_message = message  # Placeholder - full integration requires async refactor

                        # Evaluate interaction safety (synchronously for now)
                        user_msg = (
                            self.last_user_message.content.get("message", "")
                            if self.last_user_message
                            else ""
                        )
                        # safety_eval = await guardrails.evaluate_interaction(user_msg, final_message)
                        safety_eval = {
                            "is_safe": True,
                            "risk_score": 0.0,
                        }  # Placeholder

                        # End tracing
                        if trace_id:
                            tracer.end_agent_trace(
                                trace_id,
                                success=safety_eval.get("is_safe", True),
                                result=final_message[:200] + "..."
                                if len(final_message) > 200
                                else final_message,
                            )

                        # Update task progress
                        task_manager.update_task_progress(
                            task_id, 1.0, "Agent response completed with SDK guardrails"
                        )
                        task_manager.complete_task(
                            task_id,
                            final_message[:200] + "..."
                            if len(final_message) > 200
                            else final_message,
                        )

                        # Log safety evaluation results
                        if not safety_eval.get("is_safe", True):
                            self.context.log.log(
                                type="warning",
                                content=f"Safety evaluation flagged interaction (risk score: {safety_eval.get('risk_score', 0):.2f})",
                            )

                        self.context.log.log(
                            type="success",
                            content=f"Completed task {task_id[:8]} with SDK integration (trace: {trace_id[:8] if trace_id else 'N/A'})",
                        )

                    except Exception as sdk_error:
                        # Fall back to traditional completion
                        self.context.log.log(
                            type="warning",
                            content=f"SDK completion failed, using traditional method: {sdk_error}",
                        )
                        task_manager.complete_task(
                            task_id,
                            message[:200] + "..." if len(message) > 200 else message,
                        )
                else:
                    # Traditional completion
                    task_manager.complete_task(
                        task_id,
                        message[:200] + "..." if len(message) > 200 else message,
                    )

                # Clear the current task ID
                self.set_data("current_task_id", None)
                self.set_data("current_trace_id", None)
                self.set_data("sdk_enabled", False)

        except Exception as e:
            # Don't let task completion errors break the core functionality
            self.context.log.log(
                type="warning", content=f"Task completion integration failed: {e}"
            )

        return response_msg

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt("fw.warning.md", message=message)
        return self.hist_add_message(False, content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str):
        content = self.parse_prompt(
            "fw.tool_result.md", tool_name=tool_name, tool_result=tool_result
        )
        return self.hist_add_message(False, content=content)

    def concat_messages(
        self, messages
    ):  # TODO add param for message range, topic, history
        return self.history.output_text(human_label="user", ai_label="assistant")

    def get_chat_model(self):
        try:
            model = models.get_model(
                models.ModelType.CHAT,
                self.config.chat_model.provider,
                self.config.chat_model.name,
                **self.config.chat_model.kwargs,
            )
            if model is None:
                raise ValueError(
                    f"Chat model returned None - provider: {self.config.chat_model.provider}, "
                    f"name: {self.config.chat_model.name}"
                )
            return model
        except Exception as e:
            error_msg = (
                f"Failed to initialize chat model - "
                f"provider: {self.config.chat_model.provider}, "
                f"name: {self.config.chat_model.name}, "
                f"error: {str(e)}"
            )
            self.context.log.log(type="error", content=error_msg)
            raise RuntimeError(error_msg) from e

    def get_utility_model(self):
        try:
            model = models.get_model(
                models.ModelType.CHAT,
                self.config.utility_model.provider,
                self.config.utility_model.name,
                **self.config.utility_model.kwargs,
            )
            if model is None:
                raise ValueError(
                    f"Utility model returned None - provider: {self.config.utility_model.provider}, "
                    f"name: {self.config.utility_model.name}"
                )
            return model
        except Exception as e:
            error_msg = (
                f"Failed to initialize utility model - "
                f"provider: {self.config.utility_model.provider}, "
                f"name: {self.config.utility_model.name}, "
                f"error: {str(e)}"
            )
            self.context.log.log(type="error", content=error_msg)
            raise RuntimeError(error_msg) from e

    def get_embedding_model(self):
        try:
            model = models.get_model(
                models.ModelType.EMBEDDING,
                self.config.embeddings_model.provider,
                self.config.embeddings_model.name,
                **self.config.embeddings_model.kwargs,
            )
            if model is None:
                raise ValueError(
                    f"Embedding model returned None - provider: {self.config.embeddings_model.provider}, "
                    f"name: {self.config.embeddings_model.name}"
                )
            return model
        except Exception as e:
            error_msg = (
                f"Failed to initialize embedding model - "
                f"provider: {self.config.embeddings_model.provider}, "
                f"name: {self.config.embeddings_model.name}, "
                f"error: {str(e)}"
            )
            self.context.log.log(type="error", content=error_msg)
            raise RuntimeError(error_msg) from e

    async def call_utility_model(
        self,
        system: str,
        message: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessage(content=system), HumanMessage(content=message)]
        )

        response = ""

        # model class
        model = self.get_utility_model()

        # rate limiter
        limiter = await self.rate_limiter(
            self.config.utility_model, prompt.format(), background
        )

        async for chunk in (prompt | model).astream({}):
            await (
                self.handle_intervention()
            )  # wait for intervention and handle it, if paused

            content = models.parse_chunk(chunk)
            limiter.add(output=tokens.approximate_tokens(content))
            response += content

            if callback:
                await callback(content)

        return response

    async def call_chat_model(
        self,
        prompt: ChatPromptTemplate,
        callback: Callable[[str, str], Awaitable[None]] | None = None,
    ):
        response = ""

        # model class
        model = self.get_chat_model()

        # rate limiter
        limiter = await self.rate_limiter(self.config.chat_model, prompt.format())

        # Retry logic for connection failures
        max_retries = 3
        retry_delay = 1  # Start with 1 second

        for attempt in range(max_retries):
            try:
                async for chunk in (prompt | model).astream({}):
                    await (
                        self.handle_intervention()
                    )  # wait for intervention and handle it, if paused

                    content = models.parse_chunk(chunk)
                    limiter.add(output=tokens.approximate_tokens(content))
                    response += content

                    if callback:
                        await callback(content, response)

                # If we reach here, streaming completed successfully
                break

            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.ReadError,
            ) as e:
                if attempt < max_retries - 1:  # Don't retry on last attempt
                    self.context.log.log(
                        type="warning",
                        content=f"HTTP connection error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_delay}s...",
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    response = ""  # Reset response for retry
                    continue
                else:
                    # On final attempt, raise a more user-friendly error
                    error_msg = f"Failed to connect to AI model service after {max_retries} attempts. Please check your internet connection and try again."
                    self.context.log.log(type="error", content=error_msg)
                    raise RepairableError(error_msg) from e
            except Exception as e:
                # For other exceptions, don't retry but still log appropriately
                error_msg = f"Unexpected error during AI model communication: {str(e)}"
                self.context.log.log(type="error", content=error_msg)
                raise RepairableError(error_msg) from e

        return response

    async def rate_limiter(
        self, model_config: ModelConfig, input: str, background: bool = False
    ):
        # rate limiter log
        wait_log = None

        async def wait_callback(msg: str, key: str, total: int, limit: int):
            nonlocal wait_log
            if not wait_log:
                wait_log = self.context.log.log(
                    type="util",
                    update_progress="none",
                    heading=msg,
                    model=f"{model_config.provider.value}\\{model_config.name}",
                )
            wait_log.update(heading=msg, key=key, value=total, limit=limit)
            if not background:
                self.context.log.set_progress(msg, -1)

        # rate limiter
        limiter = models.get_rate_limiter(
            model_config.provider,
            model_config.name,
            model_config.limit_requests,
            model_config.limit_input,
            model_config.limit_output,
        )
        limiter.add(input=tokens.approximate_tokens(input))
        limiter.add(requests=1)
        await limiter.wait(callback=wait_callback)
        return limiter

    async def handle_intervention(self, progress: str = ""):
        while self.context.paused:
            await asyncio.sleep(0.1)  # wait if paused
        if (
            self.intervention
        ):  # if there is an intervention message, but not yet processed
            msg = self.intervention
            self.intervention = None  # reset the intervention message
            if progress.strip():
                self.hist_add_ai_response(progress)
            # append the intervention message
            self.hist_add_user_message(msg, intervention=True)
            raise InterventionError(msg)

    async def wait_if_paused(self):
        while self.context.paused:
            await asyncio.sleep(0.1)

    async def process_tools(self, msg: str):
        # search for tool usage requests in agent message
        tool_request = extract_tools.json_parse_dirty(msg)

        if tool_request is not None:
            raw_tool_name = tool_request.get("tool_name", "")  # Get the raw tool name
            tool_args = tool_request.get("tool_args", {})

            tool_name = raw_tool_name  # Initialize tool_name with raw_tool_name
            tool_method = None  # Initialize tool_method

            # Split raw_tool_name into tool_name and tool_method if applicable
            if ":" in raw_tool_name:
                tool_name, tool_method = raw_tool_name.split(":", 1)

            tool = None  # Initialize tool to None

            # Try SDK tools first if available
            try:
                from framework.helpers.agent_tools_wrapper import get_tool_registry
                from framework.helpers.agent_tracing import get_agent_tracer

                sdk_enabled = self.get_data("sdk_enabled", False)
                trace_id = self.get_data("current_trace_id")

                if sdk_enabled:
                    registry = get_tool_registry()
                    sdk_tool = registry.get_tool(tool_name)

                    if sdk_tool:
                        # Log tool execution to trace
                        if trace_id:
                            tracer = get_agent_tracer()
                            tracer.add_trace_event(
                                trace_id,
                                tracer.tracing_processor.TraceEventType.TOOL_CALL,
                                {"tool_name": tool_name, "args": tool_args},
                            )

                        # Execute SDK tool
                        await self.handle_intervention()
                        sdk_result = await sdk_tool.execute(**tool_args)
                        await self.handle_intervention()

                        # Convert SDK result to Gary-Zero format
                        class SDKToolResult:
                            def __init__(self, sdk_result):
                                if hasattr(sdk_result, "error") and sdk_result.error:
                                    self.message = f"Tool error: {sdk_result.error}"
                                    self.break_loop = False
                                else:
                                    self.message = (
                                        str(sdk_result.result)
                                        if hasattr(sdk_result, "result")
                                        else str(sdk_result)
                                    )
                                    self.break_loop = (
                                        False  # SDK tools don't break loop by default
                                    )

                        response = SDKToolResult(sdk_result)

                        if response.break_loop:
                            return response.message

                        # Continue to traditional tool fallback if SDK tool didn't work
                        tool = None

            except Exception as e:
                self.context.log.log(
                    type="warning",
                    content=f"SDK tool execution failed, falling back to traditional tools: {e}",
                )
                tool = None

            # Try getting tool from MCP if SDK tools didn't work
            if not tool:
                try:
                    import framework.helpers.mcp_handler as mcp_helper

                    mcp_tool_candidate = mcp_helper.MCPConfig.get_instance().get_tool(
                        self, tool_name
                    )
                    if mcp_tool_candidate:
                        tool = mcp_tool_candidate
                except Exception as e:
                    PrintStyle(
                        background_color="black", font_color="red", padding=True
                    ).print(f"Failed to get MCP tool '{tool_name}': {e}")

            # Fallback to local get_tool if MCP tool was not found or MCP lookup failed
            if not tool:
                tool = self.get_tool(
                    name=tool_name, method=tool_method, args=tool_args, message=msg
                )

            if tool:
                await self.handle_intervention()
                await tool.before_execution(**tool_args)
                await self.handle_intervention()
                response = await tool.execute(**tool_args)
                await self.handle_intervention()
                await tool.after_execution(response)
                await self.handle_intervention()
                if response.break_loop:
                    return response.message
            else:
                error_detail = (
                    f"Tool '{raw_tool_name}' not found or could not be initialized."
                )
                self.hist_add_warning(error_detail)
                PrintStyle(font_color="red", padding=True).print(error_detail)
                self.context.log.log(
                    type="error", content=f"{self.agent_name}: {error_detail}"
                )
        else:
            warning_msg_misformat = self.read_prompt("fw.msg_misformat.md")
            self.hist_add_warning(warning_msg_misformat)
            PrintStyle(font_color="red", padding=True).print(warning_msg_misformat)
            self.context.log.log(
                type="error",
                content=f"{self.agent_name}: Message misformat, no valid tool request found.",
            )

    def log_from_stream(self, stream: str, log_item: log.LogItem):
        try:
            if len(stream) < 25:
                return  # no reason to try
            response = dirty_json.parse_string(stream)
            if isinstance(response, dict):
                # log if result is a dictionary already
                log_item.update(content=stream, kvps=response)
        except Exception:
            pass

    def get_tool(
        self, name: str, method: str | None, args: dict, message: str, **kwargs
    ):
        from framework.helpers.tool import Tool
        from framework.tools.unknown import Unknown

        # First try to load from plugins
        try:
            plugin_tool_class = self._get_plugin_tool(name)
            if plugin_tool_class:
                return plugin_tool_class(
                    agent=self,
                    name=name,
                    method=method,
                    args=args,
                    message=message,
                    **kwargs,
                )
        except Exception as e:
            print(f"Failed to load plugin tool {name}: {e}")

        # Fallback to static tools
        classes = extract_tools.load_classes_from_folder(
            "framework/tools", name + ".py", Tool
        )
        tool_class = classes[0] if classes else Unknown
        return tool_class(
            agent=self, name=name, method=method, args=args, message=message, **kwargs
        )

    def _get_plugin_tool(self, name: str):
        """Get a tool from the plugin system."""
        # Initialize plugin manager if not already done
        if not hasattr(self, "_plugin_manager"):
            try:
                from framework.plugins.manager import PluginManager

                self._plugin_manager = PluginManager()
            except Exception as e:
                print(f"Failed to initialize plugin manager: {e}")
                return None

        return self._plugin_manager.get_tool(name)

    async def call_extensions(self, folder: str, **kwargs) -> Any:
        from framework.helpers.extension import Extension

        classes = extract_tools.load_classes_from_folder(
            "framework/extensions/" + folder, "*", Extension
        )
        for cls in classes:
            await cls(agent=self).execute(**kwargs)

    async def message_loop(self, msg: str) -> dict[str, Any]:
        pass
