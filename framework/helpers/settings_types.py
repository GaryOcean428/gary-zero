"""Type definitions and constants for application settings.

This module contains the core type definitions used across the settings system
to avoid circular imports between settings.py and settings_manager.py.
"""
from typing import Literal, TypedDict


class Settings(TypedDict):
    """Application settings structure."""
    chat_model_provider: str
    chat_model_name: str
    chat_model_kwargs: dict[str, str]
    chat_model_ctx_length: int
    chat_model_ctx_history: float
    chat_model_vision: bool
    chat_model_rl_requests: int
    chat_model_rl_input: int
    chat_model_rl_output: int
    util_model_provider: str
    util_model_name: str
    util_model_kwargs: dict[str, str]
    util_model_ctx_length: int
    util_model_ctx_input: float


# Default settings values that can be used across modules
DEFAULT_SETTINGS: Settings = {
    # Chat model settings
    "chat_model_provider": "groq",
    "chat_model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "chat_model_kwargs": {},
    "chat_model_ctx_length": 131072, # 128K tokens
    "chat_model_ctx_history": 0.9,
    "chat_model_vision": True, # Llama 4 Maverick supports vision
    "chat_model_rl_requests": 0, # Set to 0 to disable rate limiting by default
    "chat_model_rl_input": 0,
    "chat_model_rl_output": 0,

    # Utility model settings
    "util_model_provider": "groq",
    "util_model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "util_model_kwargs": {},
    "util_model_ctx_length": 131072,
    "util_model_ctx_input": 0.9,
    "util_model_rl_requests": 0,
    "util_model_rl_input": 0,
    "util_model_rl_output": 0,

    # Embedding model settings
    "embed_model_provider": "openai",
    "embed_model_name": "text-embedding-ada-002",
    "embed_model_kwargs": {},
    "embed_model_rl_requests": 0,
    "embed_model_rl_input": 0,

    # Browser model settings
    "browser_model_provider": "openai",
    "browser_model_name": "gpt-4.1-vision-preview",
    "browser_model_vision": True,
    "browser_model_kwargs": {"temperature": "0"}
}
