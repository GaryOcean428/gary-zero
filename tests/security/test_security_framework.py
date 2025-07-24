"""Tests for the security framework components."""

import pytest

from framework.security import (
    AuditEventType,
    AuditLevel,
    AuditLogger,
    ContentSanitizer,
    InputValidator,
    RateLimitConfig,
    RateLimiter,
    RateLimitExceeded,
    RateLimitStrategy,
    ValidationError,
)


class TestInputValidator:
    """Test input validation functionality."""

    def setup_method(self):
        self.validator = InputValidator()

    def test_valid_user_input(self):
        """Test validation of valid user input."""
        result = self.validator.validate_user_input("Hello world", "text")
        assert result.content == "Hello world"
        assert result.content_type == "text"

    def test_invalid_user_input_empty(self):
        """Test validation fails for empty input."""
        with pytest.raises(ValidationError):
            self.validator.validate_user_input("", "text")

    def test_invalid_user_input_script(self):
        """Test validation fails for script injection."""
        with pytest.raises(ValidationError):
            self.validator.validate_user_input("<script>alert('xss')</script>", "text")

    def test_valid_tool_input(self):
        """Test validation of valid tool input."""
        result = self.validator.validate_tool_input(
            "test_tool", {"param1": "value1"}, timeout=60
        )
        assert result.tool_name == "test_tool"
        assert result.parameters == {"param1": "value1"}
        assert result.timeout == 60

    def test_invalid_tool_name(self):
        """Test validation fails for invalid tool name."""
        with pytest.raises(ValidationError):
            self.validator.validate_tool_input("invalid-tool-name", {})

    def test_deeply_nested_parameters(self):
        """Test validation fails for deeply nested parameters."""
        # Create parameters with 12 levels of nesting (exceeds 10 level limit)
        nested_params = {}
        current = nested_params
        for i in range(12):
            current[f"level{i}"] = {}
            current = current[f"level{i}"]

        with pytest.raises(ValidationError):
            self.validator.validate_tool_input("test_tool", nested_params)

    def test_valid_config_input(self):
        """Test validation of valid config input."""
        result = self.validator.validate_config_input("test_setting", "test_value")
        assert result.key == "test_setting"
        assert result.value == "test_value"
        assert result.scope == "user"

    def test_invalid_config_sensitive_key(self):
        """Test validation fails for sensitive config keys."""
        with pytest.raises(ValidationError):
            self.validator.validate_config_input("password", "secret123")


