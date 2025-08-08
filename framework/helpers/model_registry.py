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
        """Initialize the model registry dynamically from MODEL_CATALOG."""
        # Load configurations dynamically from the central MODEL_CATALOG
        providers_found = set()
        
        for provider_key, models in MODEL_CATALOG.items():
            provider_name = provider_key.lower()
            providers_found.add(provider_name)
            
            for model_info in models:
                model_value = model_info["value"]
                qualified_id = f"{provider_name}:{model_value}"
                
                # Determine endpoint based on provider
                if provider_name == "openai":
                    endpoint = ModelEndpoint.CHAT
                elif provider_name == "anthropic":
                    endpoint = ModelEndpoint.MESSAGES
                else:
                    endpoint = ModelEndpoint.CHAT  # Default fallback
                
                # Infer capabilities based on model characteristics
                capabilities = ["chat"]
                if model_info.get("modern", False):
                    capabilities.extend(["function_calling"])
                    
                # Add vision capability for certain models
                if any(keyword in model_value.lower() for keyword in ["gpt-4", "claude-3", "claude-4", "o3", "gpt-5"]):
                    if "vision" not in capabilities:
                        capabilities.append("vision")
                
                # Add advanced reasoning for newer models
                if any(keyword in model_value.lower() for keyword in ["gpt-5", "claude-4", "o3"]):
                    capabilities.append("advanced_reasoning")
                
                # Estimate max tokens based on model
                max_tokens = 128000  # Default
                if any(keyword in model_value.lower() for keyword in ["gpt-5", "claude-4"]):
                    max_tokens = 200000
                elif "claude" in model_value.lower():
                    max_tokens = 200000
                
                config = ModelConfig(
                    provider=provider_name,
                    model_name=model_value,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    max_tokens=max_tokens
                )
                
                self._register_model(qualified_id, config)
        
        # Initialize provider statuses for all found providers
        for provider in providers_found:
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
            # Make a minimal health check call to the provider
            success = await self._perform_provider_health_check(provider)
            
            status.is_healthy = success
            status.last_check = now
            
            if success:
                status.error_count = 0
                status.last_error = None
                PrintStyle().success(f"✅ Provider {provider} health check passed")
            else:
                status.error_count += 1
                status.last_error = "Health check failed"
                PrintStyle().error(f"❌ Provider {provider} health check failed")
                
            return success
            
        except Exception as e:
            status.is_healthy = False
            status.last_check = now
            status.error_count += 1
            status.last_error = str(e)
            
            PrintStyle().error(f"❌ Provider {provider} health check failed: {e}")
            return False
    
    async def _perform_provider_health_check(self, provider: str) -> bool:
        """Perform actual health check for a specific provider."""
        try:
            # Import here to avoid circular dependencies
            import models
            from framework.helpers import dotenv
            
            # Get API key for the provider
            api_key = dotenv.get_dotenv_value(f"API_KEY_{provider.upper()}")
            if not api_key:
                return False
            
            # Get a model for this provider to test with
            provider_models = self.get_models_by_provider(provider)
            if not provider_models:
                return False
                
            # Select the first available model for testing
            test_model_id = next(iter(provider_models.keys()))
            config = provider_models[test_model_id]
            
            # Perform provider-specific health check
            if provider == "openai":
                return await self._health_check_openai(config.model_name, api_key)
            elif provider == "anthropic":
                return await self._health_check_anthropic(config.model_name, api_key)
            elif provider == "google":
                return await self._health_check_google(config.model_name, api_key)
            else:
                # For other providers, assume healthy if API key exists
                return bool(api_key)
                
        except Exception as e:
            PrintStyle().error(f"Health check error for {provider}: {e}")
            return False
    
    async def _health_check_openai(self, model_name: str, api_key: str) -> bool:
        """Health check for OpenAI provider."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            
            # Make a minimal completion request
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                timeout=10.0
            )
            return response.choices[0].message.content is not None
            
        except Exception:
            return False
    
    async def _health_check_anthropic(self, model_name: str, api_key: str) -> bool:
        """Health check for Anthropic provider."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            # Make a minimal message request
            response = await client.messages.create(
                model=model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
                timeout=10.0
            )
            return len(response.content) > 0
            
        except Exception:
            return False
    
    async def _health_check_google(self, model_name: str, api_key: str) -> bool:
        """Health check for Google provider."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async("test")
            return response.text is not None
            
        except Exception:
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