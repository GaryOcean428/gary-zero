"""Tests for enhanced input sanitization and validation."""

import pytest
from framework.security.enhanced_sanitizer import (
    InputSanitizer,
    InputValidator,
    ValidationError,
    sanitize_and_validate_input,
)


class TestInputSanitizer:
    """Test input sanitization functionality."""
    
    def test_basic_text_sanitization(self):
        """Test basic text sanitization."""
        text = "Hello, World!"  # Simple text without HTML
        result = InputSanitizer.sanitize_text(text)
        assert result == "Hello, World!"
    
    def test_html_sanitization(self):
        """Test HTML content sanitization."""
        text = "Hello, <b>World!</b>"
        result = InputSanitizer.sanitize_text(text)
        assert result == "Hello, &lt;b&gt;World!&lt;/b&gt;"
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        malicious_text = "'; DROP TABLE users; --"
        
        with pytest.raises(ValueError, match="SQL pattern"):
            InputSanitizer.sanitize_text(malicious_text)
    
    def test_xss_pattern_detection(self):
        """Test XSS pattern detection."""
        malicious_text = "<script>alert('xss')</script>"
        
        with pytest.raises(ValueError, match="XSS pattern"):
            InputSanitizer.sanitize_text(malicious_text)
    
    def test_command_injection_detection(self):
        """Test command injection pattern detection."""
        malicious_text = "test; rm -rf /"
        
        with pytest.raises(ValueError, match="command injection"):
            InputSanitizer.sanitize_text(malicious_text)
    
    def test_file_path_sanitization(self):
        """Test file path sanitization."""
        safe_path = "documents/file.txt"
        result = InputSanitizer.sanitize_file_path(safe_path)
        assert "file.txt" in result
    
    def test_path_traversal_detection(self):
        """Test path traversal attack detection."""
        malicious_path = "../../../etc/passwd"
        
        with pytest.raises(ValueError, match="Dangerous path pattern"):
            InputSanitizer.sanitize_file_path(malicious_path)
    
    def test_url_sanitization(self):
        """Test URL sanitization."""
        safe_url = "https://example.com/page"
        result = InputSanitizer.sanitize_url(safe_url)
        assert result == safe_url
    
    def test_dangerous_url_scheme(self):
        """Test dangerous URL scheme detection."""
        malicious_url = "javascript:alert('xss')"
        
        with pytest.raises(ValueError, match="Dangerous URL scheme"):
            InputSanitizer.sanitize_url(malicious_url)
    
    def test_json_input_sanitization(self):
        """Test JSON input sanitization."""
        data = {
            "name": "John Doe",
            "message": "<script>alert('xss')</script>",
            "nested": {
                "value": "Safe content"
            }
        }
        
        with pytest.raises(ValueError, match="XSS pattern"):
            InputSanitizer.sanitize_json_input(data)
    
    def test_safe_json_input_sanitization(self):
        """Test safe JSON input sanitization."""
        data = {
            "name": "John Doe",
            "message": "Hello, world!",
            "nested": {
                "value": "Safe content"
            }
        }
        
        result = InputSanitizer.sanitize_json_input(data)
        assert result["name"] == "John Doe"
        assert result["message"] == "Hello, world!"
        assert result["nested"]["value"] == "Safe content"
    
    def test_text_length_limit(self):
        """Test text length limitation."""
        long_text = "a" * 10001
        
        with pytest.raises(ValueError, match="exceeds maximum length"):
            InputSanitizer.sanitize_text(long_text)
    
    def test_null_byte_removal(self):
        """Test null byte removal."""
        text_with_null = "Hello\x00World"
        result = InputSanitizer.sanitize_text(text_with_null)
        assert "\x00" not in result
        assert result == "HelloWorld"
    
    def test_control_character_removal(self):
        """Test control character removal."""
        text_with_control = "Hello\x08\x0E World"
        result = InputSanitizer.sanitize_text(text_with_control)
        assert result == "Hello World"


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_email_validation(self):
        """Test email address validation."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test@domain"  # Missing TLD
        ]
        
        for email in valid_emails:
            assert InputValidator.validate_email(email), f"Should be valid: {email}"
        
        for email in invalid_emails:
            assert not InputValidator.validate_email(email), f"Should be invalid: {email}"
    
    def test_username_validation(self):
        """Test username validation."""
        valid_usernames = [
            "john_doe",
            "user123",
            "test-user",
            "ValidUser"
        ]
        
        invalid_usernames = [
            "ab",  # too short
            "a" * 31,  # too long
            "user@name",  # invalid character
            "user name"  # space not allowed
        ]
        
        for username in valid_usernames:
            assert InputValidator.validate_username(username), f"Should be valid: {username}"
        
        for username in invalid_usernames:
            assert not InputValidator.validate_username(username), f"Should be invalid: {username}"
    
    def test_password_validation(self):
        """Test password strength validation."""
        valid_passwords = [
            "SecurePass123!",
            "MyPassword@2024",
            "Complex1$Password"
        ]
        
        invalid_passwords = [
            "weak",  # too short
            "password123",  # no uppercase
            "PASSWORD123",  # no lowercase
            "Password",  # no digit
            "Password123"  # no special character
        ]
        
        for password in valid_passwords:
            assert InputValidator.validate_password(password), f"Should be valid: {password}"
        
        for password in invalid_passwords:
            assert not InputValidator.validate_password(password), f"Should be invalid: {password}"
    
    def test_agent_name_validation(self):
        """Test agent name validation."""
        valid_names = [
            "Chat Agent",
            "agent-1",
            "Agent_Bot",
            "MyAgent123"
        ]
        
        invalid_names = [
            "",  # empty
            "a" * 51,  # too long
            "Agent@Bot",  # invalid character
            "Agent$Bot"  # invalid character
        ]
        
        for name in valid_names:
            assert InputValidator.validate_agent_name(name), f"Should be valid: {name}"
        
        for name in invalid_names:
            assert not InputValidator.validate_agent_name(name), f"Should be invalid: {name}"
    
    def test_model_name_validation(self):
        """Test AI model name validation."""
        valid_models = [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-sonnet",
            "claude-2.1",
            "gemini-1.5-pro",
            "llama-3.1-8b"
        ]
        
        invalid_models = [
            "invalid-model",
            "gpt5",  # wrong format
            "random-name"
        ]
        
        for model in valid_models:
            assert InputValidator.validate_model_name(model), f"Should be valid: {model}"
        
        for model in invalid_models:
            assert not InputValidator.validate_model_name(model), f"Should be invalid: {model}"
    
    def test_temperature_validation(self):
        """Test temperature parameter validation."""
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        invalid_temps = [-0.1, 2.1, 5.0]
        
        for temp in valid_temps:
            assert InputValidator.validate_temperature(temp), f"Should be valid: {temp}"
        
        for temp in invalid_temps:
            assert not InputValidator.validate_temperature(temp), f"Should be invalid: {temp}"
    
    def test_max_tokens_validation(self):
        """Test max tokens parameter validation."""
        valid_tokens = [1, 100, 4096, 32000]
        invalid_tokens = [0, -1, 32001]
        
        for tokens in valid_tokens:
            assert InputValidator.validate_max_tokens(tokens), f"Should be valid: {tokens}"
        
        for tokens in invalid_tokens:
            assert not InputValidator.validate_max_tokens(tokens), f"Should be invalid: {tokens}"
    
    def test_message_content_validation(self):
        """Test message content validation."""
        valid_content = [
            "Hello, world!",
            "A" * 1000,  # reasonable length
            "Multi\nline\ncontent"
        ]
        
        invalid_content = [
            "",  # empty
            "   ",  # whitespace only
            "\x00content",  # null byte
            "A" * 50001  # too long
        ]
        
        for content in valid_content:
            assert InputValidator.validate_message_content(content), f"Should be valid: {content}"
        
        for content in invalid_content:
            assert not InputValidator.validate_message_content(content), f"Should be invalid: {content}"


class TestSanitizeAndValidateInput:
    """Test comprehensive input sanitization and validation."""
    
    def test_successful_validation(self):
        """Test successful input validation."""
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "message": "Hello, world!"
        }
        
        validation_rules = {
            "username": {
                "required": True,
                "type": str,
                "min_length": 3,
                "max_length": 30,
                "validator": InputValidator.validate_username
            },
            "email": {
                "required": True,
                "type": str,
                "validator": InputValidator.validate_email
            },
            "message": {
                "required": True,
                "type": str,
                "max_length": 1000
            }
        }
        
        result = sanitize_and_validate_input(data, validation_rules)
        assert result["username"] == "john_doe"
        assert result["email"] == "john@example.com"
        assert result["message"] == "Hello, world!"
    
    def test_validation_failure_required_field(self):
        """Test validation failure for required field."""
        data = {
            "username": "",
            "email": "john@example.com"
        }
        
        validation_rules = {
            "username": {"required": True, "type": str}
        }
        
        with pytest.raises(ValidationError, match="Field 'username' is required"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_validation_failure_wrong_type(self):
        """Test validation failure for wrong type."""
        data = {
            "age": "twenty"
        }
        
        validation_rules = {
            "age": {"type": int}
        }
        
        with pytest.raises(ValidationError, match="must be of type int"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_validation_failure_string_length(self):
        """Test validation failure for string length."""
        data = {
            "name": "Jo"
        }
        
        validation_rules = {
            "name": {"type": str, "min_length": 3}
        }
        
        with pytest.raises(ValidationError, match="must be at least 3 characters"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_validation_failure_numeric_range(self):
        """Test validation failure for numeric range."""
        data = {
            "temperature": 3.0
        }
        
        validation_rules = {
            "temperature": {"type": float, "max_value": 2.0}
        }
        
        with pytest.raises(ValidationError, match="must be at most 2.0"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_validation_failure_allowed_values(self):
        """Test validation failure for allowed values."""
        data = {
            "status": "invalid"
        }
        
        validation_rules = {
            "status": {"allowed_values": ["active", "inactive", "pending"]}
        }
        
        with pytest.raises(ValidationError, match="must be one of"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_validation_failure_custom_validator(self):
        """Test validation failure for custom validator."""
        data = {
            "email": "invalid-email"
        }
        
        validation_rules = {
            "email": {"validator": InputValidator.validate_email}
        }
        
        with pytest.raises(ValidationError, match="failed custom validation"):
            sanitize_and_validate_input(data, validation_rules)
    
    def test_sanitization_before_validation(self):
        """Test that sanitization happens before validation."""
        data = {
            "message": "  Hello, world!  "
        }
        
        result = sanitize_and_validate_input(data)
        assert result["message"] == "Hello, world!"  # Should be trimmed