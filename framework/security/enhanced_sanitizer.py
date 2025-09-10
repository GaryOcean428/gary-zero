"""Enhanced input sanitization and validation for the Gary-Zero framework.

Provides comprehensive protection against various attack vectors including:
- SQL injection
- XSS attacks
- Command injection
- Path traversal
- Malicious file uploads
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import html
import urllib.parse

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Enhanced input sanitization with multiple protection layers."""
    
    # Allowed HTML tags for safe content
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'code', 'pre', 'p', 'br']
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('|\"|;|\\)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]\\]",
        r"\.\./",
        r"~",
        r"\$\(",
        r"`.*`",
        r"\|\s*\w+",
        r"&&\s*\w+",
        r";\s*\w+",
    ]
    
    # File path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
        r"~",
        r"/etc/",
        r"/proc/",
        r"/sys/",
        r"C:\\Windows",
        r"C:\\Program Files",
    ]
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10000) -> str:
        """Comprehensive text sanitization."""
        if not isinstance(text, str):
            text = str(text)
        
        # Length check
        if len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length} characters")
        
        # Remove null bytes and control characters
        text = text.replace('\x00', '')
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # HTML escape
        text = html.escape(text, quote=True)
        
        # Check for dangerous patterns
        cls._check_sql_injection(text)
        cls._check_xss_patterns(text)
        cls._check_command_injection(text)
        
        return text.strip()
    
    @classmethod
    def sanitize_html(cls, html_content: str, allow_tags: List[str] = None) -> str:
        """Sanitize HTML content while preserving safe formatting."""
        try:
            import bleach
        except ImportError:
            logger.warning("bleach not available, using basic HTML sanitization")
            return html.escape(html_content)
        
        allowed_tags = allow_tags or cls.ALLOWED_TAGS
        
        # Use bleach for comprehensive HTML sanitization
        cleaned = bleach.clean(
            html_content,
            tags=allowed_tags,
            strip=True,
            strip_comments=True
        )
        
        return cleaned
    
    @classmethod
    def sanitize_file_path(cls, file_path: str, allowed_extensions: List[str] = None) -> str:
        """Sanitize file paths to prevent directory traversal."""
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")
        
        # Check for path traversal patterns
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                raise ValueError(f"Dangerous path pattern detected: {pattern}")
        
        # Normalize the path
        path = Path(file_path).resolve()
        
        # Check file extension if allowed list provided
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                raise ValueError(f"File extension {path.suffix} not allowed")
        
        # Convert back to string and ensure it's relative
        clean_path = str(path.relative_to(path.anchor))
        
        return clean_path
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """Sanitize URLs to prevent malicious redirects."""
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Check for dangerous schemes
        dangerous_schemes = ['javascript', 'vbscript', 'data', 'file']
        if parsed.scheme.lower() in dangerous_schemes:
            raise ValueError(f"Dangerous URL scheme: {parsed.scheme}")
        
        # Only allow http/https for external URLs
        if parsed.netloc and parsed.scheme.lower() not in ['http', 'https']:
            raise ValueError(f"Only HTTP/HTTPS URLs allowed for external links")
        
        # URL encode dangerous characters
        safe_url = urllib.parse.quote(url, safe=':/?#[]@!$&\'()*+,;=')
        
        return safe_url
    
    @classmethod
    def sanitize_json_input(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize JSON input data."""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = cls.sanitize_text(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                clean_value = cls.sanitize_text(value)
            elif isinstance(value, dict):
                clean_value = cls.sanitize_json_input(value)
            elif isinstance(value, list):
                clean_value = [
                    cls.sanitize_text(str(item)) if isinstance(item, str)
                    else cls.sanitize_json_input(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    @classmethod
    def _check_sql_injection(cls, text: str) -> None:
        """Check for SQL injection patterns."""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                raise ValueError("Potentially dangerous SQL pattern detected")
    
    @classmethod
    def _check_xss_patterns(cls, text: str) -> None:
        """Check for XSS patterns."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern}")
                raise ValueError("Potentially dangerous XSS pattern detected")
    
    @classmethod
    def _check_command_injection(cls, text: str) -> None:
        """Check for command injection patterns."""
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Potential command injection detected: {pattern}")
                raise ValueError("Potentially dangerous command injection pattern detected")