class TestRateLimiter:
    """Test rate limiting functionality."""

    def setup_method(self):
        self.rate_limiter = RateLimiter()

    @pytest.mark.asyncio
    async def test_sliding_window_rate_limit(self):
        """Test sliding window rate limiting."""
        config = RateLimitConfig(
            max_requests=3, window_size=1, strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        self.rate_limiter.configure_limit("test_endpoint", config)

        # First 3 requests should pass
        for i in range(3):
            await self.rate_limiter.check_limit("test_endpoint", "user1")

        # 4th request should fail
        with pytest.raises(RateLimitExceeded):
            await self.rate_limiter.check_limit("test_endpoint", "user1")

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limit(self):
        """Test token bucket rate limiting."""
        config = RateLimitConfig(
            max_requests=2, window_size=1, strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        self.rate_limiter.configure_limit("test_endpoint", config)

        # Should allow initial requests
        await self.rate_limiter.check_limit("test_endpoint", "user1")
        await self.rate_limiter.check_limit("test_endpoint", "user1")

        # Should fail when bucket is empty
        with pytest.raises(RateLimitExceeded):
            await self.rate_limiter.check_limit("test_endpoint", "user1")

    @pytest.mark.asyncio
    async def test_fixed_window_rate_limit(self):
        """Test fixed window rate limiting."""
        config = RateLimitConfig(
            max_requests=2, window_size=1, strategy=RateLimitStrategy.FIXED_WINDOW
        )
        self.rate_limiter.configure_limit("test_endpoint", config)

        # First 2 requests should pass
        await self.rate_limiter.check_limit("test_endpoint", "user1")
        await self.rate_limiter.check_limit("test_endpoint", "user1")

        # 3rd request should fail
        with pytest.raises(RateLimitExceeded):
            await self.rate_limiter.check_limit("test_endpoint", "user1")

    @pytest.mark.asyncio
    async def test_rate_limit_status(self):
        """Test getting rate limit status."""
        config = RateLimitConfig(
            max_requests=5, window_size=60, strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        self.rate_limiter.configure_limit("test_endpoint", config)

        # Make some requests
        await self.rate_limiter.check_limit("test_endpoint", "user1")
        await self.rate_limiter.check_limit("test_endpoint", "user1")

        status = await self.rate_limiter.get_limit_status("test_endpoint", "user1")
        assert status["status"] == "active"
        assert status["current_requests"] == 2
        assert status["remaining"] == 3

    def test_configure_global_limits(self):
        """Test configuring global rate limits."""
        self.rate_limiter.configure_global_limits()

        assert "user_input" in self.rate_limiter.configs
        assert "tool_execution" in self.rate_limiter.configs
        assert "api_call" in self.rate_limiter.configs
        assert "config_change" in self.rate_limiter.configs


class TestAuditLogger:
    """Test audit logging functionality."""

    def setup_method(self):
        self.audit_logger = AuditLogger()

    @pytest.mark.asyncio
    async def test_log_user_input(self):
        """Test logging user input events."""
        await self.audit_logger.log_user_input(
            user_id="user123", content="Test message", content_type="text"
        )

        events = await self.audit_logger.get_events(
            event_type=AuditEventType.USER_INPUT
        )
        assert len(events) == 1
        assert events[0].user_id == "user123"
        assert events[0].event_type == AuditEventType.USER_INPUT

    @pytest.mark.asyncio
    async def test_log_tool_execution(self):
        """Test logging tool execution events."""
        await self.audit_logger.log_tool_execution(
            user_id="user123",
            tool_name="test_tool",
            parameters={"param": "value"},
            success=True,
            execution_time=1.5,
        )

        events = await self.audit_logger.get_events(
            event_type=AuditEventType.TOOL_EXECUTION
        )
        assert len(events) == 1
        assert events[0].tool_name == "test_tool"
        assert events[0].input_data["success"] is True

    @pytest.mark.asyncio
    async def test_log_security_violation(self):
        """Test logging security violations."""
        await self.audit_logger.log_security_violation(
            event_details="Suspicious script injection attempt",
            severity=AuditLevel.WARNING,
            user_id="user123",
        )

        events = await self.audit_logger.get_events(
            event_type=AuditEventType.SECURITY_VIOLATION
        )
        assert len(events) == 1
        assert events[0].level == AuditLevel.WARNING

    @pytest.mark.asyncio
    async def test_get_security_summary(self):
        """Test getting security summary."""
        # Log some events
        await self.audit_logger.log_security_violation(
            "Test violation", AuditLevel.WARNING
        )
        await self.audit_logger.log_rate_limit(
            "test_endpoint", "user123", "sliding_window"
        )

        summary = await self.audit_logger.get_security_summary(hours=1)
        assert summary["total_events"] == 2
        assert summary["security_violations"] == 1
        assert summary["rate_limit_exceeded"] == 1

    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test filtering audit events."""
        # Log events for different users
        await self.audit_logger.log_user_input("user1", "message1")
        await self.audit_logger.log_user_input("user2", "message2")

        # Filter by user
        user1_events = await self.audit_logger.get_events(user_id="user1")
        assert len(user1_events) == 1
        assert user1_events[0].user_id == "user1"


class TestContentSanitizer:
    """Test content sanitization functionality."""

    def setup_method(self):
        self.sanitizer = ContentSanitizer()

    def test_sanitize_basic_text(self):
        """Test basic text sanitization."""
        result = self.sanitizer.sanitize_text("Hello <b>world</b>")
        assert result == "Hello &lt;b&gt;world&lt;/b&gt;"

    def test_sanitize_script_injection(self):
        """Test script injection sanitization."""
        malicious = "<script>alert('xss')</script>Hello"
        result = self.sanitizer.sanitize_text(malicious)
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_html_with_allowlist(self):
        """Test HTML sanitization with allowed tags."""
        html_content = "<p>Hello <script>alert('xss')</script> <b>world</b></p>"
        result = self.sanitizer.sanitize_text(html_content, allow_html=True)
        assert "<script>" not in result
        assert "<p>" in result  # Should preserve allowed tags

    def test_sanitize_sql_input(self):
        """Test SQL injection sanitization."""
        malicious = "'; DROP TABLE users; --"
        result = self.sanitizer.sanitize_sql_input(malicious)
        assert "DROP" not in result
        assert "''" in result  # Single quotes should be escaped

    def test_sanitize_command_input(self):
        """Test command injection sanitization."""
        malicious = "ls; rm -rf /"
        result = self.sanitizer.sanitize_command_input(malicious)
        assert ";" not in result
        assert "rm" not in result

    def test_sanitize_url(self):
        """Test URL sanitization."""
        # Valid URL
        valid_url = "https://example.com/path"
        result = self.sanitizer.sanitize_url(valid_url)
        assert result == "https://example.com/path"

        # Invalid scheme
        invalid_url = "javascript:alert('xss')"
        result = self.sanitizer.sanitize_url(invalid_url)
        assert result is None

    def test_sanitize_file_path(self):
        """Test file path sanitization."""
        # Valid path
        valid_path = "documents/file.txt"
        result = self.sanitizer.sanitize_file_path(valid_path)
        assert result == "documents/file.txt"

        # Path traversal attempt
        malicious_path = "../../../etc/passwd"
        result = self.sanitizer.sanitize_file_path(malicious_path)
        assert result == "etc/passwd"

    def test_sanitize_json_data(self):
        """Test JSON data sanitization."""
        data = {
            "safe_key": "safe_value",
            "dangerous_key": "<script>alert('xss')</script>",
            "nested": {"list": ["item1", "<script>evil</script>"]},
        }

        result = self.sanitizer.sanitize_json_data(data)
        assert result["safe_key"] == "safe_value"
        assert "<script>" not in result["dangerous_key"]
        assert "<script>" not in str(result["nested"]["list"])

    def test_detect_suspicious_patterns(self):
        """Test suspicious pattern detection."""
        malicious_text = "<script>alert('xss')</script> OR 1=1"
        patterns = self.sanitizer.detect_suspicious_patterns(malicious_text)

        assert patterns["script_injection"] is True
        assert patterns["sql_injection"] is True
        assert patterns["excessive_length"] is False

    def test_sanitize_user_input_by_type(self):
        """Test user input sanitization by type."""
        # HTML type
        html_input = "<p>Hello <script>alert('xss')</script></p>"
        result = self.sanitizer.sanitize_user_input(html_input, "html")
        assert "<p>" in result
        assert "<script>" not in result

        # SQL type
        sql_input = "'; DROP TABLE users; --"
        result = self.sanitizer.sanitize_user_input(sql_input, "sql")
        assert "DROP" not in result

        # Command type
        cmd_input = "ls; rm -rf /"
        result = self.sanitizer.sanitize_user_input(cmd_input, "command")
        assert ";" not in result


@pytest.mark.asyncio
async def test_security_integration():
    """Test integration between security components."""
    # Initialize components
    validator = InputValidator()
    rate_limiter = RateLimiter()
    audit_logger = AuditLogger()
    sanitizer = ContentSanitizer()

    # Configure rate limits
    rate_limiter.configure_global_limits()

    # Simulate a user request with potential security issues
    user_id = "test_user"
    raw_input = "<script>alert('xss')</script>Hello world"

    # 1. Sanitize input
    sanitized_input = sanitizer.sanitize_user_input(raw_input)

    # 2. Validate input
    try:
        validated_input = validator.validate_user_input(sanitized_input, "text")
    except ValidationError as e:
        await audit_logger.log_security_violation(
            f"Input validation failed: {e}", AuditLevel.WARNING, user_id=user_id
        )
        return

    # 3. Check rate limits
    try:
        await rate_limiter.check_limit("user_input", user_id)
    except RateLimitExceeded:
        await audit_logger.log_rate_limit("user_input", user_id, "sliding_window")
        return

    # 4. Log successful processing
    await audit_logger.log_user_input(
        user_id=user_id,
        content=validated_input.content,
        content_type=validated_input.content_type,
    )

    # Verify audit log contains expected events
    events = await audit_logger.get_events(limit=10)
    assert len(events) >= 1
    assert any(e.event_type == AuditEventType.USER_INPUT for e in events)
