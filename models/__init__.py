"""AI Model Registry for Gary-Zero."""

# Import necessary classes from the main models.py file
import sys
import os

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
except (ImportError, AttributeError) as e:
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