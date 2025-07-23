
import models
from framework.helpers.settings.constants import MODEL_PARAMS_DESCRIPTION, PASSWORD_PLACEHOLDER
from framework.helpers.settings.field_builders import FieldBuilder
from framework.helpers.settings.types import Settings, SettingsField, SettingsSection

# Local imports for dotenv, files, runtime will be added within methods as needed


class SectionBuilder:
    """Builder for creating settings sections."""

    @staticmethod
    def build_chat_model_section(settings: Settings) -> SettingsSection:
        """Builds the chat model settings section."""
        chat_model_fields = FieldBuilder.create_model_fields(
            "chat",
            settings,
            models.ModelProvider,
            include_vision=True,
            include_context_length=True,
            include_context_history=True,
            model_params_description=MODEL_PARAMS_DESCRIPTION
        )
        return {
            "id": "chat_model",
            "title": "Chat Model",
            "description": "Selection and settings for main chat model used by Gary-Zero",
            "fields": chat_model_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_util_model_section(settings: Settings) -> SettingsSection:
        """Builds the utility model settings section."""
        util_model_fields = FieldBuilder.create_model_fields(
            "util",
            settings,
            models.ModelProvider,
            model_params_description=(
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            )
        )
        return {
            "id": "util_model",
            "title": "Utility model",
            "description": (
                "Smaller, cheaper, faster model for handling utility tasks like "
                "organizing memory, preparing prompts, summarizing."
            ),
            "fields": util_model_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_embed_model_section(settings: Settings) -> SettingsSection:
        """Builds the embedding model settings section."""
        embed_model_fields = FieldBuilder.create_model_fields(
            "embed",
            settings,
            models.ModelProvider,
            model_params_description=(
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            )
        )
        return {
            "id": "embed_model",
            "title": "Embedding Model",
            "description": "Settings for the embedding model used by Gary-Zero.",
            "fields": embed_model_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_browser_model_section(settings: Settings) -> SettingsSection:
        """Builds the browser model settings section."""
        browser_model_fields = FieldBuilder.create_model_fields(
            "browser",
            settings,
            models.ModelProvider,
            include_vision=True,
            model_params_description=(
                "Any other parameters supported by the model. "
                "Format is KEY=VALUE on individual lines, just like .env file."
            )
        )
        # Override description for browser model provider
        for field in browser_model_fields:
            if field["id"] == "browser_model_provider":
                field["description"] = """The provider for the browser model.
    This determines which API or service to use for browser operations."""
            if field["id"] == "browser_model_vision":
                field["title"] = "Use Vision"
                field["description"] = (
                    "Models capable of Vision can use it to analyze web pages from screenshots. "
                    "Increases quality but also token usage."
                )
        return {
            "id": "browser_model",
            "title": "Web Browser Model",
            "description": (
                "Settings for the web browser model. Gary-Zero uses "
                "<a href='https://github.com/browser-use/browser-use' target='_blank'>"
                "browser-use</a> agentic framework to handle web interactions."
            ),
            "fields": browser_model_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_auth_section(settings: Settings) -> SettingsSection:
        """Builds the authentication settings section."""
        from framework.helpers import (
            dotenv,  # Local import
            runtime,  # Local import
        )
        # from framework.helpers.settings.constants import PASSWORD_PLACEHOLDER # Already imported at top

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
                    PASSWORD_PLACEHOLDER
                    if dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD)
                    else ""
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
        return {
            "id": "auth",
            "title": "Authentication",
            "description": "Settings for authentication to use Gary-Zero Web UI.",
            "fields": auth_fields,
            "tab": "external",
        }

    @staticmethod
    def build_api_keys_section(settings: Settings) -> SettingsSection:
        """Builds the API keys settings section."""
        api_keys_fields = FieldBuilder.create_api_key_fields(settings)
        return {
            "id": "api_keys",
            "title": "API Keys",
            "description": "API keys for model providers and services used by Gary-Zero.",
            "fields": api_keys_fields,
            "tab": "external",
        }

    @staticmethod
    def build_agent_config_section(settings: Settings) -> SettingsSection:
        """Builds the agent configuration settings section."""
        from framework.helpers import files  # Local import

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
                    {"value": subdir, "label": subdir}
                    for subdir in files.get_subdirectories("prompts")
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
        return {
            "id": "agent",
            "title": "Agent Config",
            "description": "Agent parameters.",
            "fields": agent_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_dev_section(settings: Settings) -> SettingsSection:
        """Builds the development settings section."""
        from framework.helpers import (
            dotenv,  # Local import
            runtime,  # Local import
        )
        # from framework.helpers.settings.constants import PASSWORD_PLACEHOLDER # Already imported at top

        dev_fields: list[SettingsField] = []
        if runtime.is_development():
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
                    PASSWORD_PLACEHOLDER
                    if dotenv.get_dotenv_value(dotenv.KEY_RFC_PASSWORD)
                    else ""
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
        return {
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

    @staticmethod
    def build_stt_section(settings: Settings) -> SettingsSection:
        """Builds the speech-to-text settings section."""
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
        return {
            "id": "stt",
            "title": "Speech to Text",
            "description": (
                "Voice transcription preferences and server turn detection settings."
            ),
            "fields": stt_fields,
            "tab": "agent",
        }

    @staticmethod
    def build_mcp_client_section(settings: Settings) -> SettingsSection:
        """Builds the MCP client settings section."""
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
        return {
            "id": "mcp_client",
            "title": "External MCP Servers",
            "description": (
                "Gary-Zero can use external MCP servers, local or remote as tools."
            ),
            "fields": mcp_client_fields,
            "tab": "mcp",
        }

    @staticmethod
    def build_mcp_server_section(settings: Settings) -> SettingsSection:
        """Builds the MCP server settings section."""
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
        return {
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

    @staticmethod
    def build_computer_use_section(settings: Settings) -> SettingsSection:
        """Builds the Computer Use settings section."""
        computer_use_fields: list[SettingsField] = []

        computer_use_fields.append(
            {
                "id": "computer_use_enabled",
                "title": "Enable Computer Use",
                "description": "Enable Anthropic Computer Use tool for desktop automation (keyboard, mouse, window control)",
                "type": "switch",
                "value": settings.get("computer_use_enabled", False),
            }
        )

        computer_use_fields.append(
            {
                "id": "computer_use_require_approval",
                "title": "Require Approval",
                "description": "Require user approval before executing desktop automation actions",
                "type": "switch",
                "value": settings.get("computer_use_require_approval", True),
            }
        )

        computer_use_fields.append(
            {
                "id": "computer_use_screenshot_interval",
                "title": "Screenshot Interval (seconds)",
                "description": "Interval between automatic screenshots for computer use operations",
                "type": "number",
                "value": settings.get("computer_use_screenshot_interval", 1.0),
                "min": 0.1,
                "max": 10.0,
                "step": 0.1,
            }
        )

        computer_use_fields.append(
            {
                "id": "computer_use_max_actions_per_session",
                "title": "Max Actions Per Session",
                "description": "Maximum number of desktop automation actions allowed per session",
                "type": "number",
                "value": settings.get("computer_use_max_actions_per_session", 50),
                "min": 1,
                "max": 1000,
            }
        )

        return {
            "id": "computer_use",
            "title": "Computer Use",
            "description": "Anthropic Computer Use tool for desktop automation via keyboard, mouse, and window control",
            "fields": computer_use_fields,
            "tab": "tools",
        }

    @staticmethod
    def build_claude_code_section(settings: Settings) -> SettingsSection:
        """Builds the Claude Code settings section."""
        claude_code_fields: list[SettingsField] = []

        claude_code_fields.append(
            {
                "id": "claude_code_enabled",
                "title": "Enable Claude Code",
                "description": "Enable Claude Code tool for advanced code editing, Git operations, and terminal commands",
                "type": "switch",
                "value": settings.get("claude_code_enabled", False),
            }
        )

        claude_code_fields.append(
            {
                "id": "claude_code_max_file_size",
                "title": "Max File Size (bytes)",
                "description": "Maximum file size that can be processed by Claude Code tool",
                "type": "number",
                "value": settings.get("claude_code_max_file_size", 1048576),
                "min": 1024,
                "max": 10485760,  # 10MB
            }
        )

        claude_code_fields.append(
            {
                "id": "claude_code_enable_git_ops",
                "title": "Enable Git Operations",
                "description": "Allow Claude Code to perform Git operations (status, add, commit, push, pull)",
                "type": "switch",
                "value": settings.get("claude_code_enable_git_ops", True),
            }
        )

        claude_code_fields.append(
            {
                "id": "claude_code_enable_terminal",
                "title": "Enable Terminal Commands",
                "description": "Allow Claude Code to execute terminal commands",
                "type": "switch",
                "value": settings.get("claude_code_enable_terminal", True),
            }
        )

        return {
            "id": "claude_code",
            "title": "Claude Code",
            "description": "Claude Code tool for context-aware multi-file editing, Git operations, and terminal commands",
            "fields": claude_code_fields,
            "tab": "tools",
        }
