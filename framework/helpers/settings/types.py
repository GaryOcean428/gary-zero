"""Type definitions for application settings.

This module contains all type definitions used across the settings system.
"""

from typing import Any, Literal, TypedDict


class FieldOption(TypedDict):
    """Represents a selectable option in a settings field."""

    value: str
    label: str


class SettingsField(TypedDict, total=False):
    """Definition of a single settings field."""

    id: str
    title: str
    description: str
    type: Literal[
        "text", "number", "select", "range", "textarea", "password", "switch", "button"
    ]
    value: Any
    min: float
    max: float
    step: float
    hidden: bool
    options: list[FieldOption]


class SettingsSection(TypedDict, total=False):
    """A section containing related settings fields."""

    id: str
    title: str
    description: str
    fields: list[SettingsField]
    tab: str  # Indicates which tab this section belongs to


class SettingsOutput(TypedDict):
    """The complete settings structure for the UI."""

    sections: list[SettingsSection]


class Settings(TypedDict):
    """Application settings structure."""

    # Chat model settings
    chat_model_provider: str
    chat_model_name: str
    chat_model_kwargs: dict[str, str]
    chat_model_ctx_length: int
    chat_model_ctx_history: float
    chat_model_vision: bool
    chat_model_rl_requests: int
    chat_model_rl_input: int
    chat_model_rl_output: int

    # Utility model settings
    util_model_provider: str
    util_model_name: str
    util_model_kwargs: dict[str, str]
    util_model_ctx_length: int
    util_model_ctx_history: float
    util_model_vision: bool
    util_model_rl_requests: int
    util_model_rl_input: int
    util_model_rl_output: int

    # Embedding model settings
    embed_model_provider: str
    embed_model_name: str
    embed_model_kwargs: dict[str, str]
    embed_model_ctx_length: int
    embed_model_rl_requests: int
    embed_model_rl_input: int

    # Browser model settings
    browser_model_provider: str
    browser_model_name: str
    browser_model_kwargs: dict[str, str]
    browser_model_vision: bool
    browser_model_rl_requests: int
    browser_model_rl_input: int
    browser_model_rl_output: int

    # Voice model settings
    voice_model_provider: str
    voice_model_name: str
    voice_model_kwargs: dict[str, str]
    voice_model_rl_requests: int
    voice_model_rl_input: int
    voice_model_rl_output: int
    voice_architecture: str
    voice_transport: str

    # Code model settings
    code_model_provider: str
    code_model_name: str
    code_model_kwargs: dict[str, str]
    code_model_rl_requests: int
    code_model_rl_input: int
    code_model_rl_output: int

    # MCP Servers settings
    mcp_servers: str  # Change to string to match actual usage
    mcp_client_init_timeout: int
    mcp_client_tool_timeout: int

    # Database settings
    database_url: str
    database_name: str
    database_username: str
    database_password: str
    database_host: str
    database_port: int
    database_ssl: bool
    database_ssl_ca: str
    database_ssl_cert: str
    database_ssl_key: str
    database_ssl_verify_cert: bool

    # MCP Server settings
    mcp_server_enabled: bool
    mcp_server_token: str

    # RFC settings
    rfc_url: str
    rfc_password: str
    rfc_auto_docker: bool
    rfc_port_http: int
    rfc_port_ssh: int

    # OpenAI Codex CLI settings
    codex_cli_enabled: bool
    codex_cli_path: str
    codex_cli_approval_mode: str
    codex_cli_auto_install: bool

    # Google Gemini CLI settings
    gemini_cli_enabled: bool
    gemini_cli_path: str
    gemini_cli_approval_mode: str
    gemini_cli_auto_install: bool

    # Claude Code CLI settings
    claude_cli_enabled: bool
    claude_cli_path: str
    claude_cli_approval_mode: str
    claude_cli_auto_install: bool

    # Qwen Coder CLI settings
    qwen_cli_enabled: bool
    qwen_cli_path: str
    qwen_cli_approval_mode: str
    qwen_cli_auto_install: bool

    # Anthropic Computer Use settings
    computer_use_enabled: bool
    computer_use_require_approval: bool
    computer_use_screenshot_interval: float
    computer_use_max_actions_per_session: int

    # Claude Code settings
    claude_code_enabled: bool
    claude_code_max_file_size: int
    claude_code_enable_git_ops: bool
    claude_code_enable_terminal: bool

    # Agent configuration settings
    agent_prompts_subdir: str
    agent_memory_subdir: str
    agent_knowledge_subdir: str

    # STT settings
    stt_model_size: str
    stt_language: str
    stt_silence_threshold: float
    stt_silence_duration: int
    stt_waiting_timeout: int

    # API Keys
    api_keys: dict[str, str]

    # Auth Settings
    auth_login: str
    auth_password: str
    root_password: str


