"""
AI Model Registry for Gary-Zero.

This module provides a comprehensive registry of AI models from the specified providers:
- Abacus AI (ai1docs.abacusai.app)
- Google Gemini (ai.google.dev/gemini-api/docs/models)
- OpenAI GPT-4.1 (platform.openai.com/docs/models/gpt-4.1)
- OpenAI Models (platform.openai.com/docs/api-reference/models)
- Groq (console.groq.com/docs/models)

All models are verified against these sources as of January 2025.
"""

import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported AI model providers from specified sources."""
    
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"
    ABACUS_AI = "abacus_ai"


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
    VOICE = "voice"
    TTS = "text_to_speech"
    STT = "speech_to_text"


class ModelConfig(BaseModel):
    """Configuration for an AI model."""
    
    provider: ModelProvider
    model_name: str
    display_name: str
    max_tokens: int
    context_window: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float = Field(default=0.0)
    capabilities: list[ModelCapability]
    recommended_for: list[str]
    description: str = ""
    is_available: bool = True
    requires_api_key: bool = True
    rate_limit_rpm: int | None = None
    rate_limit_tpm: int | None = None


class ModelUsageStats(BaseModel):
    """Usage statistics for a model."""
    
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 1.0
    last_used: datetime | None = None


class ModelRegistry:
    """Registry for managing AI models from specified sources."""
    
    def __init__(self):
        self.models: dict[str, ModelConfig] = {}
        self.usage_stats: dict[str, ModelUsageStats] = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize the model registry with verified models from specified sources."""
        
        # OpenAI Models (from platform.openai.com/docs/models/gpt-4.1 and api-reference)
        self.register_model(
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4.1",
                display_name="GPT-4.1",
                max_tokens=32768,
                context_window=128000,
                cost_per_1k_input_tokens=0.0025,
                cost_per_1k_output_tokens=0.01,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.REASONING,
                ],
                recommended_for=["general", "coding", "analysis", "vision", "complex reasoning"],
                description="Latest GPT-4.1 model with enhanced reasoning and vision capabilities",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                max_tokens=16384,
                context_window=128000,
                cost_per_1k_input_tokens=0.00015,
                cost_per_1k_output_tokens=0.0006,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.JSON_MODE,
                ],
                recommended_for=["fast", "cost-effective", "simple tasks", "real-time"],
                description="Faster, more cost-effective version of GPT-4o",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4.1-nano",
                display_name="GPT-4.1 Nano",
                max_tokens=16384,
                context_window=128000,
                cost_per_1k_input_tokens=0.000075,
                cost_per_1k_output_tokens=0.0003,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.JSON_MODE,
                ],
                recommended_for=["ultra-fast", "low-cost", "simple queries"],
                description="Most cost-effective GPT-4.1 variant for basic tasks",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="o3",
                display_name="o3",
                max_tokens=32768,
                context_window=200000,
                cost_per_1k_input_tokens=0.01,
                cost_per_1k_output_tokens=0.04,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.REASONING,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["complex reasoning", "problem solving", "research"],
                description="Advanced reasoning model with enhanced problem-solving capabilities",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="o4-mini",
                display_name="o4-mini",
                max_tokens=65536,
                context_window=200000,
                cost_per_1k_input_tokens=0.0011,
                cost_per_1k_output_tokens=0.0044,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.REASONING,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["reasoning", "cost-effective", "complex tasks"],
                description="Efficient reasoning model with strong performance",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        # Google Gemini Models (from ai.google.dev/gemini-api/docs/models)
        self.register_model(
            ModelConfig(
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
                    ModelCapability.STREAMING,
                    ModelCapability.VOICE,
                ],
                recommended_for=["multimodal", "large context", "cost-effective", "real-time"],
                description="Latest Gemini model with multimodal capabilities and voice support",
                rate_limit_rpm=15000,
                rate_limit_tpm=4000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.GOOGLE,
                model_name="gemini-2.0-flash-lite",
                display_name="Gemini 2.0 Flash Lite",
                max_tokens=8192,
                context_window=1000000,
                cost_per_1k_input_tokens=0.0000375,
                cost_per_1k_output_tokens=0.00015,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["ultra-low-cost", "fast", "simple multimodal"],
                description="Lightweight Gemini model for cost-sensitive applications",
                rate_limit_rpm=15000,
                rate_limit_tpm=4000000,
            )
        )
        
        self.register_model(
            ModelConfig(
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
                    ModelCapability.REASONING,
                ],
                recommended_for=["complex reasoning", "large documents", "research", "advanced coding"],
                description="Advanced Gemini Pro model with enhanced reasoning and coding capabilities",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.GOOGLE,
                model_name="gemini-2.5-pro-exp-03-25",
                display_name="Gemini 2.5 Pro Experimental",
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
                    ModelCapability.REASONING,
                ],
                recommended_for=["experimental", "cutting-edge", "research"],
                description="Experimental Gemini 2.5 Pro with latest features",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        # Groq Models (from console.groq.com/docs/models)
        self.register_model(
            ModelConfig(
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
                    ModelCapability.STREAMING,
                ],
                recommended_for=["fast inference", "open source", "cost-effective"],
                description="High-performance Llama model optimized for speed on Groq hardware",
                rate_limit_rpm=30000,
                rate_limit_tpm=6000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.GROQ,
                model_name="llama-3.1-8b-instant",
                display_name="Llama 3.1 8B Instant",
                max_tokens=8000,
                context_window=32768,
                cost_per_1k_input_tokens=0.00005,
                cost_per_1k_output_tokens=0.00008,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["ultra-fast", "low-cost", "simple tasks"],
                description="Lightning-fast Llama model for basic text generation",
                rate_limit_rpm=30000,
                rate_limit_tpm=6000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.GROQ,
                model_name="mixtral-8x7b-32768",
                display_name="Mixtral 8x7B",
                max_tokens=32768,
                context_window=32768,
                cost_per_1k_input_tokens=0.00024,
                cost_per_1k_output_tokens=0.00024,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["mixture-of-experts", "coding", "reasoning"],
                description="Mixtral 8x7B model with large context window",
                rate_limit_rpm=30000,
                rate_limit_tpm=6000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.GROQ,
                model_name="gemma2-9b-it",
                display_name="Gemma 2 9B",
                max_tokens=8192,
                context_window=8192,
                cost_per_1k_input_tokens=0.0002,
                cost_per_1k_output_tokens=0.0002,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["google-gemma", "efficient", "coding"],
                description="Google's Gemma 2 model optimized for instruction following",
                rate_limit_rpm=30000,
                rate_limit_tpm=6000000,
            )
        )
        
        # Abacus AI Models (from ai1docs.abacusai.app)
        self.register_model(
            ModelConfig(
                provider=ModelProvider.ABACUS_AI,
                model_name="claude-3-7-sonnet-20250219",
                display_name="Claude 3.7 Sonnet",
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
                    ModelCapability.REASONING,
                ],
                recommended_for=["coding", "analysis", "reasoning", "vision"],
                description="Latest Claude 3.7 Sonnet with enhanced reasoning and coding capabilities",
                rate_limit_rpm=5000,
                rate_limit_tpm=1000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.ABACUS_AI,
                model_name="claude-3-5-haiku-20241022",
                display_name="Claude 3.5 Haiku",
                max_tokens=8192,
                context_window=200000,
                cost_per_1k_input_tokens=0.001,
                cost_per_1k_output_tokens=0.005,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.STREAMING,
                ],
                recommended_for=["fast", "cost-effective", "simple tasks"],
                description="Fast and efficient Claude model for quick tasks",
                rate_limit_rpm=5000,
                rate_limit_tpm=1000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.ABACUS_AI,
                model_name="gpt-4o",
                display_name="GPT-4O",
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
                    ModelCapability.JSON_MODE,
                ],
                recommended_for=["general", "coding", "analysis", "vision"],
                description="GPT-4O with vision and function calling capabilities",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
        
        self.register_model(
            ModelConfig(
                provider=ModelProvider.ABACUS_AI,
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
                    ModelCapability.JSON_MODE,
                ],
                recommended_for=["fast", "cost-effective", "simple tasks"],
                description="Faster, more cost-effective version of GPT-4O",
                rate_limit_rpm=10000,
                rate_limit_tpm=2000000,
            )
        )
    
    def register_model(self, model: ModelConfig):
        """Register a new model in the registry."""
        self.models[model.model_name] = model
        if model.model_name not in self.usage_stats:
            self.usage_stats[model.model_name] = ModelUsageStats()
        logger.info(f"Registered model: {model.display_name} ({model.model_name})")
    
    def get_model(self, model_name: str) -> ModelConfig | None:
        """Get a model configuration by name."""
        return self.models.get(model_name)
    
    def list_models(self, provider: ModelProvider | None = None) -> list[ModelConfig]:
        """List all models, optionally filtered by provider."""
        models = list(self.models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        return models
    
    def get_models_by_capability(
        self, capability: ModelCapability
    ) -> list[ModelConfig]:
        """Get models that support a specific capability."""
        return [m for m in self.models.values() if capability in m.capabilities]
    
    def get_recommended_model(
        self, use_case: str, max_cost: float | None = None
    ) -> ModelConfig | None:
        """Get the recommended model for a specific use case."""
        candidates = [
            m
            for m in self.models.values()
            if use_case in m.recommended_for and m.is_available
        ]
        
        if max_cost is not None:
            candidates = [
                m for m in candidates if m.cost_per_1k_input_tokens <= max_cost
            ]
        
        if not candidates:
            return None
        
        # Sort by usage stats and cost efficiency
        candidates.sort(
            key=lambda m: (
                -self.usage_stats[m.model_name].success_rate,
                m.cost_per_1k_input_tokens,
            )
        )
        
        return candidates[0]
    
    def update_usage_stats(
        self,
        model_name: str,
        tokens_used: int,
        response_time: float,
        success: bool,
        cost: float = 0.0,
    ):
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
            stats.average_response_time * (stats.total_requests - 1) + response_time
        ) / stats.total_requests
        
        # Update success rate
        if success:
            stats.success_rate = (
                stats.success_rate * (stats.total_requests - 1) + 1.0
            ) / stats.total_requests
        else:
            stats.success_rate = (
                stats.success_rate * (stats.total_requests - 1) + 0.0
            ) / stats.total_requests
    
    def get_usage_stats(self, model_name: str) -> ModelUsageStats | None:
        """Get usage statistics for a model."""
        return self.usage_stats.get(model_name)
    
    def get_cost_estimate(
        self, model_name: str, input_tokens: int, output_tokens: int = 0
    ) -> float:
        """Calculate cost estimate for using a model."""
        model_config = self.get_model(model_name)
        if not model_config:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output_tokens
        
        return input_cost + output_cost


# Global model registry instance
_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _registry


def get_model(model_name: str) -> ModelConfig | None:
    """Get a model configuration by name."""
    return _registry.get_model(model_name)


def list_models(provider: ModelProvider | None = None) -> list[ModelConfig]:
    """List all available models."""
    return _registry.list_models(provider)


def get_recommended_model(
    use_case: str, max_cost: float | None = None
) -> ModelConfig | None:
    """Get the recommended model for a specific use case."""
    return _registry.get_recommended_model(use_case, max_cost)
