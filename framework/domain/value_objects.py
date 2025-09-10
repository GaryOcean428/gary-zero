"""Value objects for the Gary-Zero framework.

Implements value object patterns for immutable data types that are
defined by their attributes rather than identity.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for value objects - immutable objects defined by their attributes."""
    
    def __post_init__(self):
        """Validate the value object after creation."""
        self.validate()
    
    @abstractmethod
    def validate(self) -> None:
        """Validate the value object's data."""
        pass


@dataclass(frozen=True)
class ModelConfiguration(ValueObject):
    """Value object representing AI model configuration."""
    
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    def validate(self) -> None:
        """Validate model configuration parameters."""
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be greater than 0")
        
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("Frequency penalty must be between -2.0 and 2.0")
        
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("Presence penalty must be between -2.0 and 2.0")


@dataclass(frozen=True)
class PromptTemplate(ValueObject):
    """Value object representing a prompt template."""
    
    name: str
    template: str
    variables: List[str]
    metadata: Dict[str, Any]
    
    def validate(self) -> None:
        """Validate prompt template."""
        if not self.name:
            raise ValueError("Prompt name cannot be empty")
        
        if not self.template:
            raise ValueError("Prompt template cannot be empty")
        
        # Check that all variables in template are declared
        import re
        template_vars = set(re.findall(r'\{(\w+)\}', self.template))
        declared_vars = set(self.variables)
        
        missing_vars = template_vars - declared_vars
        if missing_vars:
            raise ValueError(f"Template uses undeclared variables: {missing_vars}")
    
    def render(self, **kwargs: Any) -> str:
        """Render the template with provided variables."""
        # Validate all required variables are provided
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        return self.template.format(**kwargs)


@dataclass(frozen=True)
class SecurityContext(ValueObject):
    """Value object representing security context for operations."""
    
    user_id: str
    session_id: str
    permissions: List[str]
    ip_address: str = ""
    user_agent: str = ""
    
    def validate(self) -> None:
        """Validate security context."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        
        if not self.session_id:
            raise ValueError("Session ID cannot be empty")
        
        if not self.permissions:
            raise ValueError("Permissions list cannot be empty")
    
    def has_permission(self, permission: str) -> bool:
        """Check if the context has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions


@dataclass(frozen=True)
class ToolParameters(ValueObject):
    """Value object representing validated tool parameters."""
    
    tool_name: str
    parameters: Dict[str, Any]
    schema_version: str = "1.0"
    
    def validate(self) -> None:
        """Validate tool parameters."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")


@dataclass(frozen=True)
class RateLimitConfig(ValueObject):
    """Value object representing rate limiting configuration."""
    
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    
    def validate(self) -> None:
        """Validate rate limit configuration."""
        if self.requests_per_minute <= 0:
            raise ValueError("Requests per minute must be greater than 0")
        
        if self.requests_per_hour <= 0:
            raise ValueError("Requests per hour must be greater than 0")
        
        if self.burst_limit <= 0:
            raise ValueError("Burst limit must be greater than 0")
        
        if self.requests_per_hour < self.requests_per_minute:
            raise ValueError("Hourly limit cannot be less than per-minute limit")
        
        if self.burst_limit > self.requests_per_minute:
            raise ValueError("Burst limit cannot exceed per-minute limit")


@dataclass(frozen=True)
class ErrorInfo(ValueObject):
    """Value object representing error information."""
    
    error_code: str
    error_message: str
    timestamp: str
    context: Dict[str, Any]
    
    def validate(self) -> None:
        """Validate error information."""
        if not self.error_code:
            raise ValueError("Error code cannot be empty")
        
        if not self.error_message:
            raise ValueError("Error message cannot be empty")
        
        if not self.timestamp:
            raise ValueError("Timestamp cannot be empty")