# Default settings values that can be used across modules
DEFAULT_SETTINGS: Settings = {
    # Chat model settings - using Claude 3.5 Sonnet (reliable and available)
    "chat_model_provider": "ANTHROPIC",
    "chat_model_name": "claude-3-5-sonnet-20241022",
    "chat_model_kwargs": {},
    "chat_model_ctx_length": 200000,  # 200K tokens
    "chat_model_ctx_history": 0.9,
    "chat_model_vision": True,
    "chat_model_rl_requests": 0,
    "chat_model_rl_input": 0,
    "chat_model_rl_output": 0,
    # Utility model settings - using GPT-4o-mini (available and efficient)
    "util_model_provider": "OPENAI",
    "util_model_name": "gpt-4o-mini",
    "util_model_kwargs": {},
    "util_model_ctx_length": 128000,  # 128K tokens (actual limit)
    "util_model_ctx_history": 0.9,
    "util_model_vision": False,
    "util_model_rl_requests": 0,
    "util_model_rl_input": 0,
    "util_model_rl_output": 0,
    # Embedding model settings - using OpenAI text-embedding-3-large (modern and valid)
    "embed_model_provider": "OPENAI",
    "embed_model_name": "text-embedding-3-large",
    "embed_model_kwargs": {},
    "embed_model_ctx_length": 8192,
    "embed_model_rl_requests": 0,
    "embed_model_rl_input": 0,
    # Browser model settings - using Claude 3.5 Sonnet for vision
    "browser_model_provider": "ANTHROPIC",
    "browser_model_name": "claude-3-5-sonnet-20241022",
    "browser_model_kwargs": {},
    "browser_model_vision": True,
    "browser_model_rl_requests": 0,
    "browser_model_rl_input": 0,
    "browser_model_rl_output": 0,
    # Voice model settings - using OpenAI GPT-4o (available model)
    "voice_model_provider": "OPENAI",
    "voice_model_name": "gpt-4o",
    "voice_model_kwargs": {},
    "voice_model_rl_requests": 0,
    "voice_model_rl_input": 0,
    "voice_model_rl_output": 0,
    "voice_architecture": "speech_to_speech",
    "voice_transport": "websocket",
    # Code model settings - using Claude 3.5 Sonnet for code tasks
    "code_model_provider": "ANTHROPIC",
    "code_model_name": "claude-3-5-sonnet-20241022",
    "code_model_kwargs": {},
    "code_model_rl_requests": 0,
    "code_model_rl_input": 0,
    "code_model_rl_output": 0,
    # Agent configuration settings
    "agent_prompts_subdir": "default",
    "agent_memory_subdir": "default",
    "agent_knowledge_subdir": "default",
    # STT settings
    "stt_model_size": "base",
    "stt_language": "en",
    "stt_silence_threshold": 0.5,
    "stt_silence_duration": 1000,
    "stt_waiting_timeout": 30,
    # MCP settings
    "mcp_servers": "filesystem,github,github.com/pashpashpash/mcp-taskmanager,mcp-browserbase,mcp-playwright,memory",
    "mcp_client_init_timeout": 30,
    "mcp_client_tool_timeout": 300,
    # Database settings
    "database_url": "sqlite:///./zero.db",
    "database_name": "zero",
    "database_username": "",
    "database_password": "",
    "database_host": "localhost",
    "database_port": 5432,
    "database_ssl": False,
    "database_ssl_ca": "",
    "database_ssl_cert": "",
    "database_ssl_key": "",
    "database_ssl_verify_cert": True,
    # MCP Server settings
    "mcp_server_enabled": True,
    "mcp_server_token": "mcp-token-12345",
    # RFC settings
    "rfc_url": "http://localhost:8000",
    "rfc_password": "",
    "rfc_auto_docker": True,
    "rfc_port_http": 8000,
    "rfc_port_ssh": 22,
    # OpenAI Codex CLI settings
    "codex_cli_enabled": False,
    "codex_cli_path": "codex",
    "codex_cli_approval_mode": "suggest",
    "codex_cli_auto_install": True,
    # Google Gemini CLI settings
    "gemini_cli_enabled": False,
    "gemini_cli_path": "gemini",
    "gemini_cli_approval_mode": "suggest",
    "gemini_cli_auto_install": True,
    # Claude Code CLI settings
    "claude_cli_enabled": False,
    "claude_cli_path": "claude-code",
    "claude_cli_approval_mode": "suggest",
    "claude_cli_auto_install": True,
    # Qwen Coder CLI settings
    "qwen_cli_enabled": False,
    "qwen_cli_path": "qwen-coder",
    "qwen_cli_approval_mode": "suggest",
    "qwen_cli_auto_install": True,
    # Anthropic Computer Use settings
    "computer_use_enabled": True,
    "computer_use_require_approval": False,
    "computer_use_screenshot_interval": 1.0,
    "computer_use_max_actions_per_session": 50,
    # Claude Code settings
    "claude_code_enabled": True,
    "claude_code_max_file_size": 1048576,  # 1MB
    "claude_code_enable_git_ops": True,
    "claude_code_enable_terminal": True,
    # API Keys (initially empty dict)
    "api_keys": {},
    # Auth settings
    "auth_login": "admin",
    "auth_password": "",
    "root_password": "",
}
