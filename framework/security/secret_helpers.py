"""
Secret Store Integration Helpers.

This module provides helper functions and utilities for integrating the
secret store with existing Gary-Zero components like session managers,
tools, and planners.
"""

import logging
import os
from typing import Optional, Dict, Any

from .secret_store import get_secret, store_secret, AccessLevel

logger = logging.getLogger(__name__)


def get_api_key(service: str, default: Optional[str] = None, 
               fallback_env_var: Optional[str] = None) -> Optional[str]:
    """
    Get an API key for a service, with fallback to environment variables.
    
    Args:
        service: Service name (e.g., 'openai', 'anthropic', 'google')
        default: Default value if not found
        fallback_env_var: Environment variable to check as fallback
        
    Returns:
        API key or default value
    """
    # Normalize service name to secret name
    secret_name = f"{service.lower()}_api_key"
    
    # Try to get from secret store first
    api_key = get_secret(secret_name)
    
    if api_key:
        logger.debug(f"Retrieved {service} API key from secret store")
        return api_key
    
    # Fallback to environment variable
    if fallback_env_var:
        env_key = os.getenv(fallback_env_var)
        if env_key:
            logger.debug(f"Retrieved {service} API key from environment variable {fallback_env_var}")
            # Optionally store it in the secret store for future use
            try:
                store_secret(secret_name, env_key, overwrite=False)
                logger.info(f"Stored {service} API key in secret store for future use")
            except Exception as e:
                logger.warning(f"Failed to store {service} API key in secret store: {e}")
            return env_key
    
    # Return default if nothing found
    if default:
        logger.debug(f"Using default value for {service} API key")
    else:
        logger.warning(f"No API key found for {service}")
    
    return default


def get_database_url(default: Optional[str] = None) -> Optional[str]:
    """
    Get database URL from secret store or environment.
    
    Args:
        default: Default URL if not found
        
    Returns:
        Database URL or default
    """
    # Try secret store first
    db_url = get_secret("database_url")
    if db_url:
        return db_url
    
    # Fallback to environment
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        # Store for future use
        try:
            store_secret("database_url", env_url, overwrite=False)
        except Exception as e:
            logger.warning(f"Failed to store database URL in secret store: {e}")
        return env_url
    
    return default


def get_auth_credentials(service: str) -> Optional[Dict[str, str]]:
    """
    Get authentication credentials for a service.
    
    Args:
        service: Service name
        
    Returns:
        Dictionary with username/password or None
    """
    username = get_secret(f"{service}_username")
    password = get_secret(f"{service}_password")
    
    if username and password:
        return {"username": username, "password": password}
    
    # Try environment fallback
    env_user = os.getenv(f"{service.upper()}_USERNAME") or os.getenv(f"{service.upper()}_USER")
    env_pass = os.getenv(f"{service.upper()}_PASSWORD") or os.getenv(f"{service.upper()}_PASS")
    
    if env_user and env_pass:
        # Store for future use
        try:
            store_secret(f"{service}_username", env_user, overwrite=False)
            store_secret(f"{service}_password", env_pass, overwrite=False)
        except Exception as e:
            logger.warning(f"Failed to store {service} credentials in secret store: {e}")
        
        return {"username": env_user, "password": env_pass}
    
    return None


