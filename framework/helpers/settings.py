import base64
import hashlib
import json
import re
import subprocess
from typing import Any, Literal, TypedDict

import models
from framework.helpers import runtime
from framework.helpers.print_style import PrintStyle

from . import dotenv, files, settings_manager
from .settings_types import DEFAULT_SETTINGS, Settings

# Import MCPConfig at module level to avoid cell variable issues
try:
    from framework.helpers.mcp_handler import MCPConfig
except ImportError:
    MCPConfig = None

# Constants for repeated descriptions
MODEL_PARAMS_DESCRIPTION = (
    """Any other parameters supported by the model. Format is KEY=VALUE """
    """on individual lines, just like .env file."""
)


class FieldOption(TypedDict):
    value: str
    label: str


class SettingsField(TypedDict, total=False):
    id: str
    title: str
    description: str
    type: Literal["text", "number", "select", "range", "textarea", "password", "switch", "button"]
    value: Any
    min: float
    max: float
    step: float
    hidden: bool
    options: list[FieldOption]


class SettingsSection(TypedDict, total=False):
    id: str
    title: str
    description: str
    fields: list[SettingsField]
    tab: str  # Indicates which tab this section belongs to


class SettingsOutput(TypedDict):
    sections: list[SettingsSection]


class PartialSettings(Settings, total=False):
    pass


PASSWORD_PLACEHOLDER = "****PSWD****"

SETTINGS_FILE = files.get_abs_path("tmp/settings.json")


