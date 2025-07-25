"""AI Model Registry for Gary-Zero."""

# Import necessary classes from the main models.py file
import os
import sys

# Add the parent directory to sys.path to import from models.py
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Import from the models.py file in the parent directory
    import importlib.util
    import os
    
    models_py_path = os.path.join(parent_dir, 'models.py')
    spec = importlib.util.spec_from_file_location("models_module", models_py_path)
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)

    ModelProvider = models_module.ModelProvider
    ModelType = models_module.ModelType
    get_api_key = models_module.get_api_key
    get_model = models_module.get_model
    get_rate_limiter = models_module.get_rate_limiter
    parse_chunk = models_module.parse_chunk
    
    # Export all provider-specific functions
    get_anthropic_chat = models_module.get_anthropic_chat
    get_anthropic_embedding = models_module.get_anthropic_embedding
    get_deepseek_chat = models_module.get_deepseek_chat
    get_google_chat = models_module.get_google_chat
    get_google_embedding = models_module.get_google_embedding
    get_groq_chat = models_module.get_groq_chat
    get_huggingface_chat = models_module.get_huggingface_chat
    get_huggingface_embedding = models_module.get_huggingface_embedding
    get_lmstudio_chat = models_module.get_lmstudio_chat
    get_lmstudio_embedding = models_module.get_lmstudio_embedding
    get_meta_chat = models_module.get_meta_chat
    get_meta_embedding = models_module.get_meta_embedding
    get_mistralai_chat = models_module.get_mistralai_chat
    get_ollama_chat = models_module.get_ollama_chat
    get_ollama_embedding = models_module.get_ollama_embedding
    get_openai_azure_chat = models_module.get_openai_azure_chat
    get_openai_azure_embedding = models_module.get_openai_azure_embedding
    get_openai_chat = models_module.get_openai_chat
    get_openai_embedding = models_module.get_openai_embedding
    get_openrouter_chat = models_module.get_openrouter_chat
    get_openrouter_embedding = models_module.get_openrouter_embedding
    get_qwen_chat = models_module.get_qwen_chat
    get_qwen_embedding = models_module.get_qwen_embedding
    get_sambanova_chat = models_module.get_sambanova_chat
    get_sambanova_embedding = models_module.get_sambanova_embedding
    get_xai_chat = models_module.get_xai_chat
    get_xai_embedding = models_module.get_xai_embedding
except (ImportError, AttributeError):
    # Fallback definitions if main models.py is not available
    from enum import Enum

    class ModelProvider(Enum):
        ANTHROPIC = "Anthropic"
        OPENAI = "OpenAI"
        GOOGLE = "Google"
        GROQ = "Groq"
        MISTRALAI = "Mistral AI"
        OTHER = "Other"

    class ModelType(Enum):
        CHAT = "Chat"
        EMBEDDING = "Embedding"

    def get_api_key(service):
        return None

    def get_model(model_type, provider, name, **kwargs):
        return None
    
    def get_rate_limiter(provider, name, requests, input_tokens, output_tokens):
        from framework.helpers.rate_limiter import RateLimiter
        return RateLimiter(
            requests=requests or 1000,
            input_tokens=input_tokens or 1000000,
            output_tokens=output_tokens or 1000000
        )
    
    def parse_chunk(chunk):
        if isinstance(chunk, str):
            return chunk
        elif hasattr(chunk, "content"):
            return str(chunk.content)
        else:
            return str(chunk)
