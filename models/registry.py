"""
AI Model Registry for Gary-Zero.

This module provides a comprehensive registry of AI models from multiple providers
with capabilities, configuration, and performance tracking.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MISTRAL = "mistral"
    GROQ = "groq"
    OLLAMA = "ollama"
    CUSTOM = "custom"

class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    REASONING = "reasoning"
    SEARCH = "search"
    EMBEDDINGS = "embeddings"

class ModelConfig(BaseModel):
    """Configuration for an AI model."""
    provider: ModelProvider
    model_name: str
    display_name: str
    max_tokens: int
    context_window: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float = Field(default=0.0)
    capabilities: List[ModelCapability]
    recommended_for: List[str]
    description: str = ""
    is_available: bool = True
    requires_api_key: bool = True
    rate_limit_rpm: Optional[int] = None
    rate_limit_tpm: Optional[int] = None

class ModelUsageStats(BaseModel):
    """Usage statistics for a model."""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 1.0
    last_used: Optional[datetime] = None

class ModelRegistry:
    """Registry for managing AI models and their configurations."""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.usage_stats: Dict[str, ModelUsageStats] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the model registry with supported models."""
        
        # OpenAI Models
        self.register_model(ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            display_name="GPT-4O (Latest)",
            max_tokens=4096,
            context_window=128000,
            cost_per_1k_input_tokens=0.0025,
            cost_per_1k_output_tokens=0.01,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.JSON_MODE
            ],
            recommended_for=["general", "coding", "analysis", "vision"],
            description="Latest GPT-4O model with vision and function calling capabilities",
            rate_limit_rpm=10000,
            rate_limit_tpm=2000000
        ))
        
        self.register_model(ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            display_name="GPT-4O Mini",
            max_tokens=4096,
            context_window=128000,
            cost_per_1k_input_tokens=0.00015,
            cost_per_1k_output_tokens=0.0006,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING,
                ModelCapability.JSON_MODE
            ],
            recommended_for=["fast", "cost-effective", "simple tasks"],
            description="Faster, more cost-effective version of GPT-4O",
            rate_limit_rpm=10000,
            rate_limit_tpm=2000000
        ))
        
        # Anthropic Models
        self.register_model(ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            display_name="Claude 3.5 Sonnet",
            max_tokens=8192,
            context_window=200000,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.REASONING
            ],
            recommended_for=["coding", "analysis", "reasoning", "long documents"],
            description="Advanced Claude model with excellent coding and reasoning capabilities",
            rate_limit_rpm=5000,
            rate_limit_tpm=1000000
        ))
        
        self.register_model(ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-5-haiku-20241022",
            display_name="Claude 3.5 Haiku",
            max_tokens=8192,
            context_window=200000,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.005,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING
            ],
            recommended_for=["fast", "cost-effective", "simple tasks"],
            description="Fast and efficient Claude model for quick tasks",
            rate_limit_rpm=5000,
            rate_limit_tpm=1000000
        ))
        
        # Google Models
        self.register_model(ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_name="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            max_tokens=8192,
            context_window=1000000,
            cost_per_1k_input_tokens=0.000075,
            cost_per_1k_output_tokens=0.0003,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING
            ],
            recommended_for=["multimodal", "large context", "cost-effective"],
            description="Latest Gemini model with large context window and multimodal capabilities",
            rate_limit_rpm=15000,
            rate_limit_tpm=4000000
        ))
        
        self.register_model(ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_name="gemini-2.5-pro",
            display_name="Gemini 2.5 Pro",
            max_tokens=8192,
            context_window=2000000,
            cost_per_1k_input_tokens=0.00125,
            cost_per_1k_output_tokens=0.005,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.REASONING
            ],
            recommended_for=["complex reasoning", "large documents", "research"],
            description="Advanced Gemini Pro model with enhanced reasoning capabilities",
            rate_limit_rpm=10000,
            rate_limit_tpm=2000000
        ))
        
        # Groq Models
        self.register_model(ModelConfig(
            provider=ModelProvider.GROQ,
            model_name="llama-3.3-70b-versatile",
            display_name="Llama 3.3 70B",
            max_tokens=8000,
            context_window=32768,
            cost_per_1k_input_tokens=0.00059,
            cost_per_1k_output_tokens=0.00079,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING
            ],
            recommended_for=["fast inference", "open source", "cost-effective"],
            description="High-performance Llama model optimized for speed on Groq hardware",
            rate_limit_rpm=30000,
            rate_limit_tpm=6000000
        ))
        
        # Mistral Models
        self.register_model(ModelConfig(
            provider=ModelProvider.MISTRAL,
            model_name="mistral-large-2407",
            display_name="Mistral Large",
            max_tokens=8192,
            context_window=128000,
            cost_per_1k_input_tokens=0.002,
            cost_per_1k_output_tokens=0.006,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING
            ],
            recommended_for=["multilingual", "coding", "reasoning"],
            description="Large Mistral model with strong multilingual and coding capabilities",
            rate_limit_rpm=5000,
            rate_limit_tpm=1000000
        ))
        
        # Ollama Local Models
        self.register_model(ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name="llama3.1:8b",
            display_name="Llama 3.1 8B (Local)",
            max_tokens=4096,
            context_window=32768,
            cost_per_1k_input_tokens=0.0,  # Local model, no cost
            cost_per_1k_output_tokens=0.0,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING
            ],
            recommended_for=["local", "privacy", "offline"],
            description="Local Llama model running on Ollama for privacy and offline use",
            requires_api_key=False,
            rate_limit_rpm=None,  # No rate limits for local models
            rate_limit_tpm=None
        ))
    
    def register_model(self, model: ModelConfig):
        """Register a new model in the registry."""
        self.models[model.model_name] = model
        if model.model_name not in self.usage_stats:
            self.usage_stats[model.model_name] = ModelUsageStats()
        logger.info(f"Registered model: {model.display_name} ({model.model_name})")
    
    def get_model(self, model_name: str) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        return self.models.get(model_name)
    
    def list_models(self, provider: Optional[ModelProvider] = None) -> List[ModelConfig]:
        """List all models, optionally filtered by provider."""
        models = list(self.models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        return models
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelConfig]:
        """Get models that support a specific capability."""
        return [m for m in self.models.values() if capability in m.capabilities]
    
    def get_recommended_model(self, use_case: str, max_cost: Optional[float] = None) -> Optional[ModelConfig]:
        """Get the recommended model for a specific use case."""
        candidates = [
            m for m in self.models.values() 
            if use_case in m.recommended_for and m.is_available
        ]
        
        if max_cost is not None:
            candidates = [
                m for m in candidates 
                if m.cost_per_1k_input_tokens <= max_cost
            ]
        
        if not candidates:
            return None
        
        # Sort by usage stats and cost efficiency
        candidates.sort(key=lambda m: (
            -self.usage_stats[m.model_name].success_rate,
            m.cost_per_1k_input_tokens
        ))
        
        return candidates[0]
    
    def update_usage_stats(self, model_name: str, tokens_used: int, 
                          response_time: float, success: bool, cost: float = 0.0):
        """Update usage statistics for a model."""
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = ModelUsageStats()
        
        stats = self.usage_stats[model_name]
        stats.total_requests += 1
        stats.total_tokens += tokens_used
        stats.total_cost += cost
        stats.last_used = datetime.now()
        
        # Update average response time
        stats.average_response_time = (
            (stats.average_response_time * (stats.total_requests - 1) + response_time) /
            stats.total_requests
        )
        
        # Update success rate
        if success:
            stats.success_rate = (
                (stats.success_rate * (stats.total_requests - 1) + 1.0) /
                stats.total_requests
            )
        else:
            stats.success_rate = (
                (stats.success_rate * (stats.total_requests - 1) + 0.0) /
                stats.total_requests
            )
    
    def get_usage_stats(self, model_name: str) -> Optional[ModelUsageStats]:
        """Get usage statistics for a model."""
        return self.usage_stats.get(model_name)
    
    def get_cost_estimate(self, model_name: str, input_tokens: int, output_tokens: int = 0) -> float:
        """Calculate cost estimate for using a model."""
        model = self.get_model(model_name)
        if not model:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output_tokens
        
        return input_cost + output_cost

# Global model registry instance
_registry = ModelRegistry()

def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _registry

def get_model(model_name: str) -> Optional[ModelConfig]:
    """Get a model configuration by name."""
    return _registry.get_model(model_name)

def list_models(provider: Optional[ModelProvider] = None) -> List[ModelConfig]:
    """List all available models."""
    return _registry.list_models(provider)

def get_recommended_model(use_case: str, max_cost: Optional[float] = None) -> Optional[ModelConfig]:
    """Get the recommended model for a specific use case."""
    return _registry.get_recommended_model(use_case, max_cost)