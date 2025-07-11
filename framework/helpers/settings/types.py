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
    type: Literal["text", "number", "select", "range", "textarea", "password", "switch", "button"]
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

    # MCP Servers settings
    mcp_servers: dict[str, Any]

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


# Default settings values that can be used across modules
DEFAULT_SETTINGS: Settings = {
    # Chat model settings - using Claude-3.5-Sonnet for high performance
    "chat_model_provider": "ANTHROPIC",
    "chat_model_name": "claude-3-5-sonnet-20241022",
    "chat_model_kwargs": {},
    "chat_model_ctx_length": 200000,  # 200K tokens as per spec
    "chat_model_ctx_history": 0.9,
    "chat_model_vision": True,
    "chat_model_rl_requests": 0,
    "chat_model_rl_input": 0,
    "chat_model_rl_output": 0,
    # Utility model settings - using GPT-4.1-mini for efficiency
    "util_model_provider": "OPENAI",
    "util_model_name": "gpt-4.1-mini",
    "util_model_kwargs": {},
    "util_model_ctx_length": 1047576,  # 1M+ tokens as per spec
    "util_model_ctx_history": 0.9,
    "util_model_vision": False,
    "util_model_rl_requests": 0,
    "util_model_rl_input": 0,
    "util_model_rl_output": 0,
    # Embedding model settings - using OpenAI text-embedding-3-large
    "embed_model_provider": "OPENAI",
    "embed_model_name": "text-embedding-3-large",
    "embed_model_kwargs": {},
    "embed_model_ctx_length": 8192,
    "embed_model_rl_requests": 0,
    "embed_model_rl_input": 0,
    # Browser model settings - using Claude-3.5-Sonnet for vision
    "browser_model_provider": "ANTHROPIC",
    "browser_model_name": "claude-3-5-sonnet-20241022",
    "browser_model_kwargs": {},
    "browser_model_vision": True,
    # MCP Servers settings
    "mcp_servers": {},
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
}
