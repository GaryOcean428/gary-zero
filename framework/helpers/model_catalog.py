"""Model catalog with available models for each provider.

This module provides a comprehensive mapping of AI models available
for each provider, used to populate dropdown selections in the UI.
Modern models (released after June 2024) are prioritized first in each provider's list.
"""


# Comprehensive model catalog organized by provider
# Modern models (post-June 2024) are listed first, legacy models follow
MODEL_CATALOG: dict[str, list[dict[str, str]]] = {
    "ANTHROPIC": [
        # Modern models (post-June 2024)
        {"value": "claude-sonnet-4-20250514", "label": "Claude 4 Sonnet (2025-05-14)", "modern": True, "release_date": "2025-05-14"},
        {"value": "claude-opus-4-20250514", "label": "Claude 4 Opus (2025-05-14)", "modern": True, "release_date": "2025-05-14"},
        {"value": "claude-opus-4-latest", "label": "Claude 4 Opus", "modern": True, "release_date": "2025-05-14"},
        {"value": "claude-3-7-sonnet-20250219", "label": "Claude 3.7 Sonnet (2025-02-19)", "modern": True, "release_date": "2025-02-19"},
        {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (Latest)", "modern": True, "release_date": "2024-10-22"},
        {"value": "claude-code", "label": "Claude Code", "modern": True, "release_date": "2024-10-22"},
        {"value": "claude-3-5-sonnet-latest", "label": "Claude 3.5 Sonnet (Latest)", "modern": True, "release_date": "2024-06-21"},
        {"value": "claude-3-5-haiku-latest", "label": "Claude 3.5 Haiku (Latest)", "modern": True, "release_date": "2024-11-01"},
        {"value": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (2024-10-22)", "modern": True, "release_date": "2024-10-22"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus", "deprecated": True, "release_date": "2024-03-04"},
        {"value": "claude-3-sonnet-20240229", "label": "Claude 3 Sonnet", "deprecated": True, "release_date": "2024-03-04"},
        {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku", "deprecated": True, "release_date": "2024-03-04"},
        {"value": "claude-2.1", "label": "Claude 2.1", "deprecated": True, "release_date": "2023-11-21"},
        {"value": "claude-2.0", "label": "Claude 2.0", "deprecated": True, "release_date": "2023-07-11"},
        {"value": "claude-instant-1.2", "label": "Claude Instant 1.2", "deprecated": True, "release_date": "2024-03-01"},
    ],
    "OPENAI": [
        # Modern models (post-June 2024)
        {"value": "o3", "label": "o3", "modern": True, "release_date": "2025-01-31"},
        {"value": "o3-mini", "label": "o3 Mini", "modern": True, "release_date": "2025-01-31"},
        {"value": "o3-mini-2025-01-31", "label": "o3 Mini (2025-01-31)", "modern": True, "release_date": "2025-01-31"},
        {"value": "o3-pro", "label": "o3 Pro", "modern": True, "release_date": "2025-01-31"},
        {"value": "o4-mini", "label": "o4 Mini", "modern": True, "release_date": "2025-03-01"},
        {"value": "o1", "label": "o1", "modern": True, "release_date": "2024-09-12"},
        {"value": "o1-mini", "label": "o1 Mini", "modern": True, "release_date": "2024-09-12"},
        {"value": "o1-pro", "label": "o1 Pro", "modern": True, "release_date": "2024-12-05"},
        {"value": "chatgpt-4.1", "label": "ChatGPT-4.1", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4.1", "label": "GPT-4.1", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4.1-mini", "label": "GPT-4.1 Mini", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4.1-nano", "label": "GPT-4.1 Nano", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4.1-vision", "label": "GPT-4.1 Vision", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4.1-embeddings", "label": "GPT-4.1 Embeddings", "modern": True, "release_date": "2024-12-01"},
        {"value": "gpt-4o-mini", "label": "GPT-4o Mini", "modern": True, "release_date": "2024-07-18"},
        {"value": "computer-use-preview", "label": "Computer Use Preview", "modern": True, "release_date": "2024-10-01"},
        # Mixed models (gpt-4o was May 2024, but variants are newer)
        {"value": "gpt-4o", "label": "GPT-4o (Latest)", "modern": True, "release_date": "2024-05-13"},
        {"value": "gpt-4o-realtime-preview", "label": "GPT-4o Realtime Preview", "modern": True, "release_date": "2024-10-01"},
        {"value": "gpt-4o-audio", "label": "GPT-4o Audio", "modern": True, "release_date": "2024-10-01"},
        {"value": "gpt-4o-mini-audio", "label": "GPT-4o Mini Audio", "modern": True, "release_date": "2024-10-01"},
        {"value": "gpt-4o-search-preview", "label": "GPT-4o Search Preview", "modern": True, "release_date": "2024-10-01"},
        {"value": "gpt-4o-mini-search-preview", "label": "GPT-4o Mini Search Preview", "modern": True, "release_date": "2024-10-01"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "gpt-4-turbo", "label": "GPT-4 Turbo", "deprecated": True, "release_date": "2023-11-06"},
        {"value": "gpt-4-turbo-preview", "label": "GPT-4 Turbo Preview", "deprecated": True, "release_date": "2023-11-06"},
        {"value": "gpt-4", "label": "GPT-4", "deprecated": True, "release_date": "2023-03-14"},
        {"value": "gpt-4-32k", "label": "GPT-4 32K", "deprecated": True, "release_date": "2023-03-14"},
        {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo", "deprecated": True, "release_date": "2022-11-30"},
        {"value": "gpt-3.5-turbo-16k", "label": "GPT-3.5 Turbo 16K", "deprecated": True, "release_date": "2023-06-13"},
        {"value": "gpt-3.5-turbo-1106", "label": "GPT-3.5 Turbo (1106)", "deprecated": True, "release_date": "2023-11-06"},
        {"value": "text-embedding-3-large", "label": "Text Embedding 3 Large", "deprecated": True, "release_date": "2024-01-25"},
        {"value": "text-embedding-3-small", "label": "Text Embedding 3 Small", "deprecated": True, "release_date": "2024-01-25"},
        {"value": "text-embedding-ada-002", "label": "Text Embedding Ada 002", "deprecated": True, "release_date": "2022-12-15"},
    ],
    "GOOGLE": [
        # Modern models (post-June 2024)
        {"value": "gemini-2.5-pro-preview-06-05", "label": "Gemini 2.5 Pro Preview (06-05)", "modern": True, "release_date": "2025-06-05"},
        {"value": "gemini-2.5-flash-preview-05-20", "label": "Gemini 2.5 Flash Preview (05-20)", "modern": True, "release_date": "2025-05-20"},
        {"value": "gemini-2.5-flash-preview-tts", "label": "Gemini 2.5 Flash Preview TTS", "modern": True, "release_date": "2025-05-20"},
        {"value": "gemini-2.5-pro-preview-tts", "label": "Gemini 2.5 Pro Preview TTS", "modern": True, "release_date": "2025-06-05"},
        {"value": "gemini-2.5-pro-exp-03-25", "label": "Gemini 2.5 Pro Exp (03-25)", "modern": True, "release_date": "2025-03-25"},
        {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash", "modern": True, "release_date": "2024-12-11"},
        {"value": "gemini-2.0-flash-preview-image-generation", "label": "Gemini 2.0 Flash Preview Image Generation", "modern": True, "release_date": "2024-12-11"},
        {"value": "gemini-2.0-flash-thinking-exp", "label": "Gemini 2.0 Flash Thinking Exp", "modern": True, "release_date": "2024-12-11"},
        {"value": "gemini-2.0-pro-experimental", "label": "Gemini 2.0 Pro Experimental", "modern": True, "release_date": "2024-12-11"},
        {"value": "gemini-2.0-flash-lite", "label": "Gemini 2.0 Flash Lite", "modern": True, "release_date": "2024-12-11"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "gemini-1.5-pro", "label": "Gemini 1.5 Pro", "deprecated": True, "release_date": "2024-02-15"},
        {"value": "gemini-1.5-flash", "label": "Gemini 1.5 Flash", "deprecated": True, "release_date": "2024-05-14"},
        {"value": "gemini-pro", "label": "Gemini Pro", "deprecated": True, "release_date": "2023-12-13"},
        {"value": "gemini-pro-vision", "label": "Gemini Pro Vision", "deprecated": True, "release_date": "2023-12-13"},
        {"value": "text-bison", "label": "Text Bison", "deprecated": True, "release_date": "2023-05-10"},
        {"value": "chat-bison", "label": "Chat Bison", "deprecated": True, "release_date": "2023-05-10"},
    ],
    "GROQ": [
        # Modern models (post-June 2024)
        {"value": "compound-beta", "label": "Compound Beta", "modern": True, "release_date": "2024-10-01"},
        {"value": "kimi-k2-instruct", "label": "Kimi K2 Instruct", "modern": True, "release_date": "2024-10-01"},
        {"value": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile", "modern": True, "release_date": "2024-12-06"},
        {"value": "llama-3.1-70b-versatile", "label": "Llama 3.1 70B Versatile", "modern": True, "release_date": "2024-07-23"},
        {"value": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant", "modern": True, "release_date": "2024-07-23"},
        {"value": "gemma2-9b-it", "label": "Gemma 2 9B IT", "modern": True, "release_date": "2024-06-27"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "mixtral-8x7b-32768", "label": "Mixtral 8x7B", "deprecated": True, "release_date": "2023-12-11"},
        {"value": "gemma-7b-it", "label": "Gemma 7B IT", "deprecated": True, "release_date": "2024-02-21"},
    ],
    "MISTRALAI": [
        # Modern models (post-June 2024)
        {"value": "mistral-large-latest", "label": "Mistral Large (Latest)", "modern": True, "release_date": "2024-02-26"},
        {"value": "mistral-medium-latest", "label": "Mistral Medium (Latest)", "modern": True, "release_date": "2024-02-26"},
        {"value": "mistral-small-latest", "label": "Mistral Small (Latest)", "modern": True, "release_date": "2024-02-26"},
        {"value": "mixtral-8x22b-instruct", "label": "Mixtral 8x22B Instruct", "modern": True, "release_date": "2024-04-17"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "mistral-tiny", "label": "Mistral Tiny", "deprecated": True, "release_date": "2023-09-27"},
        {"value": "mistral-7b-instruct", "label": "Mistral 7B Instruct", "deprecated": True, "release_date": "2023-09-27"},
        {"value": "mixtral-8x7b-instruct", "label": "Mixtral 8x7B Instruct", "deprecated": True, "release_date": "2023-12-11"},
    ],
    "OPENAI_AZURE": [
        # Modern models (post-June 2024)
        {"value": "gpt-4o", "label": "GPT-4o (Azure)", "modern": True, "release_date": "2024-05-13"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "gpt-4-turbo", "label": "GPT-4 Turbo (Azure)", "deprecated": True, "release_date": "2023-11-06"},
        {"value": "gpt-4", "label": "GPT-4 (Azure)", "deprecated": True, "release_date": "2023-03-14"},
        {"value": "gpt-35-turbo", "label": "GPT-3.5 Turbo (Azure)", "deprecated": True, "release_date": "2022-11-30"},
        {"value": "gpt-35-turbo-16k", "label": "GPT-3.5 Turbo 16K (Azure)", "deprecated": True, "release_date": "2023-06-13"},
    ],
    "DEEPSEEK": [
        # Modern models (post-June 2024)
        {"value": "deepseek-v3", "label": "DeepSeek V3", "modern": True, "release_date": "2024-12-26"},
        {"value": "deepseek-chat", "label": "DeepSeek Chat", "modern": True, "release_date": "2024-05-06"},
        {"value": "deepseek-coder", "label": "DeepSeek Coder", "modern": True, "release_date": "2024-05-06"},
    ],
    "OPENROUTER": [
        # Modern models (using modern base models)
        {"value": "anthropic/claude-3.5-sonnet", "label": "Claude 3.5 Sonnet (OR)", "modern": True, "release_date": "2024-06-21"},
        {"value": "openai/gpt-4o", "label": "GPT-4o (OR)", "modern": True, "release_date": "2024-05-13"},
        {"value": "google/gemini-1.5-pro", "label": "Gemini 1.5 Pro (OR)", "modern": True, "release_date": "2024-02-15"},
        {"value": "meta-llama/llama-3.1-70b-instruct", "label": "Llama 3.1 70B (OR)", "modern": True, "release_date": "2024-07-23"},
        {"value": "qwen/qwen-2.5-72b-instruct", "label": "Qwen 2.5 72B (OR)", "modern": True, "release_date": "2024-09-19"},
        {"value": "mistralai/mistral-large", "label": "Mistral Large (OR)", "modern": True, "release_date": "2024-02-26"},
    ],
    "SAMBANOVA": [
        # Modern models (post-June 2024)
        {"value": "Meta-Llama-3.1-70B-Instruct", "label": "Llama 3.1 70B Instruct", "modern": True, "release_date": "2024-07-23"},
        {"value": "Meta-Llama-3.1-8B-Instruct", "label": "Llama 3.1 8B Instruct", "modern": True, "release_date": "2024-07-23"},
        {"value": "Meta-Llama-3.2-1B-Instruct", "label": "Llama 3.2 1B Instruct", "modern": True, "release_date": "2024-09-25"},
        {"value": "Meta-Llama-3.2-3B-Instruct", "label": "Llama 3.2 3B Instruct", "modern": True, "release_date": "2024-09-25"},
    ],
    "XAI": [
        # Modern models (post-June 2024)
        {"value": "grok-4-latest", "label": "Grok 4 (Latest)", "modern": True, "release_date": "2025-07-09"},
        {"value": "grok-4-0709", "label": "Grok 4 (0709)", "modern": True, "release_date": "2025-07-09"},
        {"value": "grok-3", "label": "Grok 3", "modern": True, "release_date": "2025-02-17"},
        {"value": "grok-3-fast", "label": "Grok 3 Fast", "modern": True, "release_date": "2025-02-17"},
        {"value": "grok-3-mini", "label": "Grok 3 Mini", "modern": True, "release_date": "2025-02-17"},
        {"value": "grok-3-mini-fast", "label": "Grok 3 Mini Fast", "modern": True, "release_date": "2025-02-17"},
        {"value": "grok-2-1212", "label": "Grok 2 (1212)", "modern": True, "release_date": "2024-08-14"},
        {"value": "grok-2-vision-1212", "label": "Grok 2 Vision (1212)", "modern": True, "release_date": "2024-08-14"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "grok-beta", "label": "Grok Beta", "deprecated": True, "release_date": "2023-11-03"},
    ],
    "PERPLEXITY": [
        # Modern models (post-June 2024)
        {"value": "sonar-reasoning-pro", "label": "Sonar Reasoning Pro", "modern": True, "release_date": "2025-02-11"},
        {"value": "sonar-pro", "label": "Sonar Pro", "modern": True, "release_date": "2025-02-11"},
        {"value": "llama-3.1-sonar-small-128k-online", "label": "Llama 3.1 Sonar Small 128K", "modern": True, "release_date": "2024-07-23"},
        {"value": "llama-3.1-sonar-large-128k-online", "label": "Llama 3.1 Sonar Large 128K", "modern": True, "release_date": "2024-07-23"},
        {"value": "llama-3.1-sonar-huge-128k-online", "label": "Llama 3.1 Sonar Huge 128K", "modern": True, "release_date": "2024-07-23"},
    ],
    "HUGGINGFACE": [
        # Legacy models (pre-June 2024) - deprecated
        {"value": "microsoft/DialoGPT-medium", "label": "DialoGPT Medium", "deprecated": True, "release_date": "2019-11-05"},
        {"value": "microsoft/DialoGPT-large", "label": "DialoGPT Large", "deprecated": True, "release_date": "2019-11-05"},
        {"value": "facebook/blenderbot-400M-distill", "label": "BlenderBot 400M", "deprecated": True, "release_date": "2021-04-29"},
        {"value": "meta-llama/Llama-2-7b-chat-hf", "label": "Llama 2 7B Chat", "deprecated": True, "release_date": "2023-07-18"},
        {"value": "meta-llama/Llama-2-13b-chat-hf", "label": "Llama 2 13B Chat", "deprecated": True, "release_date": "2023-07-18"},
    ],
    "OLLAMA": [
        # Modern models (post-June 2024)
        {"value": "llama3.2", "label": "Llama 3.2", "modern": True, "release_date": "2024-09-25"},
        {"value": "llama3.1", "label": "Llama 3.1", "modern": True, "release_date": "2024-07-23"},
        {"value": "llama3", "label": "Llama 3", "modern": True, "release_date": "2024-04-18"},
        {"value": "phi3", "label": "Phi 3", "modern": True, "release_date": "2024-04-23"},
        {"value": "gemma", "label": "Gemma", "modern": True, "release_date": "2024-02-21"},
        {"value": "qwen2", "label": "Qwen 2", "modern": True, "release_date": "2024-06-07"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "llama2", "label": "Llama 2", "deprecated": True, "release_date": "2023-07-18"},
        {"value": "mistral", "label": "Mistral", "deprecated": True, "release_date": "2023-09-27"},
        {"value": "mixtral", "label": "Mixtral", "deprecated": True, "release_date": "2023-12-11"},
        {"value": "codellama", "label": "Code Llama", "deprecated": True, "release_date": "2023-08-24"},
    ],
    "LMSTUDIO": [
        # Modern models (post-June 2024)
        {"value": "llama-3.2-1b-instruct", "label": "Llama 3.2 1B Instruct", "modern": True, "release_date": "2024-09-25"},
        {"value": "llama-3.2-3b-instruct", "label": "Llama 3.2 3B Instruct", "modern": True, "release_date": "2024-09-25"},
        {"value": "phi-3-mini-4k-instruct", "label": "Phi 3 Mini 4K Instruct", "modern": True, "release_date": "2024-04-23"},
        {"value": "gemma-2-2b-instruct", "label": "Gemma 2 2B Instruct", "modern": True, "release_date": "2024-06-27"},
        # Legacy models (pre-June 2024) - deprecated
        {"value": "mistral-7b-instruct", "label": "Mistral 7B Instruct", "deprecated": True, "release_date": "2023-09-27"},
    ],
    "CHUTES": [
        # Using modern base models
        {"value": "gpt-4", "label": "GPT-4 (Chutes)", "deprecated": True, "release_date": "2023-03-14"},
        {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo (Chutes)", "deprecated": True, "release_date": "2022-11-30"},
        {"value": "claude-3-sonnet", "label": "Claude 3 Sonnet (Chutes)", "deprecated": True, "release_date": "2024-03-04"},
    ],
    "META": [
        # Modern models (post-June 2024)
        {"value": "llama-3.3", "label": "LLaMA 3.3", "modern": True, "release_date": "2024-12-06"},
        {"value": "llama-3.3-70b-instruct", "label": "Llama 3.3 70B Instruct", "modern": True, "release_date": "2024-12-06"},
        {"value": "llama-3.2-11b-vision-instruct", "label": "Llama 3.2 11B Vision", "modern": True, "release_date": "2024-09-25"},
        {"value": "llama-3.2-90b-vision-instruct", "label": "Llama 3.2 90B Vision", "modern": True, "release_date": "2024-09-25"},
        {"value": "llama-3.1-405b-instruct", "label": "Llama 3.1 405B Instruct", "modern": True, "release_date": "2024-07-23"},
    ],
    "OTHER": [
        {"value": "custom-model-1", "label": "Custom Model 1"},
        {"value": "custom-model-2", "label": "Custom Model 2"},
    ],
}


def get_models_for_provider(provider_name: str) -> list[dict[str, str]]:
    """Get available models for a specific provider.
    
    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')
        
    Returns:
        List of model dictionaries with 'value' and 'label' keys
    """
    return MODEL_CATALOG.get(provider_name, [])


def get_modern_models_for_provider(provider_name: str) -> list[dict[str, str]]:
    """Get modern models (post-June 2024) for a specific provider.
    
    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')
        
    Returns:
        List of modern model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    return [model for model in provider_models if model.get("modern", False)]


def get_deprecated_models_for_provider(provider_name: str) -> list[dict[str, str]]:
    """Get deprecated models (pre-June 2024) for a specific provider.
    
    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')
        
    Returns:
        List of deprecated model dictionaries
    """
    provider_models = get_models_for_provider(provider_name)
    return [model for model in provider_models if model.get("deprecated", False)]


def get_all_models() -> list[dict[str, str]]:
    """Get all available models across all providers.
    
    Returns:
        List of all model dictionaries with 'value' and 'label' keys
    """
    all_models = []
    for provider_models in MODEL_CATALOG.values():
        all_models.extend(provider_models)
    return all_models


def get_all_modern_models() -> list[dict[str, str]]:
    """Get all modern models (post-June 2024) across all providers.
    
    Returns:
        List of all modern model dictionaries
    """
    all_models = get_all_models()
    return [model for model in all_models if model.get("modern", False)]


def get_all_deprecated_models() -> list[dict[str, str]]:
    """Get all deprecated models (pre-June 2024) across all providers.
    
    Returns:
        List of all deprecated model dictionaries
    """
    all_models = get_all_models()
    return [model for model in all_models if model.get("deprecated", False)]


def get_recommended_model_for_provider(provider_name: str) -> dict[str, str] | None:
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
