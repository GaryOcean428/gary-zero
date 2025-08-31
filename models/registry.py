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

import csv
import logging
import os
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
    ANTHROPIC = "anthropic"
    XAI = "xai"


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
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    MODERATION = "moderation"


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
    modern: bool = Field(default=True)
    release_date: str = Field(default="")


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

    def infer_provider(self, model_code: str) -> str:
        code_lower = model_code.lower()
        if any(
            term in code_lower
            for term in [
                "gpt",
                "o1",
                "o3",
                "dall-e",
                "whisper",
                "tts",
                "omni",
                "text-embedding",
            ]
        ):
            return "openai"
        if "gemini" in code_lower or "imagen" in code_lower or "veo" in code_lower:
            return "google"
        if "claude" in code_lower:
            return "anthropic"
        if "grok" in code_lower:
            return "xai"
        if "llama" in code_lower or "mixtral" in code_lower or "gemma" in code_lower:
            return "groq"
        return ""

    def map_features_to_capabilities(
        self,
        features: list[str],
        model_code: str,
        inputs: list[str],
        outputs: list[str],
    ) -> list[ModelCapability]:
        capabilities = set()
        code_lower = model_code.lower()

        # Base on model type
        if any(
            m in code_lower
            for m in [
                "gpt",
                "o1",
                "o3",
                "claude",
                "grok",
                "gemini",
                "llama",
                "mixtral",
                "gemma",
            ]
        ):
            capabilities.add(ModelCapability.TEXT_GENERATION)
        if "embedding" in code_lower:
            capabilities.add(ModelCapability.EMBEDDINGS)
        if "tts" in code_lower:
            capabilities.add(ModelCapability.TTS)
        if "whisper" in code_lower:
            capabilities.add(ModelCapability.STT)
        if any(m in code_lower for m in ["dall-e", "imagen"]):
            capabilities.add(ModelCapability.IMAGE_GENERATION)
        if "veo" in code_lower:
            capabilities.add(ModelCapability.VIDEO_GENERATION)
        if "omni-moderation" in code_lower:
            capabilities.add(ModelCapability.MODERATION)

        # From features
        for feature in features:
            f_lower = feature.lower()
            if any(k in f_lower for k in ["code", "coding"]):
                capabilities.add(ModelCapability.CODE_GENERATION)
            if any(k in f_lower for k in ["function calling", "tool use"]):
                capabilities.add(ModelCapability.FUNCTION_CALLING)
            if any(k in f_lower for k in ["vision", "multimodal"]):
                capabilities.add(ModelCapability.VISION)
            if "streaming" in f_lower:
                capabilities.add(ModelCapability.STREAMING)
            if any(k in f_lower for k in ["json", "structured outputs"]):
                capabilities.add(ModelCapability.JSON_MODE)
            if "reasoning" in f_lower:
                capabilities.add(ModelCapability.REASONING)
            if "search" in f_lower:
                capabilities.add(ModelCapability.SEARCH)
            if any(k in f_lower for k in ["voice", "audio", "realtime"]):
                capabilities.add(ModelCapability.VOICE)
            if "text-to-speech" in f_lower:
                capabilities.add(ModelCapability.TTS)
            if "speech-to-text" in f_lower:
                capabilities.add(ModelCapability.STT)
            if "image generation" in f_lower:
                capabilities.add(ModelCapability.IMAGE_GENERATION)
            if "video generation" in f_lower:
                capabilities.add(ModelCapability.VIDEO_GENERATION)
            if "moderation" in f_lower:
                capabilities.add(ModelCapability.MODERATION)

        # From inputs/outputs
        if any(i in inputs for i in ["image", "video", "audio", "documents"]):
            capabilities.add(ModelCapability.VISION)
        if "audio" in inputs:
            capabilities.add(ModelCapability.STT)
        if "audio" in outputs:
            capabilities.add(ModelCapability.TTS)
        if "images" in outputs:
            capabilities.add(ModelCapability.IMAGE_GENERATION)
        if "videos" in outputs:
            capabilities.add(ModelCapability.VIDEO_GENERATION)
        if "embeddings" in outputs:
            capabilities.add(ModelCapability.EMBEDDINGS)
        if "moderation_scores" in outputs:
            capabilities.add(ModelCapability.MODERATION)

        return list(capabilities)

    def get_costs(self, model_code: str) -> tuple[float, float]:
        cost_map = {
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4.1": (0.01, 0.04),  # Estimated based on advanced capabilities
            "gpt-4.1-mini": (0.0005, 0.002),  # Cost-efficient version
            "gpt-4.1-nano": (0.0002, 0.0008),  # Most cost-effective
            "o1": (0.015, 0.06),
            "o1-preview": (0.015, 0.06),
            "o1-mini": (0.003, 0.012),
            "o3": (0.02, 0.08),  # Advanced reasoning model
            "o3-pro": (0.04, 0.16),  # Enhanced compute version
            "o3-mini": (0.0025, 0.01),
            "o4-mini": (0.002, 0.008),  # Cost-efficient reasoning
            "dall-e-3": (0.04, 0.0),  # per image
            "whisper-1": (0.006, 0.0),  # per minute
            "tts-1": (0.015, 0.0),  # per 1k chars
            "tts-1-hd": (0.03, 0.0),
            "text-embedding-3-small": (0.00002, 0.0),
            "text-embedding-3-large": (0.00013, 0.0),
            "omni-moderation-latest": (0.0, 0.0),  # free
            "gemini-2.5-pro": (0.00125, 0.005),
            "gemini-2.5-flash": (0.000075, 0.0003),
            "gemini-2.5-flash-lite": (0.0000375, 0.00015),
            "gemini-2.5-flash-native-audio": (0.000075, 0.0003),
            "gemini-2.5-flash-preview-tts": (0.000075, 0.0003),
            "gemini-2.5-pro-preview-tts": (0.00125, 0.005),
            "gemini-2.0-flash": (0.000075, 0.0003),
            "gemini-2.0-flash-preview-image-gen": (0.000075, 0.0003),
            "gemini-2.0-flash-lite": (0.0000375, 0.00015),
            "imagen-4": (0.04, 0.0),  # per image approx
            "imagen-3": (0.04, 0.0),
            "veo-3-preview": (0.1, 0.0),  # approx
            "veo-2": (0.1, 0.0),
            "gemini-2.5-flash-live": (0.000075, 0.0003),
            "claude-opus-4-20250514": (0.015, 0.075),
            "claude-sonnet-4-20250514": (0.003, 0.015),
            "claude-3-7-sonnet-20250219": (0.003, 0.015),
            "claude-3-5-sonnet-20241022": (0.003, 0.015),
            "claude-3-5-haiku-20241022": (0.0008, 0.004),
            "grok-4-latest": (0.003, 0.015),
            "grok-3": (0.003, 0.015),
            "grok-3-mini": (0.0003, 0.0005),
            "grok-3-fast": (0.005, 0.025),
            # add more as needed
        }
        return cost_map.get(model_code, (0.001, 0.003))

    def is_modern(self, model_code: str, release_date: str) -> bool:
        legacy_models = [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "text-embedding-ada-002",
            "text-embedding-3",
            "gpt-4o",
            "gpt-4-turbo-preview",
            "gpt-4o-mini-search-preview",
            "claude-2.0",
            "claude-2.1",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "claude-instant-1.2",
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "text-bison",
            "chat-bison",
            "mistral-7b-instruct",
            "mixtral-8x7b",
            "mixtral-8x22b",
            "mistral-large",
            "deepseek-llm",
            "deepseek-7b",
            "deepseek-67b",
            "grok-1",
            "grok-1.5",
            "llama-2-chat-7b",
            "llama-2-chat-13b",
            "dialogpt-medium",
            "dialogpt-large",
            "blenderbot-400m",
            "llama-2-chat",
        ]
        return model_code.lower() not in [m.lower() for m in legacy_models]

    def get_rate_limits(self, provider: str) -> tuple[int, int]:
        rate_map = {
            "openai": (10000, 2000000),
            "google": (15000, 4000000),
            "groq": (30000, 6000000),
            "abacus_ai": (5000, 1000000),
            "anthropic": (5000, 1000000),
            "xai": (10000, 2000000),
        }
        return rate_map.get(provider, (5000, 1000000))

    def _initialize_models(self):
        """Initialize the model registry with models from CSV."""
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "docs", "ai-models", "ai-models.csv"
        )
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["Model Name"]:
                    continue

                model_code = row["Model Code for API"]
                provider_str = self.infer_provider(model_code)
                if not provider_str:
                    logger.warning(f"Unknown provider for {model_code}")
                    continue
                provider = ModelProvider(provider_str)

                try:
                    context_window = int(
                        row["Input Token Limit"].replace(",", "").replace(" tokens", "")
                    )
                    max_tokens = int(
                        row["Output Token Limit"]
                        .replace(",", "")
                        .replace(" tokens", "")
                    )
                except ValueError:
                    logger.warning(f"Invalid token limits for {model_code}")
                    continue

                features = [
                    f.strip() for f in row["Key Features"].split(",") if f.strip()
                ]
                inputs = [i.strip() for i in row["Inputs"].split(",") if i.strip()]
                outputs = [o.strip() for o in row["Outputs"].split(",") if o.strip()]
                capabilities = self.map_features_to_capabilities(
                    features, model_code, inputs, outputs
                )

                recommended_for = [f.lower().strip() for f in features]

                input_cost, output_cost = self.get_costs(model_code)

                rpm, tpm = self.get_rate_limits(provider_str)

                modern = self.is_modern(model_code, row["Last Updated"])

                self.register_model(
                    ModelConfig(
                        provider=provider,
                        model_name=model_code,
                        display_name=row["Model Name"],
                        max_tokens=max_tokens,
                        context_window=context_window,
                        cost_per_1k_input_tokens=input_cost,
                        cost_per_1k_output_tokens=output_cost,
                        capabilities=capabilities,
                        recommended_for=recommended_for,
                        description=row["Description"],
                        rate_limit_rpm=rpm,
                        rate_limit_tpm=tpm,
                        modern=modern,
                        release_date=row["Last Updated"],
                    )
                )

    def register_model(self, model: ModelConfig):
        """Register a new model in the registry."""
        if model.model_name in self.models:
            logger.info(f"Skipping duplicate registration for {model.model_name}")
            return
        self.models[model.model_name] = model
        if model.model_name not in self.usage_stats:
            self.usage_stats[model.model_name] = ModelUsageStats()
        logger.info(f"Registered model: {model.display_name} ({model.model_name})")

    def get_model(self, model_name: str) -> ModelConfig | None:
        """Get a model configuration by name."""
        return self.models.get(model_name)

    def list_models(
        self, provider: ModelProvider | None = None, modern_only: bool = True
    ) -> list[ModelConfig]:
        """List all models, optionally filtered by provider and modern status."""
        models = list(self.models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        if modern_only:
            models = [m for m in models if m.modern]
        return models

    def get_models_by_capability(
        self, capability: ModelCapability, modern_only: bool = True
    ) -> list[ModelConfig]:
        """Get models that support a specific capability."""
        models = [m for m in self.models.values() if capability in m.capabilities]
        if modern_only:
            models = [m for m in models if m.modern]
        return models

    def get_recommended_model(
        self, use_case: str, max_cost: float | None = None, prefer_modern: bool = True
    ) -> ModelConfig | None:
        """Get the recommended model for a specific use case."""
        candidates = [
            m
            for m in self.models.values()
            if (
                any(uc in m.recommended_for for uc in use_case.lower().split())
                and m.is_available
            )
        ]

        if prefer_modern:
            candidates = [m for m in candidates if m.modern]

        if max_cost is not None:
            candidates = [
                m for m in candidates if m.cost_per_1k_input_tokens <= max_cost
            ]

        if not candidates:
            return None

        # Prefer gpt-4.1 over gpt-4o except for realtime voice
        is_realtime_voice = any(
            term in use_case.lower() for term in ["realtime", "voice"]
        )

        def priority_key(m):
            if is_realtime_voice:
                if "gpt-4o" in m.model_name:
                    return 0
                elif "gpt-4.1" in m.model_name:
                    return 1
            else:
                if "gpt-4.1" in m.model_name:
                    return 0
                elif "gpt-4o" in m.model_name:
                    return 1
            return 2

        candidates.sort(
            key=lambda m: (
                priority_key(m),
                -self.usage_stats.get(m.model_name, ModelUsageStats()).success_rate,
                m.cost_per_1k_input_tokens,
            )
        )

        return candidates[0] if candidates else None

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
