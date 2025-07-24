"""Model catalog with available models for each provider.

This module provides a comprehensive mapping of AI models available
for each provider, used to populate dropdown selections in the UI.
Modern models (released after June 2024) are prioritized first in each provider's list.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.helpers.settings import FieldOption

# A dictionary representing a single model's metadata.
# The values can be strings or booleans.
ModelInfo = dict[str, str | bool]

# A dictionary mapping a provider (like "OPENAI") to a list of its models.
ModelCollection = dict[str, list[ModelInfo]]

# For runtime, we'll use the actual type
from typing import Any
FieldOptionRuntime = dict[str, Any]

# The main catalog of all models.
MODEL_CATALOG: ModelCollection = {
    "ANTHROPIC": [
        # Modern models (post-June 2024)
        {
            "value": "claude-sonnet-4-0",
            "label": "Claude 4 Sonnet",
            "modern": True,
            "release_date": "2025-05-14",
        },
        {
            "value": "claude-opus-4-0",
            "label": "Claude 4 Opus",
            "modern": True,
            "release_date": "2025-05-14",
        },
        {
            "value": "claude-3-7-sonnet-latest",
            "label": "Claude 3.7 Sonnet (2025-02-19)",
            "modern": True,
            "release_date": "2025-02-19",
        },
        {
            "value": "claude-3-5-sonnet-latest",
            "label": "Claude 3.5 Sonnet (Latest)",
            "modern": True,
            "release_date": "2024-10-22",
        },
        {
            "value": "claude-code",
            "label": "Claude Code",
            "modern": True,
            "release_date": "2024-10-22",
            "code": True,
        },
        {
            "value": "claude-3-5-haiku-latest",
            "label": "Claude 3.5 Haiku (Latest)",
            "modern": True,
            "release_date": "2024-11-01",
        },
    ],
    "OPENAI": [
        # Modern models (post-June 2024)
        {"value": "o3", "label": "o3", "modern": True, "release_date": "2025-01-31"},
        {
            "value": "o3-mini",
            "label": "o3 Mini",
            "modern": True,
            "release_date": "2025-01-31",
        },
        {
            "value": "o3-mini-2025-01-31",
            "label": "o3 Mini (2025-01-31)",
            "modern": True,
            "release_date": "2025-01-31",
        },
        {
            "value": "o3-pro",
            "label": "o3 Pro",
            "modern": True,
            "release_date": "2025-01-31",
        },
        {
            "value": "o4-mini",
            "label": "o4 Mini",
            "modern": True,
            "release_date": "2025-03-01",
        },
        {"value": "o1", "label": "o1", "modern": True, "release_date": "2024-09-12"},
        {
            "value": "o1-mini",
            "label": "o1 Mini",
            "modern": True,
            "release_date": "2024-09-12",
        },
        {
            "value": "o1-pro",
            "label": "o1 Pro",
            "modern": True,
            "release_date": "2024-12-05",
        },
        {
            "value": "chatgpt-4.1",
            "label": "ChatGPT-4.1",
            "modern": True,
            "release_date": "2024-12-01",
        },
        {
            "value": "gpt-4.1",
            "label": "GPT-4.1",
            "modern": True,
            "release_date": "2024-12-01",
        },
        {
            "value": "gpt-4.1-mini",
            "label": "GPT-4.1 Mini",
            "modern": True,
            "release_date": "2024-12-01",
        },
        {
            "value": "gpt-4.1-nano",
            "label": "GPT-4.1 Nano",
            "modern": True,
            "release_date": "2024-12-01",
        },
        {
            "value": "gpt-4.1-vision",
            "label": "GPT-4.1 Vision",
            "modern": True,
            "release_date": "2024-12-01",
        },
        {
            "value": "gpt-4o-mini",
            "label": "GPT-4o Mini",
            "modern": True,
            "release_date": "2024-07-18",
        },
        {
            "value": "computer-use-preview",
            "label": "Computer Use Preview",
            "modern": True,
            "release_date": "2024-10-01",
        },
        {
            "value": "gpt-4o-realtime-preview",
            "label": "GPT-4o Realtime Preview",
            "modern": True,
            "release_date": "2024-10-01",
            "voice": True,
        },
        {
            "value": "gpt-4o-audio",
            "label": "GPT-4o Audio",
            "modern": True,
            "release_date": "2024-10-01",
            "voice": True,
        },
        {
            "value": "gpt-4o-mini-audio",
            "label": "GPT-4o Mini Audio",
            "modern": True,
            "release_date": "2024-10-01",
            "voice": True,
        },
        {
            "value": "gpt-4o-search-preview",
            "label": "GPT-4o Search Preview",
            "modern": True,
            "release_date": "2024-10-01",
        },
        {
            "value": "gpt-4o-mini-search-preview",
            "label": "GPT-4o Mini Search Preview",
            "modern": True,
            "release_date": "2024-10-01",
        },
        # Embedding models - modern and widely used
        {
            "value": "text-embedding-3-large",
            "label": "Text Embedding 3 Large",
            "modern": True,
            "release_date": "2024-01-25",
        },
        {
            "value": "text-embedding-3-small",
            "label": "Text Embedding 3 Small",
            "modern": True,
            "release_date": "2024-01-25",
        },
    ],
    "GOOGLE": [
        # Modern models (post-June 2024)
        {
            "value": "gemini-2.5-pro-preview-06-05",
            "label": "Gemini 2.5 Pro Preview (06-05)",
            "modern": True,
            "release_date": "2025-06-05",
        },
        {
            "value": "gemini-2.5-flash-preview-05-20",
            "label": "Gemini 2.5 Flash Preview (05-20)",
            "modern": True,
            "release_date": "2025-05-20",
        },
        {
            "value": "gemini-2.5-flash-preview-tts",
            "label": "Gemini 2.5 Flash Preview TTS",
            "modern": True,
            "release_date": "2025-05-20",
            "voice": True,
        },
        {
            "value": "gemini-2.5-pro-preview-tts",
            "label": "Gemini 2.5 Pro Preview TTS",
            "modern": True,
            "release_date": "2025-06-05",
            "voice": True,
        },
        {
            "value": "gemini-2.5-pro-exp-03-25",
            "label": "Gemini 2.5 Pro Exp (03-25)",
            "modern": True,
            "release_date": "2025-03-25",
        },
        {
            "value": "gemini-2.0-flash",
            "label": "Gemini 2.0 Flash",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-2.0-flash-preview-image-generation",
            "label": "Gemini 2.0 Flash Preview Image Generation",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-2.0-flash-thinking-exp",
            "label": "Gemini 2.0 Flash Thinking Exp",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-2.0-pro-experimental",
            "label": "Gemini 2.0 Pro Experimental",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-2.0-flash-lite",
            "label": "Gemini 2.0 Flash Lite",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-cli-chat",
            "label": "Gemini CLI Chat",
            "modern": True,
            "release_date": "2024-12-11",
        },
        {
            "value": "gemini-cli-code",
            "label": "Gemini CLI Code",
            "modern": True,
            "release_date": "2024-12-11",
            "code": True,
        },
    ],
    "GROQ": [
        # Modern models (post-June 2024)
        {
            "value": "compound-beta",
            "label": "Compound Beta",
            "modern": True,
            "release_date": "2024-10-01",
        },
        {
            "value": "kimi-k2-instruct",
            "label": "Kimi K2 Instruct",
            "modern": True,
            "release_date": "2024-10-01",
        },
        {
            "value": "llama-3.3-70b-versatile",
            "label": "Llama 3.3 70B Versatile",
            "modern": True,
            "release_date": "2024-12-06",
        },
        {
            "value": "llama-3.1-70b-versatile",
            "label": "Llama 3.1 70B Versatile",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "llama-3.1-8b-instant",
            "label": "Llama 3.1 8B Instant",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "gemma2-9b-it",
            "label": "Gemma 2 9B IT",
            "modern": True,
            "release_date": "2024-06-27",
        },
    ],
    "MISTRALAI": [
        # No modern models available - all legacy models removed
    ],
    "OPENAI_AZURE": [
        # No modern models available - all legacy models removed
    ],
    "DEEPSEEK": [
        # Modern models (post-June 2024)
        {
            "value": "deepseek-v3",
            "label": "DeepSeek V3",
            "modern": True,
            "release_date": "2024-12-26",
        },
    ],
    "OPENROUTER": [
        # Modern models (using modern base models)
        {
            "value": "anthropic/claude-3.5-sonnet",
            "label": "Claude 3.5 Sonnet (OR)",
            "modern": True,
            "release_date": "2024-06-21",
        },
        {
            "value": "meta-llama/llama-3.1-70b-instruct",
            "label": "Llama 3.1 70B (OR)",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "qwen/qwen-2.5-72b-instruct",
            "label": "Qwen 2.5 72B (OR)",
            "modern": True,
            "release_date": "2024-09-19",
        },
    ],
    "SAMBANOVA": [
        # Modern models (post-June 2024)
        {
            "value": "Meta-Llama-3.1-70B-Instruct",
            "label": "Llama 3.1 70B Instruct",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "Meta-Llama-3.1-8B-Instruct",
            "label": "Llama 3.1 8B Instruct",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "Meta-Llama-3.2-1B-Instruct",
            "label": "Llama 3.2 1B Instruct",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "Meta-Llama-3.2-3B-Instruct",
            "label": "Llama 3.2 3B Instruct",
            "modern": True,
            "release_date": "2024-09-25",
        },
    ],
    "XAI": [
        # Modern models (post-June 2024)
        {
            "value": "grok-4-latest",
            "label": "Grok 4 (Latest)",
            "modern": True,
            "release_date": "2025-07-09",
        },
        {
            "value": "grok-4-0709",
            "label": "Grok 4 (0709)",
            "modern": True,
            "release_date": "2025-07-09",
        },
        {
            "value": "grok-3",
            "label": "Grok 3",
            "modern": True,
            "release_date": "2025-02-17",
        },
        {
            "value": "grok-3-fast",
            "label": "Grok 3 Fast",
            "modern": True,
            "release_date": "2025-02-17",
        },
        {
            "value": "grok-3-mini",
            "label": "Grok 3 Mini",
            "modern": True,
            "release_date": "2025-02-17",
        },
        {
            "value": "grok-3-mini-fast",
            "label": "Grok 3 Mini Fast",
            "modern": True,
            "release_date": "2025-02-17",
        },
        {
            "value": "grok-2-1212",
            "label": "Grok 2 (1212)",
            "modern": True,
            "release_date": "2024-08-14",
        },
        {
            "value": "grok-2-vision-1212",
            "label": "Grok 2 Vision (1212)",
            "modern": True,
            "release_date": "2024-08-14",
        },
    ],
    "PERPLEXITY": [
        # Modern models (post-June 2024)
        {
            "value": "sonar-reasoning-pro",
            "label": "Sonar Reasoning Pro",
            "modern": True,
            "release_date": "2025-02-11",
        },
        {
            "value": "sonar-pro",
            "label": "Sonar Pro",
            "modern": True,
            "release_date": "2025-02-11",
        },
        {
            "value": "llama-3.1-sonar-small-128k-online",
            "label": "Llama 3.1 Sonar Small 128K",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "llama-3.1-sonar-large-128k-online",
            "label": "Llama 3.1 Sonar Large 128K",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "llama-3.1-sonar-huge-128k-online",
            "label": "Llama 3.1 Sonar Huge 128K",
            "modern": True,
            "release_date": "2024-07-23",
        },
    ],
    "HUGGINGFACE": [
        # No modern models available - provider deprecated
    ],
    "OLLAMA": [
        # Modern models (post-June 2024)
        {
            "value": "llama3.2",
            "label": "Llama 3.2",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "llama3.1",
            "label": "Llama 3.1",
            "modern": True,
            "release_date": "2024-07-23",
        },
        {
            "value": "qwen2",
            "label": "Qwen 2",
            "modern": True,
            "release_date": "2024-06-07",
        },
    ],
    "LMSTUDIO": [
        # Modern models (post-June 2024)
        {
            "value": "llama-3.2-1b-instruct",
            "label": "Llama 3.2 1B Instruct",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "llama-3.2-3b-instruct",
            "label": "Llama 3.2 3B Instruct",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "gemma-2-2b-instruct",
            "label": "Gemma 2 2B Instruct",
            "modern": True,
            "release_date": "2024-06-27",
        },
    ],
    "CHUTES": [
        # Provider deprecated - no modern models available
    ],
    "META": [
        # Modern models (post-June 2024)
        {
            "value": "llama-3.3",
            "label": "LLaMA 3.3",
            "modern": True,
            "release_date": "2024-12-06",
        },
        {
            "value": "llama-3.3-70b-instruct",
            "label": "Llama 3.3 70B Instruct",
            "modern": True,
            "release_date": "2024-12-06",
        },
        {
            "value": "llama-3.2-11b-vision-instruct",
            "label": "Llama 3.2 11B Vision",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "llama-3.2-90b-vision-instruct",
            "label": "Llama 3.2 90B Vision",
            "modern": True,
            "release_date": "2024-09-25",
        },
        {
            "value": "llama-3.1-405b-instruct",
            "label": "Llama 3.1 405B Instruct",
            "modern": True,
            "release_date": "2024-07-23",
        },
    ],
    "QWEN": [
        # Modern models (post-June 2024)
        {
            "value": "qwen-3-coder",
            "label": "Qwen 3 Coder",
            "modern": True,
            "release_date": "2024-11-15",
            "code": True,
        },
        {
            "value": "qwen-2.5-coder-32b-instruct",
            "label": "Qwen 2.5 Coder 32B Instruct",
            "modern": True,
            "release_date": "2024-09-19",
            "code": True,
        },
        {
            "value": "qwen-2.5-coder-14b-instruct",
            "label": "Qwen 2.5 Coder 14B Instruct",
            "modern": True,
            "release_date": "2024-09-19",
            "code": True,
        },
        {
            "value": "qwen-2.5-coder-7b-instruct",
            "label": "Qwen 2.5 Coder 7B Instruct",
            "modern": True,
            "release_date": "2024-09-19",
            "code": True,
        },
    ],
    "OTHER": [
        {"value": "custom-model-1", "label": "Custom Model 1"},
        {"value": "custom-model-2", "label": "Custom Model 2"},
    ],
}


def get_models_for_provider(provider_name: str) -> list[FieldOptionRuntime]:
    """Get available models for a specific provider.

    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')

    Returns:
        List of model dictionaries with 'value' and 'label' keys
    """
    return MODEL_CATALOG.get(provider_name, [])


def get_modern_models_for_provider(provider_name: str) -> list[FieldOptionRuntime]:
    """Get modern models (post-June 2024) for a specific provider.

    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')

    Returns:
        List of modern model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    return [model for model in provider_models if model.get("modern", False)]


