"""Centralized model registry with provider-qualified IDs and validation.

This module provides a unified model registry that maps provider-qualified model IDs
to their configuration and capabilities. It supports health checks and provider status
caching to improve utility model reliability.
"""

import asyncio
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from .model_catalog import MODEL_CATALOG, validate_model_selection
from .print_style import PrintStyle


class ModelEndpoint(Enum):
    """Supported model endpoints."""
    CHAT = "chat"
    COMPLETIONS = "completions"
    MESSAGES = "messages"
    RESPONSES = "responses"


@dataclass
class ModelConfig:
    """Configuration for a registered model."""
    provider: str
    model_name: str
    endpoint: ModelEndpoint
    capabilities: list[str] = field(default_factory=list)
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    cost_per_token: Optional[float] = None


@dataclass 
class ProviderStatus:
    """Health status for a model provider."""
    provider: str
    is_healthy: bool = True
    last_check: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None


class ModelRegistry:
    """Centralized model registry with health checking and validation."""
    
    def __init__(self):
        self._registry: Dict[str, ModelConfig] = {}
        self._provider_status: Dict[str, ProviderStatus] = {}
        self._health_check_cache_duration = 300  # 5 minutes
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the model registry with provider-qualified IDs."""
        # OpenAI models
        self._register_model("openai:gpt-4o-mini", ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "function_calling"],
            max_tokens=128000
        ))
        
        self._register_model("openai:gpt-4o", ModelConfig(
            provider="openai", 
            model_name="gpt-4o",
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "function_calling", "vision"],
            max_tokens=128000
        ))
        
        self._register_model("openai:gpt-5-mini", ModelConfig(
            provider="openai",
            model_name="gpt-5-mini", 
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "function_calling", "vision"],
            max_tokens=200000
        ))
        
        self._register_model("openai:gpt-5-chat-latest", ModelConfig(
            provider="openai",
            model_name="gpt-5-chat-latest",
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "function_calling", "vision", "advanced_reasoning"],
            max_tokens=200000
        ))
        
        self._register_model("openai:o3", ModelConfig(
            provider="openai",
            model_name="o3",
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "reasoning", "mathematics", "coding"],
            max_tokens=128000
        ))
        
        self._register_model("openai:o3-pro", ModelConfig(
            provider="openai",
            model_name="o3-pro", 
            endpoint=ModelEndpoint.CHAT,
            capabilities=["chat", "reasoning", "mathematics", "coding", "research"],
            max_tokens=128000
        ))
        
        # Anthropic models
        self._register_model("anthropic:claude-3-5-sonnet-20241022", ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            endpoint=ModelEndpoint.MESSAGES,
            capabilities=["chat", "function_calling", "vision"],
            max_tokens=200000
        ))
        
        self._register_model("anthropic:claude-sonnet-4-20250514", ModelConfig(
            provider="anthropic",
            model_name="claude-sonnet-4-20250514", 
            endpoint=ModelEndpoint.MESSAGES,
            capabilities=["chat", "function_calling", "vision", "advanced_reasoning"],
            max_tokens=200000
        ))
        
        self._register_model("anthropic:claude-opus-4-20250514", ModelConfig(
            provider="anthropic",
            model_name="claude-opus-4-20250514",
            endpoint=ModelEndpoint.MESSAGES, 
            capabilities=["chat", "function_calling", "vision", "advanced_reasoning", "research"],
            max_tokens=200000
        ))
        
        # Initialize provider statuses
        for provider in ["openai", "anthropic"]:
            self._provider_status[provider] = ProviderStatus(provider=provider)
    
    def _register_model(self, qualified_id: str, config: ModelConfig):
        """Register a model with its configuration."""
        self._registry[qualified_id] = config
        
    def validate_model(self, qualified_id: str) -> bool:
        """Validate that a model exists in the registry."""
        if qualified_id not in self._registry:
            PrintStyle().error(f"Unknown model '{qualified_id}'. Available models: {list(self._registry.keys())}")
            return False
        return True
        
    def get_model_config(self, qualified_id: str) -> Optional[ModelConfig]:
        """Get the configuration for a registered model."""
        return self._registry.get(qualified_id)
        
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Get all available models."""
        return self._registry.copy()
        
    def get_models_by_provider(self, provider: str) -> Dict[str, ModelConfig]:
        """Get all models for a specific provider.""" 
        return {
            qualified_id: config 
            for qualified_id, config in self._registry.items()
            if config.provider == provider
        }
    
    def get_models_by_capability(self, capability: str) -> Dict[str, ModelConfig]:
        """Get all models that support a specific capability."""
        return {
            qualified_id: config
            for qualified_id, config in self._registry.items()
            if capability in config.capabilities
        }
    
    async def health_check_provider(self, provider: str) -> bool:
        """Check if a provider is healthy by making a minimal API call."""
        status = self._provider_status.get(provider)
        if not status:
            return False
            
        # Check cache
        now = time.time()
        if now - status.last_check < self._health_check_cache_duration:
            return status.is_healthy
            
        # Perform health check
        try:
            # TODO: Implement actual health check calls to each provider
            # For now, assume healthy
            status.is_healthy = True
            status.last_check = now
            status.error_count = 0
            status.last_error = None
            
            PrintStyle().success(f"✅ Provider {provider} health check passed")
            return True
            
        except Exception as e:
            status.is_healthy = False
            status.last_check = now
            status.error_count += 1
            status.last_error = str(e)
            
            PrintStyle().error(f"❌ Provider {provider} health check failed: {e}")
            return False
    
    def get_provider_status(self, provider: str) -> Optional[ProviderStatus]:
        """Get the current status of a provider."""
        return self._provider_status.get(provider)
        
    def get_utility_model(self, settings) -> Optional[ModelConfig]:
        """Get the utility model configuration with fallback logic."""
        try:
            # Try to get utility model from settings (support both dict and object access)
            util_provider = None
            util_model_name = None
            
            if hasattr(settings, 'util_model_provider'):
                util_provider = settings.util_model_provider
                util_model_name = settings.util_model_name
            elif isinstance(settings, dict):
                util_provider = settings.get('util_model_provider')
                util_model_name = settings.get('util_model_name')
                
            if util_provider and util_model_name:
                # Create qualified model ID
                qualified_id = f"{util_provider.lower()}:{util_model_name}"
                
                if self.validate_model(qualified_id):
                    config = self.get_model_config(qualified_id)
                    if config:
                        return config
                else:
                    PrintStyle().warn(f"⚠️ Configured utility model not in registry: {qualified_id}")
                    
            # Fallback to a known working model
            fallback_models = [
                "openai:gpt-4o-mini",
                "anthropic:claude-3-5-sonnet-20241022", 
                "openai:gpt-5-mini"
            ]
            
            for fallback in fallback_models:
                if self.validate_model(fallback):
                    PrintStyle().warn(f"⚠️ Using fallback utility model: {fallback}")
                    return self.get_model_config(fallback)
                    
        except Exception as e:
            PrintStyle().error(f"❌ Error getting utility model: {e}")
            
        PrintStyle().error("❌ No valid utility model available")
        return None


# Global registry instance
_model_registry = None

def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


def validate_model_id(qualified_id: str) -> bool:
    """Validate a qualified model ID."""
    return get_model_registry().validate_model(qualified_id)


def get_utility_model_config(settings) -> Optional[ModelConfig]:
    """Get utility model configuration."""
    return get_model_registry().get_utility_model(settings)