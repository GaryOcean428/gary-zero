"""
OAuth 2.0 Integration for Gary-Zero
Implementing secure authentication with multiple providers
"""

from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import logging
import secrets
import hashlib
import time
from dataclasses import dataclass
from urllib.parse import urlencode, parse_qs, urlparse
import json
import base64

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers"""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    DISCORD = "discord"


class OAuthScope(str, Enum):
    """Common OAuth scopes"""
    EMAIL = "email"
    PROFILE = "profile"
    OPENID = "openid"
    READ_USER = "read:user"
    REPO = "repo"
    USER_EMAIL = "user:email"


@dataclass
class OAuthConfig:
    """OAuth provider configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    authorization_url: str
    token_url: str
    user_info_url: str
    enabled: bool = True


class OAuthState(BaseModel):
    """OAuth state for security"""
    state: str
    nonce: Optional[str] = None
    redirect_after: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    expires_at: float = Field(default_factory=lambda: time.time() + 600)  # 10 minutes
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def is_valid(self, provided_state: str) -> bool:
        return not self.is_expired() and self.state == provided_state


class OAuthUser(BaseModel):
    """OAuth user information"""
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    provider: OAuthProvider
    provider_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    last_login: float = Field(default_factory=time.time)


class OAuthToken(BaseModel):
    """OAuth token information"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    expires_at: Optional[float] = None
    scope: Optional[str] = None
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return time.time() > (self.expires_at - 300)  # 5 minute buffer
        return False


class OAuthIntegrationManager:
    """
    OAuth 2.0 integration manager for Gary-Zero
    Supports multiple providers with secure token handling
    """
    
    def __init__(self):
        self.providers: Dict[OAuthProvider, OAuthConfig] = {}
        self.active_states: Dict[str, OAuthState] = {}
        self.user_sessions: Dict[str, OAuthUser] = {}
        self.logger = logging.getLogger(__name__)
        
        # Default provider configurations
        self._setup_default_providers()
    
    def _setup_default_providers(self):
        """Setup default OAuth provider configurations"""
        
        # Google OAuth 2.0
        self.providers[OAuthProvider.GOOGLE] = OAuthConfig(
            client_id="",  # To be configured
            client_secret="",  # To be configured
            redirect_uri="",  # To be configured
            scopes=["openid", "email", "profile"],
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
            enabled=False
        )
        
        # GitHub OAuth
        self.providers[OAuthProvider.GITHUB] = OAuthConfig(
            client_id="",  # To be configured
            client_secret="",  # To be configured
            redirect_uri="",  # To be configured
            scopes=["user:email", "read:user"],
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            enabled=False
        )
        
        # Microsoft OAuth 2.0
        self.providers[OAuthProvider.MICROSOFT] = OAuthConfig(
            client_id="",  # To be configured
            client_secret="",  # To be configured
            redirect_uri="",  # To be configured
            scopes=["openid", "email", "profile"],
            authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            user_info_url="https://graph.microsoft.com/v1.0/me",
            enabled=False
        )
    
    def configure_provider(self, provider: OAuthProvider, 
                          client_id: str, client_secret: str, 
                          redirect_uri: str, enabled: bool = True):
        """Configure an OAuth provider"""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        config = self.providers[provider]
        config.client_id = client_id
        config.client_secret = client_secret
        config.redirect_uri = redirect_uri
        config.enabled = enabled
        
        self.logger.info(f"Configured OAuth provider: {provider}")
    
    def generate_state(self, redirect_after: Optional[str] = None) -> OAuthState:
        """Generate secure state for OAuth flow"""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(16)
        
        oauth_state = OAuthState(
            state=state,
            nonce=nonce,
            redirect_after=redirect_after
        )
        
        self.active_states[state] = oauth_state
        return oauth_state
    
    def get_authorization_url(self, provider: OAuthProvider, 
                            redirect_after: Optional[str] = None) -> str:
        """Generate OAuth authorization URL"""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        config = self.providers[provider]
        if not config.enabled:
            raise ValueError(f"Provider {provider} is not enabled")
        
        if not config.client_id:
            raise ValueError(f"Provider {provider} is not configured")
        
        # Generate secure state
        oauth_state = self.generate_state(redirect_after)
        
        # Build authorization parameters
        params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": " ".join(config.scopes),
            "state": oauth_state.state,
            "access_type": "offline",  # For refresh tokens
        }
        
        # Add provider-specific parameters
        if provider == OAuthProvider.GOOGLE:
            params["prompt"] = "consent"
        elif provider == OAuthProvider.MICROSOFT:
            params["response_mode"] = "query"
        
        # Build URL
        auth_url = f"{config.authorization_url}?{urlencode(params)}"
        
        self.logger.info(f"Generated authorization URL for {provider}")
        return auth_url
    
    async def exchange_code_for_token(self, provider: OAuthProvider, 
                                    code: str, state: str) -> OAuthToken:
        """Exchange authorization code for access token"""
        # Validate state
        if state not in self.active_states:
            raise ValueError("Invalid or expired state")
        
        oauth_state = self.active_states[state]
        if not oauth_state.is_valid(state):
            raise ValueError("Invalid or expired state")
        
        config = self.providers[provider]
        
        # Prepare token request
        token_data = {
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": config.redirect_uri,
        }
        
        # Simulate token exchange (in real implementation, use HTTP client)
        self.logger.info(f"Exchanging code for token with {provider}")
        
        # Cleanup state
        del self.active_states[state]
        
        # Return mock token for now
        return OAuthToken(
            access_token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
            expires_in=3600,
            expires_at=time.time() + 3600,
            scope=" ".join(config.scopes)
        )
    
    async def get_user_info(self, provider: OAuthProvider, 
                          token: OAuthToken) -> OAuthUser:
        """Get user information from OAuth provider"""
        config = self.providers[provider]
        
        # Simulate user info retrieval
        self.logger.info(f"Retrieving user info from {provider}")
        
        # Mock user data based on provider
        if provider == OAuthProvider.GOOGLE:
            user_data = {
                "id": "google_123456",
                "email": "user@gmail.com",
                "name": "John Doe",
                "picture": "https://example.com/avatar.jpg"
            }
        elif provider == OAuthProvider.GITHUB:
            user_data = {
                "id": "github_789012",
                "login": "johndoe",
                "email": "user@example.com",
                "name": "John Doe",
                "avatar_url": "https://github.com/avatar.jpg"
            }
        else:
            user_data = {
                "id": f"{provider}_456789",
                "email": "user@example.com",
                "name": "John Doe"
            }
        
        return OAuthUser(
            id=f"{provider}_{user_data['id']}",
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            avatar_url=user_data.get("picture") or user_data.get("avatar_url"),
            provider=provider,
            provider_data=user_data
        )
    
    async def refresh_token(self, provider: OAuthProvider, 
                          refresh_token: str) -> OAuthToken:
        """Refresh an expired access token"""
        config = self.providers[provider]
        
        # Simulate token refresh
        self.logger.info(f"Refreshing token for {provider}")
        
        return OAuthToken(
            access_token=secrets.token_urlsafe(32),
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=3600,
            expires_at=time.time() + 3600
        )
    
    def create_session(self, user: OAuthUser, session_id: Optional[str] = None) -> str:
        """Create user session"""
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        
        user.last_login = time.time()
        self.user_sessions[session_id] = user
        
        self.logger.info(f"Created session for user {user.email}")
        return session_id
    
    def get_session_user(self, session_id: str) -> Optional[OAuthUser]:
        """Get user from session ID"""
        return self.user_sessions.get(session_id)
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke user session"""
        if session_id in self.user_sessions:
            user = self.user_sessions[session_id]
            del self.user_sessions[session_id]
            self.logger.info(f"Revoked session for user {user.email}")
            return True
        return False
    
    def cleanup_expired_states(self):
        """Clean up expired OAuth states"""
        now = time.time()
        expired_states = [
            state for state, oauth_state in self.active_states.items()
            if oauth_state.is_expired()
        ]
        
        for state in expired_states:
            del self.active_states[state]
        
        if expired_states:
            self.logger.info(f"Cleaned up {len(expired_states)} expired states")
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all OAuth providers"""
        status = {}
        
        for provider, config in self.providers.items():
            status[provider.value] = {
                "enabled": config.enabled,
                "configured": bool(config.client_id and config.client_secret),
                "scopes": config.scopes,
                "redirect_uri": config.redirect_uri
            }
        
        return status


# Security utilities
class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://accounts.google.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https://api.github.com https://www.googleapis.com; "
                "frame-src https://accounts.google.com"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            )
        }


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password with salt"""
    if not salt:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 with SHA-256
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 100k iterations
    )
    
    return base64.b64encode(password_hash).decode('utf-8'), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == password_hash


# Factory function
def create_oauth_manager() -> OAuthIntegrationManager:
    """Create OAuth integration manager"""
    return OAuthIntegrationManager()


# Example configurations for development
EXAMPLE_OAUTH_CONFIG = {
    "google": {
        "client_id": "your-google-client-id.apps.googleusercontent.com",
        "client_secret": "your-google-client-secret",
        "redirect_uri": "http://localhost:8000/auth/google/callback"
    },
    "github": {
        "client_id": "your-github-client-id",
        "client_secret": "your-github-client-secret", 
        "redirect_uri": "http://localhost:8000/auth/github/callback"
    },
    "microsoft": {
        "client_id": "your-microsoft-client-id",
        "client_secret": "your-microsoft-client-secret",
        "redirect_uri": "http://localhost:8000/auth/microsoft/callback"
    }
}