def get_deprecated_models_for_provider(provider_name: str) -> list[FieldOptionRuntime]:
    """Get deprecated models (pre-June 2024) for a specific provider.

    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')

    Returns:
        List of deprecated model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    return [model for model in provider_models if model.get("deprecated", False)]


def get_all_models() -> list[FieldOptionRuntime]:
    """Get all available models across all providers.

    Returns:
        List of all model dictionaries with 'value' and 'label' keys
    """
    all_models = []
    for provider_models in MODEL_CATALOG.values():
        all_models.extend(provider_models)
    return all_models


def get_all_modern_models() -> list[FieldOptionRuntime]:
    """Get all modern models (post-June 2024) across all providers.
    
    This includes both models released after June 2024 and approved embedding models
    (text-embedding-3-large/small) which remain supported and maintained.

    Returns:
        List of all modern model dictionaries including embeddings
    """
    all_models = get_all_models()
    modern_models = []
    
    for model in all_models:
        # Include models marked as modern
        if model.get("modern", False):
            modern_models.append(model)
        # Also include approved embedding models (exception to date rule)
        elif (model.get("value") in ["text-embedding-3-large", "text-embedding-3-small"] 
              and "embedding" in model.get("value", "").lower()):
            modern_models.append(model)
    
    return modern_models


def get_all_deprecated_models() -> list[FieldOptionRuntime]:
    """Get all deprecated models (pre-June 2024) across all providers.

    Returns:
        List of all deprecated model dictionaries
    """
    all_models = get_all_models()
    return [model for model in all_models if model.get("deprecated", False)]


def get_recommended_model_for_provider(provider_name: str) -> FieldOptionRuntime | None:
    """Get the recommended (first modern) model for a provider.

    Args:
        provider_name: The name of the provider

    Returns:
        The first modern model for the provider, or the first model if no modern models exist
    """
    modern_models = get_modern_models_for_provider(provider_name)
    if modern_models:
        return modern_models[0]

    # Fallback to first available model if no modern models
    all_models = get_models_for_provider(provider_name)
    return all_models[0] if all_models else None


def is_valid_model_for_provider(provider_name: str, model_name: str) -> bool:
    """Check if a model is valid for a given provider.

    Args:
        provider_name: The name of the provider
        model_name: The name of the model to check

    Returns:
        True if the model is valid for the provider, False otherwise
    """
    provider_models = get_models_for_provider(provider_name)
    return any(model["value"] == model_name for model in provider_models)


def is_model_deprecated(provider_name: str, model_name: str) -> bool:
    """Check if a model is deprecated (released before June 2024).

    Args:
        provider_name: The name of the provider
        model_name: The name of the model to check

    Returns:
        True if the model is deprecated, False otherwise
    """
    provider_models = get_models_for_provider(provider_name)
    for model in provider_models:
        if model["value"] == model_name:
            return model.get("deprecated", False)
    return False


def validate_model_selection(provider_name: str, model_name: str) -> bool:
    """Validate a model selection, allowing exemptions for embeddings."""
    # Retrieve models for the provider
    provider_models = get_models_for_provider(provider_name)

    # Check if model exists in the catalog
    model_exists = any(m["value"] == model_name for m in provider_models)
    if not model_exists:
        return False

    # Check modern status or embedding exemption
    for model in provider_models:
        if model["value"] == model_name:
            is_modern = model.get("modern", False)
            is_embedding = "embedding" in model_name.lower()
            return is_modern or is_embedding
    return False


def is_model_modern(provider_name: str, model_name: str) -> bool:
    """Check if a model is modern (released after June 2024).

    Args:
        provider_name: The name of the provider
        model_name: The name of the model to check

    Returns:
        True if the model is modern, False otherwise
    """
    provider_models = get_models_for_provider(provider_name)
    for model in provider_models:
        if model["value"] == model_name:
            return model.get("modern", False)
    return False


def get_voice_models_for_provider(provider_name: str) -> list[dict[str, str]]:
    """Get voice-capable models for a specific provider.

    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')

    Returns:
        List of voice model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    return [model for model in provider_models if model.get("voice", False)]


