"""Model parameters database for automatic parameter configuration.

This module provides model-specific parameters like context length, vision capabilities,
and rate limits that are automatically applied when a model is selected.
"""

from typing import Any

# Model parameters database - organized by provider and model
MODEL_PARAMETERS: dict[str, dict[str, dict[str, Any]]] = {
    "ANTHROPIC": {
        "claude-sonnet-4-20250514": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-opus-4-20250514": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-opus-4-latest": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-5-sonnet-20241022": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-code": {
            "ctx_length": 200000,
            "vision": False,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-5-sonnet-latest": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-5-haiku-latest": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-7-sonnet-20250219": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-5-sonnet-20241022": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
        "claude-3-5-haiku-20241022": {
            "ctx_length": 200000,
            "vision": True,
            "rl_requests": 1000,
            "rl_input": 400000,
            "rl_output": 50000,
        },
    },
    "OPENAI": {
        "gpt-4o": {
            "ctx_length": 128000,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "gpt-4o-mini": {
            "ctx_length": 128000,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 200000000,
            "rl_output": 70000000,
        },
        "gpt-4o-realtime-preview": {
            "ctx_length": 128000,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "gpt-4o-audio": {
            "ctx_length": 128000,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "gpt-4o-mini-audio": {
            "ctx_length": 128000,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 200000000,
            "rl_output": 70000000,
        },
        "gpt-4.1": {
            "ctx_length": 1047576,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "gpt-4.1-mini": {
            "ctx_length": 1047576,
            "vision": True,
            "rl_requests": 10000,
            "rl_input": 200000000,
            "rl_output": 70000000,
        },
        "o1": {
            "ctx_length": 200000,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "o1-mini": {
            "ctx_length": 65536,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 200000000,
            "rl_output": 70000000,
        },
        "o1-pro": {
            "ctx_length": 200000,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "o3": {
            "ctx_length": 200000,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 30000000,
            "rl_output": 10000000,
        },
        "o3-mini": {
            "ctx_length": 65536,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 200000000,
            "rl_output": 70000000,
        },
        "text-embedding-3-large": {
            "ctx_length": 8192,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 10000000,
            "rl_output": 0,
        },
        "text-embedding-3-small": {
            "ctx_length": 8192,
            "vision": False,
            "rl_requests": 10000,
            "rl_input": 10000000,
            "rl_output": 0,
        },
    },
    "GOOGLE": {
        "gemini-2.5-pro-preview-06-05": {
            "ctx_length": 2000000,
            "vision": True,
            "rl_requests": 2,
            "rl_input": 32000,
            "rl_output": 8000,
        },
        "gemini-2.5-flash-preview-05-20": {
            "ctx_length": 1000000,
            "vision": True,
            "rl_requests": 15,
            "rl_input": 1000000,
            "rl_output": 50000,
        },
        "gemini-2.0-flash": {
            "ctx_length": 1000000,
            "vision": True,
            "rl_requests": 15,
            "rl_input": 1000000,
            "rl_output": 50000,
        },
    },
    "GROQ": {
        "llama-3.3-70b-versatile": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 30,
            "rl_input": 6000,
            "rl_output": 600,
        },
        "llama-3.1-70b-versatile": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 30,
            "rl_input": 6000,
            "rl_output": 600,
        },
        "llama-3.1-8b-instant": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 30,
            "rl_input": 30000,
            "rl_output": 6000,
        },
    },
    "MISTRALAI": {
        "mistral-large-latest": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 5,
            "rl_input": 1000000,
            "rl_output": 1000000,
        },
        "mistral-medium-latest": {
            "ctx_length": 32768,
            "vision": False,
            "rl_requests": 5,
            "rl_input": 1000000,
            "rl_output": 1000000,
        },
        "mistral-small-latest": {
            "ctx_length": 32768,
            "vision": False,
            "rl_requests": 5,
            "rl_input": 1000000,
            "rl_output": 1000000,
        },
    },
    "DEEPSEEK": {
        "deepseek-chat": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 60,
            "rl_input": 10000000,
            "rl_output": 10000000,
        },
        "deepseek-coder": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 60,
            "rl_input": 10000000,
            "rl_output": 10000000,
        },
        "deepseek-v3": {
            "ctx_length": 128000,
            "vision": False,
            "rl_requests": 60,
            "rl_input": 10000000,
            "rl_output": 10000000,
        },
    },
    "XAI": {
        "grok-4-latest": {
            "ctx_length": 131072,
            "vision": True,
            "rl_requests": 60,
            "rl_input": 5000000,
            "rl_output": 1000000,
        },
        "grok-3": {
            "ctx_length": 131072,
            "vision": True,
            "rl_requests": 60,
            "rl_input": 5000000,
            "rl_output": 1000000,
        },
        "grok-beta": {
            "ctx_length": 131072,
            "vision": True,
            "rl_requests": 60,
            "rl_input": 5000000,
            "rl_output": 1000000,
        },
    },
}

# Default parameters for unknown models
DEFAULT_PARAMETERS = {
    "ctx_length": 8192,
    "vision": False,
    "rl_requests": 0,
    "rl_input": 0,
    "rl_output": 0,
}


def get_model_parameters(provider: str, model_name: str) -> dict[str, Any]:
    """Get parameters for a specific model.

    Args:
        provider: The model provider (e.g., 'ANTHROPIC', 'OPENAI')
        model_name: The name of the model

    Returns:
        Dictionary containing model parameters (ctx_length, vision, rate limits)
    """
    provider_models = MODEL_PARAMETERS.get(provider, {})
    model_params = provider_models.get(model_name, DEFAULT_PARAMETERS.copy())

    # Ensure all required keys are present
    result = DEFAULT_PARAMETERS.copy()
    result.update(model_params)

    return result


def get_all_provider_models() -> dict[str, dict[str, dict[str, Any]]]:
    """Get all model parameters for all providers.

    Returns:
        Complete model parameters database
    """
    return MODEL_PARAMETERS.copy()


def has_model_parameters(provider: str, model_name: str) -> bool:
    """Check if we have specific parameters for a model.

    Args:
        provider: The model provider
        model_name: The name of the model

    Returns:
        True if we have specific parameters for this model
    """
    return provider in MODEL_PARAMETERS and model_name in MODEL_PARAMETERS[provider]


def update_model_parameters(
    provider: str, model_name: str, parameters: dict[str, Any]
) -> None:
    """Update parameters for a specific model.

    Args:
        provider: The model provider
        model_name: The name of the model
        parameters: Dictionary of parameters to update
    """
    if provider not in MODEL_PARAMETERS:
        MODEL_PARAMETERS[provider] = {}

    if model_name not in MODEL_PARAMETERS[provider]:
        MODEL_PARAMETERS[provider][model_name] = DEFAULT_PARAMETERS.copy()

    MODEL_PARAMETERS[provider][model_name].update(parameters)