class ValidationError(Exception):
    """Exception raised when input validation fails."""
    pass


class InputValidator:
    """Enhanced input validation with comprehensive checks."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        # Allow alphanumeric, underscore, hyphen, 3-30 characters
        pattern = r'^[a-zA-Z0-9_-]{3,30}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        
        # Check for at least one uppercase, lowercase, digit, and special char
        checks = [
            r'[A-Z]',  # uppercase
            r'[a-z]',  # lowercase
            r'\d',     # digit
            r'[!@#$%^&*(),.?":{}|<>]'  # special character
        ]
        
        return all(re.search(pattern, password) for pattern in checks)
    
    @staticmethod
    def validate_agent_name(name: str) -> bool:
        """Validate agent name format."""
        # Allow alphanumeric, spaces, hyphens, underscores, 1-50 characters
        if not name or len(name) > 50:
            return False
        
        pattern = r'^[a-zA-Z0-9\s_-]+$'
        return bool(re.match(pattern, name))
    
    @staticmethod
    def validate_model_name(model: str) -> bool:
        """Validate AI model name format."""
        # Allow specific model name patterns
        allowed_models = [
            r'^gpt-[34](\.\d+)?(-\w+)?$',  # GPT models
            r'^claude-[23](\.\d+)?(-\w+)?$',  # Claude models
            r'^gemini-[12](\.\d+)?(-\w+)?$',  # Gemini models
            r'^llama-\d+(\.\d+)?(-\w+)?$',  # Llama models
        ]
        
        return any(re.match(pattern, model, re.IGNORECASE) for pattern in allowed_models)
    
    @staticmethod
    def validate_temperature(temperature: float) -> bool:
        """Validate temperature parameter."""
        return 0.0 <= temperature <= 2.0
    
    @staticmethod
    def validate_max_tokens(max_tokens: int) -> bool:
        """Validate max tokens parameter."""
        return 1 <= max_tokens <= 32000
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """Validate message content."""
        if not content or not content.strip():
            return False
        
        # Check length (max 50KB)
        if len(content) > 50000:
            return False
        
        # No null bytes or excessive control characters
        if '\x00' in content:
            return False
        
        return True


def sanitize_and_validate_input(
    data: Dict[str, Any],
    validation_rules: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Comprehensive input sanitization and validation.
    
    Args:
        data: Input data to sanitize and validate
        validation_rules: Optional validation rules to apply
    
    Returns:
        Sanitized and validated data
        
    Raises:
        ValidationError: If validation fails
    """
    # First sanitize the input
    try:
        sanitized_data = InputSanitizer.sanitize_json_input(data)
    except ValueError as e:
        raise ValidationError(f"Input sanitization failed: {e}")
    
    # Apply validation rules if provided
    if validation_rules:
        for field, rules in validation_rules.items():
            if field in sanitized_data:
                value = sanitized_data[field]
                
                # Check required fields
                if rules.get('required', False) and not value:
                    raise ValidationError(f"Field '{field}' is required")
                
                # Check data type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    raise ValidationError(f"Field '{field}' must be of type {expected_type.__name__}")
                
                # Check string length
                if isinstance(value, str):
                    min_length = rules.get('min_length', 0)
                    max_length = rules.get('max_length', float('inf'))
                    
                    if len(value) < min_length:
                        raise ValidationError(f"Field '{field}' must be at least {min_length} characters")
                    
                    if len(value) > max_length:
                        raise ValidationError(f"Field '{field}' must be at most {max_length} characters")
                
                # Check numeric ranges
                if isinstance(value, (int, float)):
                    min_value = rules.get('min_value')
                    max_value = rules.get('max_value')
                    
                    if min_value is not None and value < min_value:
                        raise ValidationError(f"Field '{field}' must be at least {min_value}")
                    
                    if max_value is not None and value > max_value:
                        raise ValidationError(f"Field '{field}' must be at most {max_value}")
                
                # Check allowed values
                allowed_values = rules.get('allowed_values')
                if allowed_values and value not in allowed_values:
                    raise ValidationError(f"Field '{field}' must be one of: {allowed_values}")
                
                # Custom validator function
                validator = rules.get('validator')
                if validator and not validator(value):
                    raise ValidationError(f"Field '{field}' failed custom validation")
    
    return sanitized_data