def get_webhook_url(service: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get webhook URL for a service.
    
    Args:
        service: Service name
        default: Default URL if not found
        
    Returns:
        Webhook URL or default
    """
    secret_name = f"{service}_webhook_url"
    return get_secret(secret_name, default)


def get_certificate(service: str) -> Optional[str]:
    """
    Get certificate for a service.
    
    Args:
        service: Service name
        
    Returns:
        Certificate content or None
    """
    secret_name = f"{service}_certificate"
    return get_secret(secret_name)


def migrate_environment_secrets(env_mapping: Optional[Dict[str, str]] = None,
                               overwrite: bool = False) -> int:
    """
    Migrate secrets from environment variables to the secret store.
    
    Args:
        env_mapping: Custom mapping of env vars to secret names
        overwrite: Whether to overwrite existing secrets
        
    Returns:
        Number of secrets migrated
    """
    from .secret_store import get_secret_store, initialize_from_environment
    
    if env_mapping:
        # Use custom mapping
        store = get_secret_store()
        return store.load_from_environment(env_mapping, overwrite=overwrite)
    else:
        # Use default mappings
        return initialize_from_environment(overwrite=overwrite)


# Convenience functions for common services
def get_openai_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get OpenAI API key."""
    return get_api_key("openai", default, "OPENAI_API_KEY")


def get_anthropic_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get Anthropic API key."""
    return get_api_key("anthropic", default, "ANTHROPIC_API_KEY")


def get_google_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get Google API key."""
    return get_api_key("google", default, "GOOGLE_API_KEY")


def get_gemini_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get Gemini API key."""
    return get_api_key("gemini", default, "GEMINI_API_KEY")


def get_groq_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get Groq API key."""
    return get_api_key("groq", default, "GROQ_API_KEY")


def get_perplexity_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get Perplexity API key."""
    return get_api_key("perplexity", default, "PERPLEXITY_API_KEY")


def get_huggingface_token(default: Optional[str] = None) -> Optional[str]:
    """Get Hugging Face token."""
    return get_api_key("huggingface", default, "HUGGINGFACE_TOKEN")


def get_e2b_api_key(default: Optional[str] = None) -> Optional[str]:
    """Get E2B API key."""
    return get_api_key("e2b", default, "E2B_API_KEY")


def get_jwt_secret(default: Optional[str] = None) -> Optional[str]:
    """Get JWT secret."""
    secret = get_secret("jwt_secret", default)
    if not secret:
        # Try environment fallback
        secret = os.getenv("JWT_SECRET", default)
        if secret and secret != default:
            try:
                store_secret("jwt_secret", secret, overwrite=False)
            except Exception as e:
                logger.warning(f"Failed to store JWT secret: {e}")
    return secret


def get_session_secret(default: Optional[str] = None) -> Optional[str]:
    """Get session secret."""
    secret = get_secret("session_secret", default)
    if not secret:
        # Try environment fallback
        secret = os.getenv("SESSION_SECRET", default)
        if secret and secret != default:
            try:
                store_secret("session_secret", secret, overwrite=False)
            except Exception as e:
                logger.warning(f"Failed to store session secret: {e}")
    return secret


def get_kali_credentials() -> Optional[Dict[str, str]]:
    """Get Kali Linux credentials."""
    return get_auth_credentials("kali")


def get_supabase_config() -> Optional[Dict[str, str]]:
    """Get Supabase configuration."""
    url = get_secret("supabase_url") or os.getenv("SUPABASE_URL")
    anon_key = get_secret("supabase_anon_key") or os.getenv("SUPABASE_ANON_KEY")
    service_role_key = get_secret("supabase_service_role_key") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if url and anon_key:
        # Store missing values
        try:
            if url and not get_secret("supabase_url"):
                store_secret("supabase_url", url, overwrite=False)
            if anon_key and not get_secret("supabase_anon_key"):
                store_secret("supabase_anon_key", anon_key, overwrite=False)
            if service_role_key and not get_secret("supabase_service_role_key"):
                store_secret("supabase_service_role_key", service_role_key, overwrite=False)
        except Exception as e:
            logger.warning(f"Failed to store Supabase config: {e}")
        
        config = {"url": url, "anon_key": anon_key}
        if service_role_key:
            config["service_role_key"] = service_role_key
        return config
    
    return None


# Decorator for tools that need API keys
def require_api_key(service: str, env_var: Optional[str] = None):
    """
    Decorator to ensure a tool has the required API key.
    
    Args:
        service: Service name
        env_var: Environment variable name for fallback
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            api_key = get_api_key(service, fallback_env_var=env_var)
            if not api_key:
                raise ValueError(f"No API key found for {service}. Please add it to the secret store or set {env_var} environment variable.")
            
            # Add api_key to kwargs if not already present
            if 'api_key' not in kwargs:
                kwargs['api_key'] = api_key
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecretStoreIntegration:
    """
    Integration class for components that need to work with secrets.
    
    This class provides a consistent interface for components to access
    secrets while maintaining backward compatibility with environment variables.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize integration for a component.
        
        Args:
            component_name: Name of the component (for logging)
        """
        self.component_name = component_name
        self.logger = logging.getLogger(f"secret_integration.{component_name}")
    
    def get_secret(self, name: str, default: Optional[str] = None,
                  env_fallback: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        Get a secret with component-specific logging.
        
        Args:
            name: Secret name
            default: Default value
            env_fallback: Environment variable fallback
            required: Whether the secret is required
            
        Returns:
            Secret value or default
            
        Raises:
            ValueError: If secret is required but not found
        """
        value = get_secret(name, default)
        
        if not value and env_fallback:
            value = os.getenv(env_fallback, default)
            if value and value != default:
                # Store for future use
                try:
                    store_secret(name, value, overwrite=False)
                    self.logger.info(f"Stored {name} from environment for future use")
                except Exception as e:
                    self.logger.warning(f"Failed to store {name}: {e}")
        
        if required and not value:
            raise ValueError(f"{self.component_name} requires secret '{name}' but it was not found")
        
        if value:
            self.logger.debug(f"Retrieved secret '{name}' for {self.component_name}")
        else:
            self.logger.warning(f"No value found for secret '{name}' in {self.component_name}")
        
        return value
    
    def get_api_key(self, service: str, required: bool = True) -> Optional[str]:
        """
        Get API key for a service.
        
        Args:
            service: Service name
            required: Whether the API key is required
            
        Returns:
            API key
        """
        env_var = f"{service.upper()}_API_KEY"
        return self.get_secret(f"{service}_api_key", env_fallback=env_var, required=required)
    
    def get_credentials(self, service: str, required: bool = True) -> Optional[Dict[str, str]]:
        """
        Get username/password credentials for a service.
        
        Args:
            service: Service name
            required: Whether credentials are required
            
        Returns:
            Credentials dictionary
        """
        username = self.get_secret(f"{service}_username", required=False)
        password = self.get_secret(f"{service}_password", required=False)
        
        if not username or not password:
            # Try environment fallback
            env_user = os.getenv(f"{service.upper()}_USERNAME") or os.getenv(f"{service.upper()}_USER")
            env_pass = os.getenv(f"{service.upper()}_PASSWORD") or os.getenv(f"{service.upper()}_PASS")
            
            if env_user and env_pass:
                username = env_user
                password = env_pass
                # Store for future use
                try:
                    if not get_secret(f"{service}_username"):
                        store_secret(f"{service}_username", username, overwrite=False)
                    if not get_secret(f"{service}_password"):
                        store_secret(f"{service}_password", password, overwrite=False)
                except Exception as e:
                    self.logger.warning(f"Failed to store {service} credentials: {e}")
        
        if username and password:
            return {"username": username, "password": password}
        elif required:
            raise ValueError(f"{self.component_name} requires credentials for {service}")
        
        return None