def convert_out(settings: Settings) -> SettingsOutput:
    from models import ModelProvider

    # main model section
    chat_model_fields: list[SettingsField] = []
    chat_model_fields.append(
        {
            "id": "chat_model_provider",
            "title": "Chat model provider",
            "description": "Select provider for main chat model used by Gary-Zero",
            "type": "select",
            "value": settings["chat_model_provider"],
            "options": [{"value": p.name, "label": p.value} for p in ModelProvider],
        }
    )
    chat_model_fields.append(
        {
            "id": "chat_model_name",
            "title": "Chat model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["chat_model_name"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_ctx_length",
            "title": "Chat model context length",
            "description": (
                "Maximum number of tokens in the context window for LLM. System "
                "prompt, chat history, RAG and response all count towards this limit."
            ),
            "type": "number",
            "value": settings["chat_model_ctx_length"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_ctx_history",
            "title": "Context window space for chat history",
            "description": (
                "Portion of context window dedicated to chat history visible to the agent. "
                "Chat history will automatically be optimized to fit. Smaller size will "
                "result in shorter and more summarized history. The remaining space will "
                "be used for system prompt, RAG and response."
            ),
            "type": "range",
            "min": 0.01,
            "max": 1,
            "step": 0.01,
            "value": settings["chat_model_ctx_history"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_vision",
            "title": "Supports Vision",
            "description": (
                "Models capable of Vision can for example natively see the content of "
                "image attachments."
            ),
            "type": "switch",
            "value": settings["chat_model_vision"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_requests",
            "title": "Requests per minute limit",
            "description": (
                "Limits the number of requests per minute to the chat model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["chat_model_rl_requests"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": (
                "Limits the number of input tokens per minute to the chat model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["chat_model_rl_input"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_rl_output",
            "title": "Output tokens per minute limit",
            "description": (
                "Limits the number of output tokens per minute to the chat model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["chat_model_rl_output"],
        }
    )

    chat_model_fields.append(
        {
            "id": "chat_model_kwargs",
            "title": "Chat model additional parameters",
            "description": MODEL_PARAMS_DESCRIPTION,
            "type": "textarea",
            "value": _dict_to_env(settings["chat_model_kwargs"]),
        }
    )

    chat_model_section: SettingsSection = {
        "id": "chat_model",
        "title": "Chat Model",
        "description": "Selection and settings for main chat model used by Gary-Zero",
        "fields": chat_model_fields,
        "tab": "agent",
    }

    # main model section
    util_model_fields: list[SettingsField] = []
    util_model_fields.append(
        {
            "id": "util_model_provider",
            "title": "Utility model provider",
            "description": "Select provider for utility model used by the framework",
            "type": "select",
            "value": settings["util_model_provider"],
            "options": [{"value": p.name, "label": p.value} for p in ModelProvider],
        }
    )
    util_model_fields.append(
        {
            "id": "util_model_name",
            "title": "Utility model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["util_model_name"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_requests",
            "title": "Requests per minute limit",
            "description": (
                "Limits the number of requests per minute to the utility model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["util_model_rl_requests"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": (
                "Limits the number of input tokens per minute to the utility model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["util_model_rl_input"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_rl_output",
            "title": "Output tokens per minute limit",
            "description": (
                "Limits the number of output tokens per minute to the utility model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["util_model_rl_output"],
        }
    )

    util_model_fields.append(
        {
            "id": "util_model_kwargs",
            "title": "Utility model additional parameters",
            "description": (
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            ),
            "type": "textarea",
            "value": _dict_to_env(settings["util_model_kwargs"]),
        }
    )

    util_model_section: SettingsSection = {
        "id": "util_model",
        "title": "Utility model",
        "description": (
            "Smaller, cheaper, faster model for handling utility tasks like "
            "organizing memory, preparing prompts, summarizing."
        ),
        "fields": util_model_fields,
        "tab": "agent",
    }

    # embedding model section
    embed_model_fields: list[SettingsField] = []
    embed_model_fields.append(
        {
            "id": "embed_model_provider",
            "title": "Embedding model provider",
            "description": "Select provider for embedding model used by the framework",
            "type": "select",
            "value": settings["embed_model_provider"],
            "options": [{"value": p.name, "label": p.value} for p in ModelProvider],
        }
    )
    embed_model_fields.append(
        {
            "id": "embed_model_name",
            "title": "Embedding model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["embed_model_name"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_rl_requests",
            "title": "Requests per minute limit",
            "description": (
                "Limits the number of requests per minute to the embedding model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["embed_model_rl_requests"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_rl_input",
            "title": "Input tokens per minute limit",
            "description": (
                "Limits the number of input tokens per minute to the embedding model. "
                "Waits if the limit is exceeded. Set to 0 to disable rate limiting."
            ),
            "type": "number",
            "value": settings["embed_model_rl_input"],
        }
    )

    embed_model_fields.append(
        {
            "id": "embed_model_kwargs",
            "title": "Embedding model additional parameters",
            "description": (
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            ),
            "type": "textarea",
            "value": _dict_to_env(settings["embed_model_kwargs"]),
        }
    )

    embed_model_section: SettingsSection = {
        "id": "embed_model",
        "title": "Embedding Model",
        "description": "Settings for the embedding model used by Gary-Zero.",
        "fields": embed_model_fields,
        "tab": "agent",
    }

    # embedding model section
    browser_model_fields: list[SettingsField] = []
    browser_model_fields.append(
        {
            "id": "browser_model_provider",
            "title": "Web Browser model provider",
            "description": """The provider for the browser model.
    This determines which API or service to use for browser operations.""",
            "type": "select",
            "value": settings["browser_model_provider"],
            "options": [{"value": p.name, "label": p.value} for p in ModelProvider],
        }
    )
    browser_model_fields.append(
        {
            "id": "browser_model_name",
            "title": "Web Browser model name",
            "description": "Exact name of model from selected provider",
            "type": "text",
            "value": settings["browser_model_name"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_vision",
            "title": "Use Vision",
            "description": (
                "Models capable of Vision can use it to analyze web pages from screenshots. "
                "Increases quality but also token usage."
            ),
            "type": "switch",
            "value": settings["browser_model_vision"],
        }
    )

    browser_model_fields.append(
        {
            "id": "browser_model_kwargs",
            "title": "Web Browser model additional parameters",
            "description": (
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            ),
            "type": "textarea",
            "value": _dict_to_env(settings["browser_model_kwargs"]),
        }
    )

    browser_model_section: SettingsSection = {
        "id": "browser_model",
        "title": "Web Browser Model",
        "description": (
            "Settings for the web browser model. Gary-Zero uses "
            "<a href='https://github.com/browser-use/browser-use' target='_blank'>browser-use</a> "
            "agentic framework to handle web interactions."
        ),
        "fields": browser_model_fields,
        "tab": "agent",
    }

    # # Memory settings section
    # memory_fields: list[SettingsField] = []
    # memory_fields.append(
    #     {
    #         "id": "memory_settings",
    #         "title": "Memory Settings",
    #         "description": "<settings for memory>",
    #         "type": "text",
    #         "value": "",
    #     }
    # )

    # memory_section: SettingsSection = {
    #     "id": "memory",
    #     "title": "Memory Settings",
    #     "description": "<settings for memory management here>",
    #     "fields": memory_fields,
    # }

    # basic auth section
    auth_fields: list[SettingsField] = []

    auth_fields.append(
        {
            "id": "auth_login",
            "title": "UI Login",
            "description": "Set user name for web UI",
            "type": "text",
            "value": dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or "",
        }
    )

    auth_fields.append(
        {
            "id": "auth_password",
            "title": "UI Password",
            "description": "Set user password for web UI",
            "type": "password",
            "value": (
                PASSWORD_PLACEHOLDER if dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD) else ""
            ),
        }
    )

    if runtime.is_dockerized():
        auth_fields.append(
            {
                "id": "root_password",
                "title": "root Password",
                "description": (
                    "Change linux root password in docker container. This password can be "
                    "used for SSH access. Original password was randomly generated during setup."
                ),
                "type": "password",
                "value": "",
            }
        )

    auth_section: SettingsSection = {
        "id": "auth",
        "title": "Authentication",
        "description": "Settings for authentication to use Gary-Zero Web UI.",
        "fields": auth_fields,
        "tab": "external",
    }

    # api keys model section
    api_keys_fields: list[SettingsField] = []
    api_keys_fields.append(_get_api_key_field(settings, "openai", "OpenAI API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "anthropic", "Anthropic API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "chutes", "Chutes API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "deepseek", "DeepSeek API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "google", "Google API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "groq", "Groq API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "huggingface", "HuggingFace API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "meta", "Meta API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "mistralai", "MistralAI API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "openrouter", "OpenRouter API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "perplexity", "Perplexity API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "sambanova", "Sambanova API Key"))
    api_keys_fields.append(_get_api_key_field(settings, "xai", "xAI API Key"))

    api_keys_section: SettingsSection = {
        "id": "api_keys",
        "title": "API Keys",
        "description": "API keys for model providers and services used by Gary-Zero.",
        "fields": api_keys_fields,
        "tab": "external",
    }

    # Agent config section
    agent_fields: list[SettingsField] = []

    agent_fields.append(
        {
            "id": "agent_prompts_subdir",
            "title": "Prompts Subdirectory",
            "description": """The name of the model to use for embeddings.
    This is used for vector storage and retrieval.""",
            "type": "select",
            "value": settings["agent_prompts_subdir"],
            "options": [
                {"value": subdir, "label": subdir} for subdir in files.get_subdirectories("prompts")
            ],
        }
    )

    agent_fields.append(
        {
            "id": "agent_memory_subdir",
            "title": "Memory Subdirectory",
            "description": (
                "Subdirectory of /memory folder to use for agent memory storage. "
                "Used to separate memory storage between different instances."
            ),
            "type": "text",
            "value": settings["agent_memory_subdir"],
            # "options": [
            #     {"value": subdir, "label": subdir}
            #     for subdir in files.get_subdirectories("memory", exclude="embeddings")
            # ],
        }
    )

    agent_fields.append(
        {
            "id": "agent_knowledge_subdir",
            "title": "Knowledge subdirectory",
            "description": (
                "Subdirectory of /knowledge folder to use for agent knowledge import. "
                "'default' subfolder is always imported and contains framework knowledge."
            ),
            "type": "select",
            "value": settings["agent_knowledge_subdir"],
            "options": [
                {"value": subdir, "label": subdir}
                for subdir in files.get_subdirectories("knowledge", exclude="default")
            ],
        }
    )

    agent_section: SettingsSection = {
        "id": "agent",
        "title": "Agent Config",
        "description": "Agent parameters.",
        "fields": agent_fields,
        "tab": "agent",
    }

    dev_fields: list[SettingsField] = []

    if runtime.is_development():
        # dev_fields.append(
        #     {
        #         "id": "rfc_auto_docker",
        #         "title": "RFC Auto Docker Management",
        #         "description": "Automatically create dockerized instance of A0 for RFCs using this instance's code base and, settings and .env.",
        #         "type": "text",
        #         "value": settings["rfc_auto_docker"],
        #     }
        # )

        dev_fields.append(
            {
                "id": "rfc_url",
                "title": "RFC Destination URL",
                "description": (
                    "URL of dockerized A0 instance for remote function calls. "
                    "Do not specify port here."
                ),
                "type": "text",
                "value": settings["rfc_url"],
            }
        )

    dev_fields.append(
        {
            "id": "rfc_password",
            "title": "RFC Password",
            "description": """The name of the model to use for browser operations.
    This is used for browser automation tasks.""",
            "type": "password",
            "value": (
                PASSWORD_PLACEHOLDER if dotenv.get_dotenv_value(dotenv.KEY_RFC_PASSWORD) else ""
            ),
        }
    )

    if runtime.is_development():
        dev_fields.append(
            {
                "id": "rfc_port_http",
                "title": "RFC HTTP port",
                "description": "HTTP port for dockerized instance of A0.",
                "type": "text",
                "value": settings["rfc_port_http"],
            }
        )

        dev_fields.append(
            {
                "id": "rfc_port_ssh",
                "title": "RFC SSH port",
                "description": "SSH port for dockerized instance of A0.",
                "type": "text",
                "value": settings["rfc_port_ssh"],
            }
        )

    dev_section: SettingsSection = {
        "id": "dev",
        "title": "Development",
        "description": (
            "Parameters for A0 framework development. RFCs (remote function calls) are used "
            "to call functions on another A0 instance. You can develop and debug A0 natively "
            "on your local system while redirecting some functions to A0 instance in docker. "
            "This is crucial for development as A0 needs to run in standardized environment "
            "to support all features."
        ),
        "fields": dev_fields,
        "tab": "developer",
    }

    # Speech to text section
    stt_fields: list[SettingsField] = []

    stt_fields.append(
        {
            "id": "stt_model_size",
            "title": "Model Size",
            "description": "Select the speech recognition model size",
            "type": "select",
            "value": settings["stt_model_size"],
            "options": [
                {"value": "tiny", "label": "Tiny (39M, English)"},
                {"value": "base", "label": "Base (74M, English)"},
                {"value": "small", "label": "Small (244M, English)"},
                {"value": "medium", "label": "Medium (769M, English)"},
                {"value": "large", "label": "Large (1.5B, Multilingual)"},
                {"value": "turbo", "label": "Turbo (Multilingual)"},
            ],
        }
    )

    stt_fields.append(
        {
            "id": "stt_language",
            "title": "Language Code",
            "description": "Language code (e.g. en, fr, it)",
            "type": "text",
            "value": settings["stt_language"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_silence_threshold",
            "title": "Silence threshold",
            "description": "Silence detection threshold. Lower values are more sensitive.",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["stt_silence_threshold"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_silence_duration",
            "title": "Silence duration (ms)",
            "description": (
                "Duration of silence before the server considers speaking to have ended."
            ),
            "type": "text",
            "value": settings["stt_silence_duration"],
        }
    )

    stt_fields.append(
        {
            "id": "stt_waiting_timeout",
            "title": "Waiting timeout (ms)",
            "description": "Duration before the server closes the microphone.",
            "type": "text",
            "value": settings["stt_waiting_timeout"],
        }
    )

    stt_section: SettingsSection = {
        "id": "stt",
        "title": "Speech to Text",
        "description": ("Voice transcription preferences and server turn detection settings."),
        "fields": stt_fields,
        "tab": "agent",
    }

    # MCP section
    mcp_client_fields: list[SettingsField] = []

    mcp_client_fields.append(
        {
            "id": "mcp_servers_config",
            "title": "MCP Servers Configuration",
            "description": "External MCP servers can be configured here.",
            "type": "button",
            "value": "Open",
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_servers",
            "title": "MCP Servers",
            "description": (
                "(JSON list of) >> RemoteServer <<: [name, url, headers, timeout (opt), "
                "sse_read_timeout (opt), disabled (opt)] / >> Local Server <<: [name, "
                "command, args, env, encoding (opt), encoding_error_handler (opt), "
                "disabled (opt)]"
            ),
            "type": "textarea",
            "value": settings["mcp_servers"],
            "hidden": True,
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_client_init_timeout",
            "title": "MCP Client Init Timeout",
            "description": (
                "Timeout for MCP client initialization (in seconds). "
                "Higher values might be required for complex MCPs, "
                "but might also slowdown system startup."
            ),
            "type": "number",
            "value": settings["mcp_client_init_timeout"],
        }
    )

    mcp_client_fields.append(
        {
            "id": "mcp_client_tool_timeout",
            "title": "MCP Client Tool Timeout",
            "description": (
                "Timeout for MCP client tool execution. "
                "Higher values might be required for complex tools, "
                "but might also result in long responses with failing tools."
            ),
            "type": "number",
            "value": settings["mcp_client_tool_timeout"],
        }
    )

    mcp_client_section: SettingsSection = {
        "id": "mcp_client",
        "title": "External MCP Servers",
        "description": ("Gary-Zero can use external MCP servers, local or remote as tools."),
        "fields": mcp_client_fields,
        "tab": "mcp",
    }

    mcp_server_fields: list[SettingsField] = []

    mcp_server_fields.append(
        {
            "id": "mcp_server_enabled",
            "title": "Enable A0 MCP Server",
            "description": (
                "Expose Gary-Zero as an SSE MCP server. "
                "This will make this A0 instance available to MCP clients."
            ),
            "type": "switch",
            "value": settings["mcp_server_enabled"],
        }
    )

    mcp_server_fields.append(
        {
            "id": "mcp_server_token",
            "title": "MCP Server Token",
            "description": "Token for MCP server authentication.",
            "type": "text",
            "hidden": True,
            "value": settings["mcp_server_token"],
        }
    )

    mcp_server_section: SettingsSection = {
        "id": "mcp_server",
        "title": "A0 MCP Server",
        "description": (
            "Gary-Zero can be exposed as an SSE MCP server. "
            "See <a href=\"javascript:openModal('settings/mcp/server/example.html')\">"
            "connection example</a>."
        ),
        "fields": mcp_server_fields,
        "tab": "mcp",
    }

    # Add the section to the result
    result: SettingsOutput = {
        "sections": [
            agent_section,
            chat_model_section,
            util_model_section,
            embed_model_section,
            browser_model_section,
            # memory_section,
            stt_section,
            api_keys_section,
            auth_section,
            mcp_client_section,
            mcp_server_section,
            dev_section,
        ]
    }
    return result


def _get_api_key_field(settings: Settings, provider: str, title: str) -> SettingsField:
    key = settings["api_keys"].get(provider, models.get_api_key(provider))
    return {
        "id": f"api_key_{provider}",
        "title": title,
        "type": "password",
        "value": (PASSWORD_PLACEHOLDER if key and key != "None" else ""),
    }


def convert_in(settings: dict) -> Settings:
    current = get_settings()
    for section in settings["sections"]:
        if "fields" in section:
            for field in section["fields"]:
                if field["value"] != PASSWORD_PLACEHOLDER:
                    if field["id"].endswith("_kwargs"):
                        current[field["id"]] = _env_to_dict(field["value"])
                    elif field["id"].startswith("api_key_"):
                        current["api_keys"][field["id"]] = field["value"]
                    else:
                        current[field["id"]] = field["value"]
    return current


def get_settings() -> Settings:
    """Get the current settings.

    Returns:
        The current settings, loaded from file or default if not set.
    """
    return settings_manager.SettingsManager().get_settings()


def set_settings(settings: Settings, apply: bool = True) -> None:
    """Apply settings to the running application.

    Args:
        settings: The new settings to apply
        apply: If True, apply the settings immediately
    """
    settings_manager.SettingsManager().set_settings(settings, apply=apply)


def set_settings_delta(delta: dict, apply: bool = True):
    current = get_settings()
    new = {**current, **delta}
    set_settings(new, apply)  # type: ignore


def normalize_settings(settings: Settings) -> Settings:
    copy = settings.copy()
    default = get_default_settings()

    # remove keys that are not in default
    keys_to_remove = [key for key in copy if key not in default]
    for key in keys_to_remove:
        del copy[key]

    # add missing keys and normalize types
    for key, value in default.items():
        if key not in copy:
            copy[key] = value
        else:
            try:
                copy[key] = type(value)(copy[key])  # type: ignore
            except (ValueError, TypeError):
                copy[key] = value  # make default instead

    # mcp server token is set automatically
    copy["mcp_server_token"] = create_auth_token()

    return copy


def _read_settings_file() -> Settings | None:
    """Read settings from the settings file.

    Note: This is kept for backward compatibility but delegates to SettingsManager.

    Returns:
        The current settings or None if no settings are available.
    """
    return settings_manager.SettingsManager().get_settings()


def _write_settings_file(settings: Settings):
    _write_sensitive_settings(settings)
    _remove_sensitive_settings(settings)

    # write settings
    content = json.dumps(settings, indent=4)
    files.write_file(SETTINGS_FILE, content)


def _remove_sensitive_settings(settings: Settings):
    settings["api_keys"] = {}
    settings["auth_login"] = ""
    settings["auth_password"] = ""
    settings["rfc_password"] = ""
    settings["root_password"] = ""
    settings["mcp_server_token"] = ""


def _write_sensitive_settings(settings: Settings):
    for key, val in settings["api_keys"].items():
        dotenv.save_dotenv_value(key.upper(), val)

    dotenv.save_dotenv_value(dotenv.KEY_AUTH_LOGIN, settings["auth_login"])
    if settings["auth_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_AUTH_PASSWORD, settings["auth_password"])
    if settings["rfc_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_RFC_PASSWORD, settings["rfc_password"])

    if settings["root_password"]:
        dotenv.save_dotenv_value(dotenv.KEY_ROOT_PASSWORD, settings["root_password"])
    if settings["root_password"]:
        set_root_password(settings["root_password"])


def get_default_settings() -> Settings:
    """Get the default settings.

    Returns:
        A copy of the default settings with additional default values.
    """
    default_settings = DEFAULT_SETTINGS.copy()
    # Add additional default settings that aren't in the base Settings type
    default_settings.update(
        {
            "embed_model_provider": "OPENAI",
            "embed_model_name": "text-embedding-3-large",
            "embed_model_kwargs": {},
            "embed_model_rl_requests": 0,
            "embed_model_rl_input": 0,
            "browser_model_provider": "ANTHROPIC",
            "browser_model_name": "claude-3-5-sonnet-20241022",
            "browser_model_vision": True,
            "browser_model_kwargs": {"temperature": "0"},
            "agent_prompts_subdir": "prompts",
            "agent_memory_subdir": "memory",
            "agent_knowledge_subdir": "knowledge",
            "api_keys": {},
            "auth_login": "admin",
            "auth_password": hashlib.sha256(b"admin").hexdigest(),
            "root_password": hashlib.sha256(b"").hexdigest(),
            "rfc_auto_docker": True,
            "rfc_url": "http://localhost:8000",
            "rfc_password": "",
            "rfc_port_http": 8000,
            "rfc_port_ssh": 8022,
            "stt_model_size": "base",
            "stt_language": "en",
            "stt_silence_threshold": 0.5,
            "stt_silence_duration": 1000,
            "stt_waiting_timeout": 5000,
            "mcp_servers": (
                "filesystem,github,github.com/pashpashpash/mcp-taskmanager,"
                "mcp-browserbase,mcp-playwright,memory"
            ),
            "mcp_client_init_timeout": 30,
            "mcp_client_tool_timeout": 300,
            "mcp_server_enabled": True,
            "mcp_server_token": create_auth_token(),
            "util_model_rl_requests": 0,
            "util_model_rl_input": 0,
            "util_model_rl_output": 0,
        }
    )
    return default_settings


def _apply_settings(previous: Settings | None) -> None:
    """Apply settings to the running application.

    Args:
        previous: The previous settings, or None if this is the first load.
    """
    current_settings = get_settings()
    if not current_settings:
        return

    # Lazy imports to avoid circular dependencies
    from agent import AgentContext
    from initialize import initialize_agent

    # Initialize agent configuration with current settings
    config = initialize_agent()

    # Update all agent contexts with the new configuration
    # TODO: Refactor AgentContext to provide a public accessor for contexts
    contexts: dict[Any, Any] = getattr(
        AgentContext, "contexts", getattr(AgentContext, "_contexts", {})
    )
    for ctx in contexts.values():
        ctx.config = config  # type: ignore[attr-defined]  # reinitialize context config

        # Apply config to all agents in the hierarchy
        agent = getattr(ctx, "agent0", None)
        while agent:
            agent.config = ctx.config  # type: ignore[attr-defined]
            agent = agent.get_data(  # type: ignore[attr-defined]
                getattr(agent, "DATA_NAME_SUBORDINATE", None)  # type: ignore[attr-defined]
            )

        # force memory reload on embedding model change
        if not previous or (
            current_settings["embed_model_name"] != previous["embed_model_name"]
            or current_settings["embed_model_provider"] != previous["embed_model_provider"]
            or current_settings["embed_model_kwargs"] != previous["embed_model_kwargs"]
        ):
            from framework.helpers.memory import reload as memory_reload

            memory_reload()

        # update mcp settings if necessary
        if not previous or current_settings["mcp_servers"] != previous["mcp_servers"]:

            async def update_mcp_settings(mcp_servers: str):
                PrintStyle(background_color="black", font_color="white", padding=True).print(
                    "Updating MCP config..."
                )
                AgentContext.log_to_all(type="info", content="Updating MCP settings...", temp=True)

                mcp_config = MCPConfig.get_instance()
                try:
                    MCPConfig.update(mcp_servers)
                except (RuntimeError, ValueError, AttributeError) as e:
                    AgentContext.log_to_all(
                        type="error",
                        content=f"Failed to update MCP settings: {e}",
                        temp=False,
                    )
                    PrintStyle(background_color="red", font_color="black", padding=True).print(
                        "Failed to update MCP settings"
                    )
                    PrintStyle(background_color="black", font_color="red", padding=True).print(
                        f"{e}"
                    )

                PrintStyle(background_color="#6734C3", font_color="white", padding=True).print(
                    "Parsed MCP config:"
                )
                PrintStyle(background_color="#334455", font_color="white", padding=False).print(
                    mcp_config.model_dump_json()
                )
                AgentContext.log_to_all(
                    type="info", content="Finished updating MCP settings.", temp=True
                )

            # TODO: Replace with a proper background task scheduler
            # if/when the codebase is fully async.
            import asyncio

            asyncio.create_task(update_mcp_settings(config.mcp_servers))

        # update token in mcp server
        # NOTE: The MCP server token is always generated from dotenv values for consistency.
        current_token = create_auth_token()
        if not previous or current_token != previous["mcp_server_token"]:

            async def update_mcp_token(token: str):
                from framework.helpers.mcp_server import DynamicMcpProxy

                DynamicMcpProxy.get_instance().reconfigure(token=token)

            # TODO: Replace with a proper background task scheduler
            # if/when the codebase is fully async.
            import asyncio

            asyncio.create_task(update_mcp_token(current_token))


def _env_to_dict(data: str):
    env_dict = {}
    line_pattern = re.compile(r"\s*([^#][^=]*)\s*=\s*(.*)")
    for line in data.splitlines():
        match = line_pattern.match(line)
        if match:
            key, value = match.groups()
            # Remove optional surrounding quotes (single or double)
            value = value.strip().strip('"').strip("'")
            env_dict[key.strip()] = value
    return env_dict


def _dict_to_env(data_dict):
    lines = []
    for key, value in data_dict.items():
        if "\n" in value:
            value = f"'{value}'"
        elif " " in value or value == "" or any(c in value for c in "\"'"):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def set_root_password(password: str):
    if not runtime.is_dockerized():
        raise RuntimeError("root password can only be set in dockerized environments")
    subprocess.run(f"echo 'root:{password}' | chpasswd", shell=True, check=True)
    dotenv.save_dotenv_value(dotenv.KEY_ROOT_PASSWORD, password)


def get_runtime_config(settings: Settings):
    if runtime.is_dockerized():
        return {
            "code_exec_ssh_addr": "localhost",
            "code_exec_ssh_port": 22,
            "code_exec_http_port": 80,
            "code_exec_ssh_user": "root",
        }
    else:
        host = settings["rfc_url"]
        if "//" in host:
            host = host.split("//")[1]
        if ":" in host:
            host = host.split(":")[0]
        if host.endswith("/"):
            host = host[:-1]
        return {
            "code_exec_ssh_addr": host,
            "code_exec_ssh_port": settings["rfc_port_ssh"],
            "code_exec_http_port": settings["rfc_port_http"],
            "code_exec_ssh_user": "root",
        }


def create_auth_token() -> str:
    username = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN) or ""
    password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD) or ""
    if not username or not password:
        return "0"
    # use base64 encoding for a more compact token with alphanumeric chars
    hash_bytes = hashlib.sha256(f"{username}:{password}".encode()).digest()
    # encode as base64 and remove any non-alphanumeric chars (like +, /, =)
    b64_token = base64.urlsafe_b64encode(hash_bytes).decode().replace("=", "")
    return b64_token[:16]
