# Standard library imports
import asyncio
import logging

import framework.helpers.mcp_handler as mcp_helper

# Third-party imports
import models

# Local application imports
from agent import AgentConfig, ModelConfig
from framework.helpers import persist_chat, runtime
from framework.helpers.defer import DeferredTask
from framework.helpers.job_loop import run_loop as job_loop_run_loop
from framework.helpers.mcp_handler import initialize_mcp as mcp_init_servers
from framework.helpers.print_style import PrintStyle
from framework.helpers.settings import get_settings
from framework.helpers.settings.types import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


def initialize_agent():
    current_settings = get_settings()

    # Merge with defaults to ensure all required keys exist
    for key, value in DEFAULT_SETTINGS.items():
        if key not in current_settings:
            current_settings[key] = value

    # chat model from user settings
    chat_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["chat_model_provider"].upper()],
        name=current_settings["chat_model_name"],
        ctx_length=current_settings["chat_model_ctx_length"],
        vision=current_settings["chat_model_vision"],
        limit_requests=current_settings["chat_model_rl_requests"],
        limit_input=current_settings["chat_model_rl_input"],
        limit_output=current_settings["chat_model_rl_output"],
        kwargs=current_settings["chat_model_kwargs"],
    )

    # utility model from user settings
    utility_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["util_model_provider"].upper()],
        name=current_settings["util_model_name"],
        ctx_length=current_settings["util_model_ctx_length"],
        limit_requests=current_settings["util_model_rl_requests"],
        limit_input=current_settings["util_model_rl_input"],
        limit_output=current_settings["util_model_rl_output"],
        kwargs=current_settings["util_model_kwargs"],
    )
    # embedding model from user settings
    embedding_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["embed_model_provider"].upper()],
        name=current_settings["embed_model_name"],
        limit_requests=current_settings["embed_model_rl_requests"],
        kwargs=current_settings["embed_model_kwargs"],
    )
    # browser model from user settings
    browser_llm = ModelConfig(
        provider=models.ModelProvider[
            current_settings["browser_model_provider"].upper()
        ],
        name=current_settings["browser_model_name"],
        vision=current_settings["browser_model_vision"],
        kwargs=current_settings["browser_model_kwargs"],
    )
    # agent configuration
    config = AgentConfig(
        chat_model=chat_llm,
        utility_model=utility_llm,
        embeddings_model=embedding_llm,
        browser_model=browser_llm,
        mcp_servers=current_settings["mcp_servers"],
    )

    # update SSH and docker settings
    _set_runtime_config(config, current_settings)

    # update config with runtime args
    _args_override(config)

    # initialize MCP in deferred task to prevent blocking the main thread
    if not mcp_helper.MCPConfig.get_instance().is_initialized():
        try:
            mcp_helper.MCPConfig.update(config.mcp_servers)
        except (ValueError, RuntimeError) as e:
            error_msg = f"Failed to update MCP settings: {e}"
            # Log warning (context not available during initialization)
            PrintStyle(background_color="black", font_color="red", padding=True).print(
                error_msg
            )
            logger.warning("Failed to update MCP settings", exc_info=e)

    # return config object
    return config


def initialize_mcp() -> DeferredTask:
    """Initialize MCP servers in a deferred task."""

    async def deferred_initialize_mcp_async():
        current_settings = get_settings()

        # Merge with defaults to ensure all required keys exist
        for key, value in DEFAULT_SETTINGS.items():
            if key not in current_settings:
                current_settings[key] = value

        mcp_servers_config = current_settings.get("mcp_servers")
        if mcp_servers_config:
            # Run the synchronous mcp_init_servers in a separate thread to avoid blocking
            await asyncio.to_thread(mcp_init_servers, mcp_servers_config)

    return DeferredTask().start_task(deferred_initialize_mcp_async)


def initialize_chats() -> DeferredTask:
    """Initialize chat sessions in a deferred task."""

    async def initialize_chats_async():
        persist_chat.load_tmp_chats()

    return DeferredTask().start_task(initialize_chats_async)


def initialize_job_loop() -> DeferredTask:
    """Initialize the job loop in a deferred task."""
    return DeferredTask("JobLoop").start_task(job_loop_run_loop)


def _args_override(config):
    # update config with runtime args
    args = runtime.RuntimeState.get_instance().args
    for key, value in args.items():
        if hasattr(config, key):
            # conversion based on type of config[key]
            if isinstance(getattr(config, key), bool):
                value = value.lower().strip() == "true"
            elif isinstance(getattr(config, key), int):
                value = int(value)
            elif isinstance(getattr(config, key), float):
                value = float(value)
            elif isinstance(getattr(config, key), str):
                value = str(value)
            else:
                error_msg = (
                    f"Unsupported argument type for '{key}': "
                    f"{type(getattr(config, key)).__name__}"
                )
                raise TypeError(error_msg)

            setattr(config, key, value)


def _set_runtime_config(config: AgentConfig, settings_data: dict) -> None:
    """Update runtime configuration from settings.

    Args:
        config: Agent configuration to update
        settings_data: Settings data containing runtime config
    """
    runtime_config = settings_data.get("runtime_config", {})
    for key, value in runtime_config.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Docker configuration is handled elsewhere in the codebase
