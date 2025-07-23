"""Input validation framework using Pydantic for comprehensive type safety."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class UserInputModel(BaseModel):
    """Base model for validating user inputs."""

    content: str = Field(..., min_length=1, max_length=10000, description="User input content")
    content_type: str = Field(default="text", pattern=r"^(text|code|query|command)$")
    metadata: dict[str, Any] | None = Field(default_factory=dict)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content for basic security concerns."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")

        # Check for potential injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # Javascript URLs
            r'on\w+\s*=',                 # Event handlers
            r'eval\s*\(',                 # eval() calls
            r'exec\s*\(',                 # exec() calls
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous content detected: {pattern}")

        return v.strip()


class ToolInputModel(BaseModel):
    """Model for validating tool execution inputs."""

    tool_name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout: int | None = Field(default=300, ge=1, le=3600)
    safe_mode: bool = Field(default=True)

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v):
        """Validate tool parameters for security."""
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")

        # Check for deeply nested structures (potential DoS)
        def check_depth(obj, depth=0):
            if depth > 10:
                raise ValueError("Parameters too deeply nested")
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)

        check_depth(v)
        return v


class ConfigInputModel(BaseModel):
    """Model for validating configuration inputs."""

    key: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-zA-Z_][a-zA-Z0-9_\.]*$")
    value: Any = Field(...)
    scope: str = Field(default="user", pattern=r"^(user|global|session)$")

    @model_validator(mode='after')
    def validate_sensitive_config(self):
        """Validate that sensitive configuration keys are not set."""
        sensitive_keys = ['password', 'secret', 'key', 'token', 'credential']
        key_lower = self.key.lower()

        if any(sensitive in key_lower for sensitive in sensitive_keys):
            raise ValueError("Cannot set sensitive configuration through this interface")

        return self


class InputValidator:
    """Comprehensive input validation framework."""

    def __init__(self):
        self.models = {
            'user_input': UserInputModel,
            'tool_input': ToolInputModel,
            'config_input': ConfigInputModel,
        }

    def validate_user_input(self, content: str, content_type: str = "text",
                          metadata: dict[str, Any] | None = None) -> UserInputModel:
        """Validate user input content."""
        try:
            return UserInputModel(
                content=content,
                content_type=content_type,
                metadata=metadata or {}
            )
        except Exception as e:
            raise ValidationError(f"User input validation failed: {e}") from e

    def validate_tool_input(self, tool_name: str, parameters: dict[str, Any],
                          timeout: int | None = None, safe_mode: bool = True) -> ToolInputModel:
        """Validate tool execution input."""
        try:
            return ToolInputModel(
                tool_name=tool_name,
                parameters=parameters,
                timeout=timeout,
                safe_mode=safe_mode
            )
        except Exception as e:
            raise ValidationError(f"Tool input validation failed: {e}") from e

    def validate_config_input(self, key: str, value: Any,
                            scope: str = "user") -> ConfigInputModel:
        """Validate configuration input."""
        try:
            return ConfigInputModel(
                key=key,
                value=value,
                scope=scope
            )
        except Exception as e:
            raise ValidationError(f"Config input validation failed: {e}") from e

    def validate_raw_input(self, input_type: str, data: dict[str, Any]) -> BaseModel:
        """Validate raw input data based on type."""
        if input_type not in self.models:
            raise ValidationError(f"Unknown input type: {input_type}")

        model_class = self.models[input_type]
        try:
            return model_class(**data)
        except Exception as e:
            raise ValidationError(f"Validation failed for {input_type}: {e}") from e

    def register_custom_model(self, input_type: str, model_class: type[BaseModel]) -> None:
        """Register a custom validation model."""
        if not issubclass(model_class, BaseModel):
            raise ValueError("Model class must inherit from BaseModel")

        self.models[input_type] = model_class
