"""
Unified configuration loader for environment variables with Railway deployment support.

This module provides a centralized way to load and validate environment variables
with sane defaults, preventing placeholder leakage and ensuring proper Railway deployment.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from framework.helpers import dotenv, git

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Unified configuration loader with Railway deployment support."""
    
    def __init__(self):
        """Initialize the configuration loader."""
        self._config_cache: Dict[str, Any] = {}
        self._git_info: Optional[Dict[str, str]] = None
        self._load_git_info()
    
    def _load_git_info(self) -> None:
        """Load git information for version data."""
        try:
            self._git_info = git.get_git_info()
        except Exception as e:
            logger.warning(f"Failed to load git info: {e}")
            self._git_info = {
                "version": "unknown",
                "commit_time": "unknown",
            }
    
    def get_env_var(self, key: str, default: Optional[str] = None, 
                   required: bool = False) -> str:
        """
        Get environment variable with validation and Railway support.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            required: Whether the variable is required
            
        Returns:
            Environment variable value or default
            
        Raises:
            ValueError: If required variable is missing or contains placeholder
        """
        # Check cache first
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Get value from environment
        value = os.getenv(key)
        
        # Handle Railway-style literal placeholders
        if value and value.startswith("${{") and value.endswith("}}"):
            logger.warning(f"Railway placeholder not resolved for {key}: {value}")
            value = None
        
        # Handle literal $VARIABLE strings (not expanded)
        if value and value.startswith("$") and not value.startswith("$$"):
            # Try to resolve the variable name
            var_name = value[1:]  # Remove the $
            resolved_value = os.getenv(var_name)
            if resolved_value:
                value = resolved_value
                logger.debug(f"Resolved {key}=${value} from ${var_name}")
            else:
                logger.warning(f"Could not resolve {key}={value}")
                value = None
        
        # Use default if value is None or empty
        if not value:
            if required and not default:
                raise ValueError(f"Required environment variable {key} is not set")
            value = default or ""
        
        # Validate that value doesn't contain template placeholders
        import re
        if re.search(r"\{\{.*?\}\}", value):
            logger.error(f"Template placeholder found in {key}: {value}")
            if required:
                raise ValueError(f"Template placeholder not resolved in {key}: {value}")
        
        # Cache and return
        self._config_cache[key] = value
        return value
    
    def get_port(self) -> int:
        """
        Get the port for the application with Railway deployment support.
        
        Returns:
            Port number as integer
        """
        # Try PORT first (Railway standard)
        port_str = self.get_env_var("PORT", "8000")
        
        # Handle literal "$PORT" string case (Railway issue)
        if port_str == "$PORT":
            logger.warning("PORT environment variable contains literal '$PORT', using default 8000")
            return 8000
        
        try:
            port = int(port_str)
            if port <= 0 or port > 65535:
                raise ValueError(f"Invalid port number: {port}")
            return port
        except ValueError as e:
            logger.error(f"Invalid PORT value '{port_str}': {e}")
            return 8000
    
    def get_host(self) -> str:
        """Get the host for the application."""
        return self.get_env_var("WEB_UI_HOST", "0.0.0.0")
    
    def get_version_info(self) -> Dict[str, str]:
        """Get version information for UI display."""
        if not self._git_info:
            self._load_git_info()
        
        return {
            "version_no": self._git_info["version"],
            "version_time": self._git_info["commit_time"]
        }
    
    def get_feature_flags_config(self) -> str:
        """
        Get feature flags configuration as JavaScript snippet for UI injection.
        
        Returns:
            JavaScript configuration snippet
        """
        # Get environment-based feature flags
        enable_dev_features = self.get_env_var("ENABLE_DEV_FEATURES", "true").lower() == "true"
        vscode_integration_enabled = self.get_env_var("VSCODE_INTEGRATION_ENABLED", "true").lower() == "true"
        chat_auto_resize_enabled = self.get_env_var("CHAT_AUTO_RESIZE_ENABLED", "true").lower() == "true"
        
        # Create JavaScript configuration snippet
        js_config = f"""
    <script>
        // Environment-based feature flags
        window.ENABLE_DEV_FEATURES = {str(enable_dev_features).lower()};
        window.VSCODE_INTEGRATION_ENABLED = {str(vscode_integration_enabled).lower()};
        window.CHAT_AUTO_RESIZE_ENABLED = {str(chat_auto_resize_enabled).lower()};
        
        // Gary-Zero configuration
        window.GARY_ZERO_CONFIG = {{
            enableDevFeatures: {str(enable_dev_features).lower()},
            vscodeIntegrationEnabled: {str(vscode_integration_enabled).lower()},
            chatAutoResizeEnabled: {str(chat_auto_resize_enabled).lower()}
        }};
    </script>
    """
        
        return js_config
    
    def get_template_vars(self) -> Dict[str, str]:
        """
        Get all template variables for HTML substitution.
        
        Returns:
            Dictionary of template variables
        """
        version_info = self.get_version_info()
        return {
            "version_no": version_info["version_no"],
            "version_time": version_info["version_time"],
            "feature_flags_config": self.get_feature_flags_config()
        }
    
    def validate_railway_config(self) -> Dict[str, Any]:
        """
        Validate Railway deployment configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check required variables
        required_vars = ["PORT", "WEB_UI_HOST"]
        for var in required_vars:
            try:
                value = self.get_env_var(var, required=True)
                if "{{" in value and "}}" in value:
                    issues.append(f"{var} contains unresolved template: {value}")
            except ValueError as e:
                issues.append(str(e))
        
        # Check optional but important variables
        optional_vars = [
            "SEARXNG_URL", "SEARCH_PROVIDER", "E2B_API_KEY",
            "KALI_SHELL_URL", "KALI_SHELL_HOST", "KALI_SHELL_PORT"
        ]
        for var in optional_vars:
            value = os.getenv(var)
            if value and ("{{" in value and "}}" in value):
                warnings.append(f"{var} contains unresolved template: {value}")
        
        # Check for Railway-specific placeholders
        railway_pattern_vars = [var for var, value in os.environ.items()
                               if "${{" in value]
        if railway_pattern_vars:
            warnings.append(f"Railway placeholders found in: {', '.join(railway_pattern_vars)}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "port": self.get_port(),
            "host": self.get_host(),
            "template_vars": self.get_template_vars()
        }
    
    def log_startup_config(self) -> None:
        """Log startup configuration for debugging."""
        validation = self.validate_railway_config()
        
        print("🔧 Configuration Status:")
        print(f"   Port: {validation['port']}")
        print(f"   Host: {validation['host']}")
        print(f"   Version: {validation['template_vars']['version_no']}")
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"   ⚠️  {warning}")
        
        if validation["issues"]:
            for issue in validation["issues"]:
                print(f"   ❌ {issue}")
        
        if validation["valid"]:
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")


# Global instance
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader