"""Environment variable mapping and priority resolution for settings."""

import os
from typing import Any, Dict

# Define environment variable mappings for settings
# Format: settings_key -> environment_variable_name
ENV_VAR_MAPPINGS = {
    # Model provider and name settings
    "chat_model_provider": "CHAT_MODEL_PROVIDER",
    "chat_model_name": "CHAT_MODEL_NAME",
    "util_model_provider": "UTIL_MODEL_PROVIDER", 
    "util_model_name": "UTIL_MODEL_NAME",
    "embed_model_provider": "EMBED_MODEL_PROVIDER",
    "embed_model_name": "EMBED_MODEL_NAME",
    "browser_model_provider": "BROWSER_MODEL_PROVIDER",
    "browser_model_name": "BROWSER_MODEL_NAME",
    "voice_model_provider": "VOICE_MODEL_PROVIDER",
    "voice_model_name": "VOICE_MODEL_NAME",
    "code_model_provider": "CODE_MODEL_PROVIDER",
    "code_model_name": "CODE_MODEL_NAME",
    
    # API Keys - these will be populated in api_keys dict
    "openai_api_key": "OPENAI_API_KEY",
    "vite_openai_api_key": "VITE_OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "vite_anthropic_api_key": "VITE_ANTHROPIC_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "vite_google_api_key": "VITE_GOOGLE_API_KEY",
    "groq_api_key": "GROQ_API_KEY",
    "vite_groq_api_key": "VITE_GROQ_API_KEY",
    "perplexity_api_key": "PERPLEXITY_API_KEY",
    "vite_perplexity_api_key": "VITE_PERPLEXITY_API_KEY",
    
    # Database settings (already supported)
    "database_url": "DATABASE_URL",
    "database_name": "DATABASE_NAME", 
    "database_username": "DATABASE_USERNAME",
    "database_password": "DATABASE_PASSWORD",
    "database_host": "DATABASE_HOST",
    "database_port": "DATABASE_PORT",
    
    # MCP and RFC settings (already supported)
    "mcp_server_token": "MCP_SERVER_TOKEN",
    "rfc_url": "RFC_URL",
    "rfc_password": "RFC_PASSWORD",
    
    # Authentication settings (already supported)  
    "auth_login": "AUTH_LOGIN",
    "auth_password": "AUTH_PASSWORD",
    "root_password": "ROOT_PASSWORD",
    
    # Railway-specific settings
    "port": "PORT",
    "railway_environment": "RAILWAY_ENVIRONMENT",
    "railway_service_name": "RAILWAY_SERVICE_NAME",
}


def get_env_value_with_type(env_var: str, default: Any = None) -> Any:
    """Get environment variable value with type conversion based on default type."""
    value = os.getenv(env_var)
    if value is None:
        return default
        
    # Type conversion based on default value type
    if isinstance(default, bool):
        return value.lower() in ('true', '1', 'yes', 'on')
    elif isinstance(default, int):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    elif isinstance(default, float):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    else:
        # String or other types
        return value


def apply_env_var_overrides(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to settings.
    
    Environment variables always take priority over stored settings.
    
    Args:
        settings: The base settings dictionary (from storage or defaults)
        
    Returns:
        Settings dictionary with environment variable overrides applied
    """
    result = settings.copy()
    
    # Apply direct settings overrides
    for setting_key, env_var in ENV_VAR_MAPPINGS.items():
        if setting_key.startswith('api_keys.'):
            continue  # Handle API keys separately
            
        if setting_key in result:  # Only override keys that exist in settings
            original_value = result[setting_key]
            env_value = get_env_value_with_type(env_var, original_value)
            if env_value is not None and str(env_value) != str(original_value):
                result[setting_key] = env_value
    
    # Special handling for API keys - populate api_keys dict from environment
    api_keys = result.get("api_keys", {}).copy()
    
    # Map of provider names to env var patterns  
    api_key_providers = {
        "OPENAI": ["OPENAI_API_KEY", "VITE_OPENAI_API_KEY"],
        "ANTHROPIC": ["ANTHROPIC_API_KEY", "VITE_ANTHROPIC_API_KEY"], 
        "GOOGLE": ["GOOGLE_API_KEY", "VITE_GOOGLE_API_KEY", "GEMINI_API_KEY", "VITE_GEMINI_API_KEY"],
        "GROQ": ["GROQ_API_KEY", "VITE_GROQ_API_KEY"],
        "PERPLEXITY": ["PERPLEXITY_API_KEY", "VITE_PERPLEXITY_API_KEY"],
        "XAI": ["XAI_API_KEY", "VITE_XAI_API_KEY"],
        "HUGGINGFACE": ["HUGGINGFACE_TOKEN", "VITE_HUGGINGFACE_TOKEN"],
    }
    
    for provider, env_vars in api_key_providers.items():
        # Check each possible environment variable for this provider
        for env_var in env_vars:
            env_value = os.getenv(env_var)
            if env_value:
                api_keys[provider] = env_value
                break  # Use first found value
    
    result["api_keys"] = api_keys
    
    return result


def get_env_var_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all environment variables for settings.
    
    Returns:
        Dictionary with environment variable status information
    """
    status = {
        "overridden": {},  # Settings overridden by env vars
        "available": {},   # Env vars that are available but not overriding 
        "missing": {}      # Env vars that could be set but aren't
    }
    
    for setting_key, env_var in ENV_VAR_MAPPINGS.items():
        env_value = os.getenv(env_var)
        if env_value:
            status["overridden"][setting_key] = {
                "env_var": env_var,
                "value": env_value[:20] + "..." if len(env_value) > 20 else env_value
            }
        else:
            status["missing"][setting_key] = {
                "env_var": env_var, 
                "description": f"Set {env_var} to override {setting_key}"
            }
    
    # Check API key environment variables
    api_key_providers = {
        "OPENAI": ["OPENAI_API_KEY", "VITE_OPENAI_API_KEY"],
        "ANTHROPIC": ["ANTHROPIC_API_KEY", "VITE_ANTHROPIC_API_KEY"],
        "GOOGLE": ["GOOGLE_API_KEY", "VITE_GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "GROQ": ["GROQ_API_KEY", "VITE_GROQ_API_KEY"],
        "PERPLEXITY": ["PERPLEXITY_API_KEY", "VITE_PERPLEXITY_API_KEY"],
    }
    
    for provider, env_vars in api_key_providers.items():
        found_key = False
        for env_var in env_vars:
            env_value = os.getenv(env_var)
            if env_value:
                status["overridden"][f"api_keys.{provider}"] = {
                    "env_var": env_var,
                    "value": "***" + env_value[-4:] if len(env_value) > 4 else "***"
                }
                found_key = True
                break
        
        if not found_key:
            status["missing"][f"api_keys.{provider}"] = {
                "env_var": env_vars[0],  # Show primary env var
                "description": f"Set {env_vars[0]} to provide {provider} API key"
            }
    
    return status