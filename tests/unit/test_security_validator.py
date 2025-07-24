"""
Unit tests for security validator module.
"""

from security.validator import CodeValidationRequest, SecurityLevel, validate_code


class TestSecureCodeValidator:
    """Test cases for the SecureCodeValidator class."""

    def test_safe_code_validation(self, code_validator, sample_safe_code):
        """Test validation of safe code."""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=sample_safe_code, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.blocked_items) == 0

    def test_unsafe_code_validation(self, code_validator, sample_unsafe_code):
        """Test validation of unsafe code."""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=sample_unsafe_code, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is False
        assert len(result.blocked_items) > 0

        # Check for specific blocked items
        blocked_items_str = " ".join(result.blocked_items)
        assert "os" in blocked_items_str
        assert "subprocess" in blocked_items_str

    def test_blocked_functions(self, code_validator):
        """Test detection of blocked functions."""
        dangerous_code = """
eval("1+1")
exec("print('hello')")
__import__("os")
"""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=dangerous_code, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is False
        assert any("eval" in item for item in result.blocked_items)
        assert any("exec" in item for item in result.blocked_items)

    def test_unauthorized_imports(self, code_validator):
        """Test detection of unauthorized imports."""
        code_with_bad_imports = """
import os
import sys
import subprocess
from socket import socket
"""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=code_with_bad_imports, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is False
        assert len(result.blocked_items) >= 4  # All imports should be blocked

    def test_security_levels(self, code_validator):
        """Test different security levels."""
        code_with_requests = """
import requests
response = requests.get("https://api.example.com")
"""

        # Should be blocked in STRICT mode
        strict_result = code_validator.validate_code(
            CodeValidationRequest(
                code=code_with_requests, security_level=SecurityLevel.STRICT
            )
        )
        assert strict_result.is_valid is False

        # Should be allowed in MODERATE mode
        moderate_result = code_validator.validate_code(
            CodeValidationRequest(
                code=code_with_requests, security_level=SecurityLevel.MODERATE
            )
        )
        assert moderate_result.is_valid is True

    def test_syntax_error_handling(self, code_validator):
        """Test handling of syntax errors."""
        invalid_code = """
def broken_function(
    print("This has a syntax error"
"""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=invalid_code, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is False
        assert any("syntax error" in error.lower() for error in result.errors)

    def test_dangerous_attributes(self, code_validator):
        """Test detection of dangerous attribute access."""
        code_with_dangerous_attrs = """
obj = object()
print(obj.__class__)
print(obj.__dict__)
print(obj.__globals__)
"""
        result = code_validator.validate_code(
            CodeValidationRequest(
                code=code_with_dangerous_attrs, security_level=SecurityLevel.STRICT
            )
        )
        assert result.is_valid is False
        assert any("__class__" in item for item in result.blocked_items)
        assert any("__dict__" in item for item in result.blocked_items)
        assert any("__globals__" in item for item in result.blocked_items)


def test_convenience_functions():
    """Test convenience functions for code validation."""
    safe_code = "print('Hello, World!')"
    unsafe_code = "import os; os.system('ls')"

    # Test validate_code function
    safe_result = validate_code(safe_code, SecurityLevel.STRICT)
    assert safe_result.is_valid is True

    unsafe_result = validate_code(unsafe_code, SecurityLevel.STRICT)
    assert unsafe_result.is_valid is False

    # Test is_code_safe function
    from security.validator import is_code_safe

    assert is_code_safe(safe_code, SecurityLevel.STRICT) is True
    assert is_code_safe(unsafe_code, SecurityLevel.STRICT) is False
