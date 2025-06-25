"""Type definitions for application settings.

This module contains all type definitions used across the settings system.
"""
from typing import Any, Literal, TypedDict, Optional, Dict, List, Union


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
        "text", "number", "select", "range",
        "textarea", "password", "switch", "button"
    ]
    value: Any
    min: float
    max: float
    step: float
    hidden: bool
    options: List[FieldOption]


class SettingsSection(TypedDict, total=False):
    """A section containing related settings fields."""
    id: str
    title: str
    description: str
    fields: List[SettingsField]
    tab: str  # Indicates which tab this section belongs to


class SettingsOutput(TypedDict):
    """The complete settings structure for the UI."""
    sections: List[SettingsSection]


class Settings(TypedDict):
    """Application settings structure."""
    # Chat model settings
    chat_model_provider: str
    chat_model_name: str
    chat_model_kwargs: Dict[str, str]
    chat_model_ctx_length: int
    chat_model_ctx_history: float
    chat_model_vision: bool
    chat_model_rl_requests: int
    chat_model_rl_input: int
    chat_model_rl_output: int

    # Utility model settings
    util_model_provider: str
    util_model_name: str
    util_model_kwargs: Dict[str, str]
    util_model_ctx_length: int
    util_model_ctx_history: float
    util_model_vision: bool
    util_model_rl_requests: int
    util_model_rl_input: int
    util_model_rl_output: int

    # Embedding model settings
    embed_model_provider: str
    embed_model_name: str
    embed_model_kwargs: Dict[str, str]
    embed_model_ctx_length: int
    embed_model_rl_requests: int
    embed_model_rl_input: int

    # Browser model settings
    browser_model_provider: str
    browser_model_name: str
    browser_model_kwargs: Dict[str, str]
    browser_model_vision: bool

    # MCP Servers settings
    mcp_servers: Dict[str, Any]

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

    # Add other settings fields as needed


# Default settings values that can be used across modules
DEFAULT_SETTINGS: Settings = {
    # Chat model settings
    "chat_model_provider": "groq",
    "chat_model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "chat_model_kwargs": {},
    "chat_model_ctx_length": 131072,  # 128K tokens
    "chat_model_ctx_history": 0.9,
    "chat_model_vision": True,
    "chat_model_rl_requests": 0,
    "chat_model_rl_input": 0,
    "chat_model_rl_output": 0,

    # Utility model settings
    "util_model_provider": "groq",
    "util_model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "util_model_kwargs": {},
    "util_model_ctx_length": 131072,
    "util_model_ctx_history": 0.9,
    "util_model_vision": False,
    "util_model_rl_requests": 0,
    "util_model_rl_input": 0,
    "util_model_rl_output": 0,

    # Embedding model settings
    "embed_model_provider": "groq",
    "embed_model_name": "text-embedding-3-large",
    "embed_model_kwargs": {},
    "embed_model_ctx_length": 8192,
    "embed_model_rl_requests": 0,
    "embed_model_rl_input": 0,

    # Browser model settings
    "browser_model_provider": "groq",
    "browser_model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
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