def get_code_models_for_provider(provider_name: str) -> list[dict[str, str]]:
    """Get code-oriented models for a specific provider.

    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')

    Returns:
        List of code model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    code_models = []
    for model in provider_models:
        # Check if it's explicitly marked as a code model or has "code" in the name
        if model.get("code", False) or "code" in model["value"].lower():
            code_models.append(model)
    return code_models


def get_all_voice_models() -> list[dict[str, str]]:
    """Get all voice-capable models across all providers.

    Returns:
        List of all voice model dictionaries
    """
    all_models = get_all_models()
    return [model for model in all_models if model.get("voice", False)]


def get_all_code_models() -> list[dict[str, str]]:
    """Get all code-oriented models across all providers.

    Returns:
        List of all code model dictionaries
    """
    all_models = get_all_models()
    code_models = []
    for model in all_models:
        # Check if it's explicitly marked as a code model or has "code" in the name
        if model.get("code", False) or "code" in model["value"].lower():
            code_models.append(model)
    return code_models


def get_model_release_date(provider_name: str, model_name: str) -> str | None:
    """Get the release date of a model.

    Args:
        provider_name: The name of the provider
        model_name: The name of the model

    Returns:
        The release date string if available, None otherwise
    """
    provider_models = get_models_for_provider(provider_name)
    for model in provider_models:
        if model["value"] == model_name:
            return model.get("release_date")
    return None
