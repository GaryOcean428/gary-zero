"""Content sanitization for user inputs and outputs."""

import html
import re
from typing import Any
from urllib.parse import urlparse


class ContentSanitizer:
    """Comprehensive content sanitization for security."""

    def __init__(self):
        # Define dangerous patterns
        self.script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'on\w+\s*=',  # Event handlers
        ]

        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\'\s*(OR|AND)\s+\'\w+\'\s*=\s*\'\w+)",
        ]

        self.command_injection_patterns = [
            r'[\;\|&`$\(\){}]',
            r'(sudo|rm|mv|cp|cat|grep|awk|sed|curl|wget)',
            r'(\.\./|\.\.\\\\)',
        ]

        # Safe URL schemes
        self.safe_schemes = {'http', 'https', 'ftp', 'ftps', 'mailto'}

        # HTML tags to allow (basic formatting)
        self.allowed_tags = {
            'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
        }

    def sanitize_text(self, text: str, allow_html: bool = False) -> str:
        """Sanitize text content for safe display."""
        if not isinstance(text, str):
            return str(text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Check for script injection
        for pattern in self.script_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        if allow_html:
            # Allow basic HTML but sanitize attributes
            text = self._sanitize_html(text)
        else:
            # Escape all HTML
            text = html.escape(text)

        return text.strip()

    def sanitize_sql_input(self, text: str) -> str:
        """Sanitize input to prevent SQL injection."""
        if not isinstance(text, str):
            return str(text)

        # Check for SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Replace dangerous SQL keywords and operators
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Escape single quotes
        text = text.replace("'", "''")

        return text.strip()

    def sanitize_command_input(self, text: str) -> str:
        """Sanitize input to prevent command injection."""
        if not isinstance(text, str):
            return str(text)

        # Check for command injection patterns
        for pattern in self.command_injection_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove path traversal attempts
        text = text.replace('..', '')

        return text.strip()

    def sanitize_url(self, url: str) -> str | None:
        """Sanitize and validate URLs."""
        if not isinstance(url, str):
            return None

        try:
            parsed = urlparse(url.strip())

            # Check scheme
            if parsed.scheme.lower() not in self.safe_schemes:
                return None

            # Check for dangerous patterns in URL
            if any(re.search(pattern, url, re.IGNORECASE) for pattern in self.script_patterns):
                return None

            # Reconstruct clean URL
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        except Exception:
            return None

    def sanitize_file_path(self, path: str) -> str | None:
        """Sanitize file paths to prevent directory traversal."""
        if not isinstance(path, str):
            return None

        # Remove dangerous path components
        path = path.replace('..', '').replace('~', '')

        # Remove leading/trailing slashes and normalize
        path = path.strip('/')

        # Check for absolute paths (should be relative)
        if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
            return None

        # Check for dangerous characters
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$']
        if any(char in path for char in dangerous_chars):
            return None

        return path

    def sanitize_json_data(self, data: Any, max_depth: int = 10) -> Any:
        """Sanitize JSON data recursively."""
        return self._sanitize_recursive(data, depth=0, max_depth=max_depth)

    def _sanitize_recursive(self, obj: Any, depth: int, max_depth: int) -> Any:
        """Recursively sanitize data structures."""
        if depth > max_depth:
            return "[TRUNCATED: Max depth exceeded]"

        if isinstance(obj, str):
            return self.sanitize_text(obj)
        elif isinstance(obj, dict):
            if len(obj) > 100:  # Limit dictionary size
                return dict.fromkeys(list(obj.keys())[:10], "[TRUNCATED: Dict too large]")
            return {
                self.sanitize_text(str(k)): self._sanitize_recursive(v, depth + 1, max_depth)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            if len(obj) > 100:  # Limit list size
                return [self._sanitize_recursive(item, depth + 1, max_depth) for item in obj[:100]]
            return [self._sanitize_recursive(item, depth + 1, max_depth) for item in obj]
        elif isinstance(obj, (int, float, bool, type(None))):
            return obj
        else:
            return self.sanitize_text(str(obj))

    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content, allowing only safe tags."""
        # Simple HTML sanitization - remove script tags and dangerous attributes

        # Remove script tags completely
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)

        # Remove dangerous attributes
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur']
        for attr in dangerous_attrs:
            html_content = re.sub(f'{attr}="[^"]*"', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(f"{attr}='[^']*'", '', html_content, flags=re.IGNORECASE)

        # Remove style attributes that could contain javascript
        html_content = re.sub(r'style="[^"]*expression[^"]*"', '', html_content, flags=re.IGNORECASE)

        return html_content

    def validate_input_length(self, text: str, max_length: int = 10000) -> bool:
        """Validate input length to prevent DoS attacks."""
        return len(text) <= max_length

    def detect_suspicious_patterns(self, text: str) -> dict[str, bool]:
        """Detect various suspicious patterns in text."""
        if not isinstance(text, str):
            return {}

        return {
            'script_injection': any(re.search(pattern, text, re.IGNORECASE) for pattern in self.script_patterns),
            'sql_injection': any(re.search(pattern, text, re.IGNORECASE) for pattern in self.sql_patterns),
            'command_injection': any(re.search(pattern, text, re.IGNORECASE) for pattern in self.command_injection_patterns),
            'path_traversal': '..' in text or '~' in text,
            'excessive_length': len(text) > 10000,
            'null_bytes': '\x00' in text,
        }

    def sanitize_user_input(self, user_input: str, input_type: str = "text") -> str:
        """Main method to sanitize user input based on type."""
        if not isinstance(user_input, str):
            user_input = str(user_input)

        # Basic sanitization for all types
        sanitized = self.sanitize_text(user_input)

        # Additional sanitization based on input type
        if input_type == "sql":
            sanitized = self.sanitize_sql_input(sanitized)
        elif input_type == "command":
            sanitized = self.sanitize_command_input(sanitized)
        elif input_type == "html":
            sanitized = self.sanitize_text(user_input, allow_html=True)
        elif input_type == "url":
            sanitized = self.sanitize_url(sanitized) or ""
        elif input_type == "filepath":
            sanitized = self.sanitize_file_path(sanitized) or ""

        return sanitized
