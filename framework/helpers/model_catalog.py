"""Model catalog with available models for each provider.

This module provides a comprehensive mapping of AI models available
for each provider, used to populate dropdown selections in the UI.
"""

from typing import Dict, List

# Comprehensive model catalog organized by provider
MODEL_CATALOG: Dict[str, List[Dict[str, str]]] = {
    "ANTHROPIC": [
        {"value": "claude-3-5-sonnet-latest", "label": "Claude 3.5 Sonnet (Latest)"},
        {"value": "claude-3-5-haiku-latest", "label": "Claude 3.5 Haiku (Latest)"},
        {"value": "claude-3-7-sonnet-20250219", "label": "Claude 3.7 Sonnet (2025-02-19)"},
        {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (2024-10-22)"},
        {"value": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (2024-10-22)"},
        {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
        {"value": "claude-3-sonnet-20240229", "label": "Claude 3 Sonnet"},
        {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku"},
        {"value": "claude-2.1", "label": "Claude 2.1"},
        {"value": "claude-2.0", "label": "Claude 2.0"},
        {"value": "claude-instant-1.2", "label": "Claude Instant 1.2"},
    ],
    "OPENAI": [
        {"value": "gpt-4o", "label": "GPT-4o (Latest)"},
        {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
        {"value": "gpt-4o-realtime-preview", "label": "GPT-4o Realtime Preview"},
        {"value": "chatgpt-4.1", "label": "ChatGPT-4.1"},
        {"value": "gpt-4.1", "label": "GPT-4.1"},
        {"value": "gpt-4.1-vision", "label": "GPT-4.1 Vision"},
        {"value": "gpt-4.1-embeddings", "label": "GPT-4.1 Embeddings"},
        {"value": "o1", "label": "o1"},
        {"value": "o1-mini", "label": "o1 Mini"},
        {"value": "o1-pro", "label": "o1 Pro"},
        {"value": "o3", "label": "o3"},
        {"value": "o3-mini", "label": "o3 Mini"},
        {"value": "o4-mini", "label": "o4 Mini"},
        {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
        {"value": "gpt-4-turbo-preview", "label": "GPT-4 Turbo Preview"},
        {"value": "gpt-4", "label": "GPT-4"},
        {"value": "gpt-4-32k", "label": "GPT-4 32K"},
        {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
        {"value": "gpt-3.5-turbo-16k", "label": "GPT-3.5 Turbo 16K"},
        {"value": "gpt-3.5-turbo-1106", "label": "GPT-3.5 Turbo (1106)"},
        {"value": "text-embedding-3-large", "label": "Text Embedding 3 Large"},
        {"value": "text-embedding-3-small", "label": "Text Embedding 3 Small"},
        {"value": "text-embedding-ada-002", "label": "Text Embedding Ada 002"},
    ],
    "GOOGLE": [
        {"value": "gemini-2.5-pro-exp-03-25", "label": "Gemini 2.5 Pro Exp (03-25)"},
        {"value": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
        {"value": "gemini-1.5-flash", "label": "Gemini 1.5 Flash"},
        {"value": "gemini-pro", "label": "Gemini Pro"},
        {"value": "gemini-pro-vision", "label": "Gemini Pro Vision"},
        {"value": "text-bison", "label": "Text Bison"},
        {"value": "chat-bison", "label": "Chat Bison"},
    ],
    "GROQ": [
        {"value": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile"},
        {"value": "llama-3.1-70b-versatile", "label": "Llama 3.1 70B Versatile"},
        {"value": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant"},
        {"value": "mixtral-8x7b-32768", "label": "Mixtral 8x7B"},
        {"value": "gemma-7b-it", "label": "Gemma 7B IT"},
        {"value": "gemma2-9b-it", "label": "Gemma 2 9B IT"},
    ],
    "MISTRALAI": [
        {"value": "mistral-large-latest", "label": "Mistral Large (Latest)"},
        {"value": "mistral-medium-latest", "label": "Mistral Medium (Latest)"},
        {"value": "mistral-small-latest", "label": "Mistral Small (Latest)"},
        {"value": "mistral-tiny", "label": "Mistral Tiny"},
        {"value": "mistral-7b-instruct", "label": "Mistral 7B Instruct"},
        {"value": "mixtral-8x7b-instruct", "label": "Mixtral 8x7B Instruct"},
        {"value": "mixtral-8x22b-instruct", "label": "Mixtral 8x22B Instruct"},
    ],
    "OPENAI_AZURE": [
        {"value": "gpt-4o", "label": "GPT-4o (Azure)"},
        {"value": "gpt-4-turbo", "label": "GPT-4 Turbo (Azure)"},
        {"value": "gpt-4", "label": "GPT-4 (Azure)"},
        {"value": "gpt-35-turbo", "label": "GPT-3.5 Turbo (Azure)"},
        {"value": "gpt-35-turbo-16k", "label": "GPT-3.5 Turbo 16K (Azure)"},
    ],
    "DEEPSEEK": [
        {"value": "deepseek-chat", "label": "DeepSeek Chat"},
        {"value": "deepseek-coder", "label": "DeepSeek Coder"},
        {"value": "deepseek-v3", "label": "DeepSeek V3"},
    ],
    "OPENROUTER": [
        {"value": "anthropic/claude-3.5-sonnet", "label": "Claude 3.5 Sonnet (OR)"},
        {"value": "openai/gpt-4o", "label": "GPT-4o (OR)"},
        {"value": "google/gemini-1.5-pro", "label": "Gemini 1.5 Pro (OR)"},
        {"value": "meta-llama/llama-3.1-70b-instruct", "label": "Llama 3.1 70B (OR)"},
        {"value": "qwen/qwen-2.5-72b-instruct", "label": "Qwen 2.5 72B (OR)"},
        {"value": "mistralai/mistral-large", "label": "Mistral Large (OR)"},
    ],
    "SAMBANOVA": [
        {"value": "Meta-Llama-3.1-70B-Instruct", "label": "Llama 3.1 70B Instruct"},
        {"value": "Meta-Llama-3.1-8B-Instruct", "label": "Llama 3.1 8B Instruct"},
        {"value": "Meta-Llama-3.2-1B-Instruct", "label": "Llama 3.2 1B Instruct"},
        {"value": "Meta-Llama-3.2-3B-Instruct", "label": "Llama 3.2 3B Instruct"},
    ],
    "XAI": [
        {"value": "grok-4-latest", "label": "Grok 4 (Latest)"},
        {"value": "grok-3", "label": "Grok 3"},
        {"value": "grok-beta", "label": "Grok Beta"},
        {"value": "grok-2-1212", "label": "Grok 2 (1212)"},
        {"value": "grok-2-vision-1212", "label": "Grok 2 Vision (1212)"},
    ],
    "PERPLEXITY": [
        {"value": "llama-3.1-sonar-small-128k-online", "label": "Llama 3.1 Sonar Small 128K"},
        {"value": "llama-3.1-sonar-large-128k-online", "label": "Llama 3.1 Sonar Large 128K"},
        {"value": "llama-3.1-sonar-huge-128k-online", "label": "Llama 3.1 Sonar Huge 128K"},
    ],
    "HUGGINGFACE": [
        {"value": "microsoft/DialoGPT-medium", "label": "DialoGPT Medium"},
        {"value": "microsoft/DialoGPT-large", "label": "DialoGPT Large"},
        {"value": "facebook/blenderbot-400M-distill", "label": "BlenderBot 400M"},
        {"value": "meta-llama/Llama-2-7b-chat-hf", "label": "Llama 2 7B Chat"},
        {"value": "meta-llama/Llama-2-13b-chat-hf", "label": "Llama 2 13B Chat"},
    ],
    "OLLAMA": [
        {"value": "llama3.2", "label": "Llama 3.2"},
        {"value": "llama3.1", "label": "Llama 3.1"},
        {"value": "llama3", "label": "Llama 3"},
        {"value": "llama2", "label": "Llama 2"},
        {"value": "mistral", "label": "Mistral"},
        {"value": "mixtral", "label": "Mixtral"},
        {"value": "codellama", "label": "Code Llama"},
        {"value": "phi3", "label": "Phi 3"},
        {"value": "gemma", "label": "Gemma"},
        {"value": "qwen2", "label": "Qwen 2"},
    ],
    "LMSTUDIO": [
        {"value": "llama-3.2-1b-instruct", "label": "Llama 3.2 1B Instruct"},
        {"value": "llama-3.2-3b-instruct", "label": "Llama 3.2 3B Instruct"},
        {"value": "mistral-7b-instruct", "label": "Mistral 7B Instruct"},
        {"value": "phi-3-mini-4k-instruct", "label": "Phi 3 Mini 4K Instruct"},
        {"value": "gemma-2-2b-instruct", "label": "Gemma 2 2B Instruct"},
    ],
    "CHUTES": [
        {"value": "gpt-4", "label": "GPT-4 (Chutes)"},
        {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo (Chutes)"},
        {"value": "claude-3-sonnet", "label": "Claude 3 Sonnet (Chutes)"},
    ],
    "META": [
        {"value": "llama-3.3", "label": "LLaMA 3.3"},
        {"value": "llama-3.3-70b-instruct", "label": "Llama 3.3 70B Instruct"},
        {"value": "llama-3.2-11b-vision-instruct", "label": "Llama 3.2 11B Vision"},
        {"value": "llama-3.2-90b-vision-instruct", "label": "Llama 3.2 90B Vision"},
        {"value": "llama-3.1-405b-instruct", "label": "Llama 3.1 405B Instruct"},
    ],
    "OTHER": [
        {"value": "custom-model-1", "label": "Custom Model 1"},
        {"value": "custom-model-2", "label": "Custom Model 2"},
    ],
}


def get_models_for_provider(provider_name: str) -> List[Dict[str, str]]:
    """Get available models for a specific provider.
    
    Args:
        provider_name: The name of the provider (e.g., 'ANTHROPIC', 'OPENAI')
        
    Returns:
        List of model dictionaries with 'value' and 'label' keys
    """
    return MODEL_CATALOG.get(provider_name, [])


def get_all_models() -> List[Dict[str, str]]:
    """Get all available models across all providers.
    
    Returns:
        List of all model dictionaries with 'value' and 'label' keys
    """
    all_models = []
    for provider_models in MODEL_CATALOG.values():
        all_models.extend(provider_models)
    return all_models


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