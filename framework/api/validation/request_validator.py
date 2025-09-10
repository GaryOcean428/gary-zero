"""API validation layer integrating security components.

Provides comprehensive API request validation including:
- Input sanitization and validation
- Rate limiting enforcement
- Authentication verification
- Request/response schema validation
- Security context management
"""

import logging
from typing import Any, Dict, Optional, Union, Callable
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

from framework.security.enhanced_sanitizer import (
    sanitize_and_validate_input,
    InputValidator,
    ValidationError
)
from framework.security.enhanced_rate_limiter import (
    EnhancedRateLimiter,
    RateLimitConfig,
    create_rate_limiter
)
from framework.domain.value_objects import SecurityContext, ModelConfiguration
from framework.domain.events import get_event_bus

logger = logging.getLogger(__name__)


class APIValidationError(HTTPException):
    """Custom exception for API validation errors."""
    
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class SecurityContextManager:
    """Manages security context for API requests."""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    async def get_security_context(
        self, 
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> SecurityContext:
        """Extract and validate security context from request."""
        # Extract user info from token (simplified - would use JWT in production)
        user_id = await self._extract_user_id(credentials.credentials)
        
        # Extract request metadata
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Create security context
        return SecurityContext(
            user_id=user_id,
            session_id=self._generate_session_id(request),
            permissions=await self._get_user_permissions(user_id),
            ip_address=client_ip,
            user_agent=user_agent
        )
    
    async def _extract_user_id(self, token: str) -> str:
        """Extract user ID from authentication token."""
        # Simplified implementation - would use proper JWT validation
        if not token or token == "invalid":
            raise APIValidationError("Invalid authentication token", 401)
        
        # Mock user ID extraction
        return f"user_{hash(token) % 10000}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _generate_session_id(self, request: Request) -> str:
        """Generate session ID for request."""
        # Simplified session ID generation
        import hashlib
        content = f"{request.url}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _get_user_permissions(self, user_id: str) -> list[str]:
        """Get user permissions (simplified implementation)."""
        # Mock permissions based on user ID
        if "admin" in user_id:
            return ["admin", "agent.create", "agent.pause", "agent.stop", 
                   "message.process", "tool.execute", "session.end"]
        else:
            return ["message.process", "tool.execute"]


class RequestValidator:
    """Validates API requests using security components."""
    
    def __init__(self, rate_limiter: Optional[EnhancedRateLimiter] = None):
        self.rate_limiter = rate_limiter or create_rate_limiter()
        self.event_bus = get_event_bus()
    
    async def validate_chat_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chat API request."""
        validation_rules = {
            "message": {
                "required": True,
                "type": str,
                "min_length": 1,
                "max_length": 10000,
                "validator": InputValidator.validate_message_content
            },
            "model": {
                "type": str,
                "validator": InputValidator.validate_model_name
            },
            "temperature": {
                "type": float,
                "validator": InputValidator.validate_temperature
            },
            "max_tokens": {
                "type": int,
                "validator": InputValidator.validate_max_tokens
            }
        }
        
        try:
            sanitized_data = sanitize_and_validate_input(data, validation_rules)
            
            # Create model configuration
            config = ModelConfiguration(
                model_name=sanitized_data.get("model", "gpt-4"),
                temperature=sanitized_data.get("temperature", 0.7),
                max_tokens=sanitized_data.get("max_tokens", 4096)
            )
            
            # Add validated config to response
            sanitized_data["_validated_config"] = config
            
            return sanitized_data
            
        except ValidationError as e:
            raise APIValidationError(f"Invalid chat request: {e}")
        except ValueError as e:
            raise APIValidationError(f"Invalid model configuration: {e}")
    
    async def validate_agent_creation_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent creation request."""
        validation_rules = {
            "name": {
                "required": True,
                "type": str,
                "min_length": 1,
                "max_length": 50,
                "validator": InputValidator.validate_agent_name
            },
            "agent_type": {
                "required": True,
                "type": str,
                "allowed_values": ["chat", "tool", "analysis", "creative"]
            },
            "model": {
                "type": str,
                "validator": InputValidator.validate_model_name
            },
            "temperature": {
                "type": float,
                "validator": InputValidator.validate_temperature
            }
        }
        
        try:
            return sanitize_and_validate_input(data, validation_rules)
        except ValidationError as e:
            raise APIValidationError(f"Invalid agent creation request: {e}")
    
    async def validate_tool_execution_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool execution request."""
        validation_rules = {
            "tool_name": {
                "required": True,
                "type": str,
                "min_length": 1,
                "max_length": 100
            },
            "parameters": {
                "required": True,
                "type": dict
            },
            "agent_id": {
                "required": True,
                "type": str,
                "min_length": 1
            }
        }
        
        try:
            return sanitize_and_validate_input(data, validation_rules)
        except ValidationError as e:
            raise APIValidationError(f"Invalid tool execution request: {e}")
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        endpoint: str, 
        tokens_required: float = 1.0
    ) -> None:
        """Check rate limit for user and endpoint."""
        result = await self.rate_limiter.check_rate_limit(user_id, endpoint, tokens_required)
        
        if not result.allowed:
            retry_after = result.retry_after or 60
            raise APIValidationError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                status_code=429
            )
    
    async def validate_file_upload(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file upload request."""
        validation_rules = {
            "filename": {
                "required": True,
                "type": str,
                "min_length": 1,
                "max_length": 255
            },
            "content_type": {
                "required": True,
                "type": str,
                "allowed_values": [
                    "text/plain", "text/csv", "application/json", 
                    "application/pdf", "image/jpeg", "image/png"
                ]
            },
            "size": {
                "required": True,
                "type": int,
                "min_value": 1,
                "max_value": 50 * 1024 * 1024  # 50MB max
            }
        }
        
        try:
            return sanitize_and_validate_input(file_data, validation_rules)
        except ValidationError as e:
            raise APIValidationError(f"Invalid file upload: {e}")


class APISecurityMiddleware:
    """Middleware for API security enforcement."""
    
    def __init__(self, validator: RequestValidator, security_manager: SecurityContextManager):
        self.validator = validator
        self.security_manager = security_manager
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware."""
        try:
            # Skip security for health checks and static content
            if self._should_skip_security(request):
                return await call_next(request)
            
            # Extract security context
            credentials = await self._extract_credentials(request)
            if credentials:
                security_context = await self.security_manager.get_security_context(
                    request, credentials
                )
                
                # Store in request state
                request.state.security_context = security_context
                
                # Check rate limits for authenticated requests
                endpoint = self._get_endpoint_name(request)
                await self.validator.check_rate_limit(
                    security_context.user_id, 
                    endpoint
                )
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except APIValidationError:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            raise APIValidationError("Security validation failed", 500)
    
    def _should_skip_security(self, request: Request) -> bool:
        """Check if request should skip security validation."""
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    async def _extract_credentials(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Extract authentication credentials from request."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Get endpoint name for rate limiting."""
        path = request.url.path
        
        # Map paths to endpoint names
        if path.startswith("/api/chat"):
            return "api.chat"
        elif path.startswith("/api/agents"):
            return "api.agents"
        elif path.startswith("/api/tools"):
            return "api.tool"
        elif path.startswith("/api/upload"):
            return "api.upload"
        elif path.startswith("/auth"):
            return "auth.login"
        else:
            return "default"


def create_api_validator(rate_limiter: Optional[EnhancedRateLimiter] = None) -> RequestValidator:
    """Factory function to create API validator."""
    return RequestValidator(rate_limiter)


def create_security_manager() -> SecurityContextManager:
    """Factory function to create security context manager."""
    return SecurityContextManager()


# Dependency injection helpers
async def get_request_validator() -> RequestValidator:
    """Dependency injection for request validator."""
    return create_api_validator()


async def get_security_manager() -> SecurityContextManager:
    """Dependency injection for security manager."""
    return create_security_manager()


async def get_security_context(
    request: Request,
    security_manager: SecurityContextManager = Depends(get_security_manager)
) -> SecurityContext:
    """Dependency injection for security context."""
    # Try to get from request state first (set by middleware)
    if hasattr(request.state, "security_context"):
        return request.state.security_context
    
    # Extract manually if not set by middleware
    credentials = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not credentials:
        raise APIValidationError("Authentication required", 401)
    
    return await security_manager.get_security_context(request, credentials)