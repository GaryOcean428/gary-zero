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
    import models as models_module

    ModelProvider = models_module.ModelProvider
    ModelType = models_module.ModelType
    get_api_key = models_module.get_api_key
    get_model = models_module.get_model
    get_rate_limiter = models_module.get_rate_limiter
    parse_chunk = models_module.parse_chunk
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
