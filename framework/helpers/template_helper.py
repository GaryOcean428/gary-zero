"""
Template helper for consistent HTML template rendering across all entry points.

This module ensures that template placeholders are properly substituted
regardless of which application entry point is used (Flask, FastAPI, uvicorn).
"""

import os
import logging
from typing import Dict, Any, Optional
from framework.helpers.config_loader import get_config_loader
from framework.helpers import files

logger = logging.getLogger(__name__)


class TemplateHelper:
    """Helper for consistent template rendering with configuration injection."""
    
    def __init__(self):
        """Initialize the template helper."""
        self.config_loader = get_config_loader()
    
    def render_html_template(self, template_path: str, **additional_vars) -> str:
        """
        Render an HTML template with proper variable substitution.
        
        Args:
            template_path: Path to the HTML template file
            **additional_vars: Additional template variables
            
        Returns:
            Rendered HTML content with substitutions
        """
        try:
            # Get standard template variables
            template_vars = self.config_loader.get_template_vars()
            
            # Add any additional variables
            template_vars.update(additional_vars)
            
            # Read and render the template
            rendered_content = files.read_file(template_path, **template_vars)
            
            # Validate that no placeholders remain
            self._validate_rendered_content(rendered_content, template_path)
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"Failed to render template {template_path}: {e}")
            # Return a fallback template with error information
            return self._create_fallback_template(template_path, str(e))
    
    def _validate_rendered_content(self, content: str, template_path: str) -> None:
        """
        Validate that rendered content doesn't contain unresolved placeholders.
        
        Args:
            content: Rendered HTML content
            template_path: Path to the template file for error reporting
        """
        # Check for unresolved template placeholders
        import re
        placeholders = re.findall(r'{{(\w+)}}', content)
        
        if placeholders:
            logger.error(f"Unresolved placeholders in {template_path}: {placeholders}")
            # Don't raise an exception, just log the error
            # The content will be served with placeholders visible for debugging
    
    def _create_fallback_template(self, template_path: str, error: str) -> str:
        """
        Create a fallback template when rendering fails.
        
        Args:
            template_path: Path to the failed template
            error: Error message
            
        Returns:
            Fallback HTML content
        """
        version_info = self.config_loader.get_version_info()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Gary-Zero - Template Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }}
        .info {{ background: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Gary-Zero</h1>
    <div class="error">
        <h2>Template Rendering Error</h2>
        <p><strong>Template:</strong> {template_path}</p>
        <p><strong>Error:</strong> {error}</p>
    </div>
    <div class="info">
        <p><strong>Version:</strong> {version_info['version_no']}</p>
        <p><strong>Build Time:</strong> {version_info['version_time']}</p>
        <p>This is a fallback page. Please check the application logs for more details.</p>
    </div>
</body>
</html>"""

    def preprocess_static_templates(self) -> None:
        """
        Preprocess static templates to replace placeholders for Railway deployment.
        
        This method can be called during application startup to create preprocessed
        versions of templates with placeholders already substituted.
        """
        try:
            template_files = [
                "./webui/index.html",
                "./webui/privacy.html", 
                "./webui/terms.html"
            ]
            
            for template_path in template_files:
                if os.path.exists(template_path):
                    self._preprocess_template_file(template_path)
                    
        except Exception as e:
            logger.error(f"Failed to preprocess templates: {e}")
    
    def _preprocess_template_file(self, template_path: str) -> None:
        """
        Preprocess a single template file.
        
        Args:
            template_path: Path to the template file
        """
        try:
            # Create a backup path
            backup_path = f"{template_path}.original"
            preprocessed_path = f"{template_path}.preprocessed"
            
            # Only create backup if it doesn't exist
            if not os.path.exists(backup_path):
                # Read original content
                with open(template_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Save backup
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                logger.info(f"Created template backup: {backup_path}")
            
            # Render template with current configuration
            rendered_content = self.render_html_template(template_path)
            
            # Save preprocessed version
            with open(preprocessed_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            logger.info(f"Created preprocessed template: {preprocessed_path}")
            
        except Exception as e:
            logger.error(f"Failed to preprocess {template_path}: {e}")


# Global instance
_template_helper = None

def get_template_helper() -> TemplateHelper:
    """Get the global template helper instance."""
    global _template_helper
    if _template_helper is None:
        _template_helper = TemplateHelper()
    return _template_helper


def render_index_html(**additional_vars) -> str:
    """
    Convenience function to render the main index.html template.
    
    Args:
        **additional_vars: Additional template variables
        
    Returns:
        Rendered HTML content
    """
    return get_template_helper().render_html_template("./webui/index.html", **additional_vars)


def render_template(template_path: str, **additional_vars) -> str:
    """
    Convenience function to render any HTML template.
    
    Args:
        template_path: Path to the template file
        **additional_vars: Additional template variables
        
    Returns:
        Rendered HTML content
    """
    return get_template_helper().render_html_template(template_path, **additional_vars)