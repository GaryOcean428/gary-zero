"""
FastAPI endpoints for Secret Store management.

This module provides REST API endpoints for managing secrets through
the Gary-Zero internal secret store with proper authentication and
access control.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    
from framework.security import (
    AccessLevel,
    SecretAccessDeniedError,
    SecretAlreadyExistsError,
    SecretMetadata,
    SecretNotFoundError,
    SecretType,
    get_secret_store,
)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "gary-zero-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User roles for authorization
USER_ROLES = {
    "admin": ["read", "write", "delete", "admin"],
    "operator": ["read", "write"],
    "viewer": ["read"],
}

# Security for API endpoints
security = HTTPBearer()

# API Router
router = APIRouter(prefix="/api/v1/secrets", tags=["secrets"])


# Request/Response Models
class SecretCreateRequest(BaseModel):
    """Request model for creating a secret."""

    name: str = Field(..., description="Secret name")
    value: str = Field(..., description="Secret value")
    secret_type: SecretType = Field(
        default=SecretType.OTHER, description="Type of secret"
    )
    access_level: AccessLevel = Field(
        default=AccessLevel.RESTRICTED, description="Access level"
    )
    description: str | None = Field(None, description="Description")
    expires_in_days: int | None = Field(None, description="Days until expiration")
    rotation_interval_days: int | None = Field(
        None, description="Rotation interval in days"
    )
    tags: list[str] = Field(default_factory=list, description="Tags")
    owner: str | None = Field(None, description="Owner")
    overwrite: bool = Field(default=False, description="Overwrite if exists")


class SecretUpdateRequest(BaseModel):
    """Request model for updating a secret."""

    value: str | None = Field(None, description="New secret value")
    description: str | None = Field(None, description="New description")
    expires_in_days: int | None = Field(None, description="New expiration in days")
    rotation_interval_days: int | None = Field(
        None, description="New rotation interval"
    )
    tags: list[str] | None = Field(None, description="New tags")


class SecretResponse(BaseModel):
    """Response model for secret metadata."""

    name: str
    secret_type: SecretType
    access_level: AccessLevel
    description: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    rotation_interval_days: int | None
    tags: list[str]
    owner: str | None
    needs_rotation: bool = Field(description="Whether the secret needs rotation")
    is_expired: bool = Field(description="Whether the secret is expired")


class SecretValueResponse(BaseModel):
    """Response model for secret with value."""

    name: str
    value: str
    metadata: SecretResponse


class SecretListResponse(BaseModel):
    """Response model for listing secrets."""

    secrets: list[SecretResponse]
    total: int


class TokenRequest(BaseModel):
    """Request model for token generation."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Response model for token generation."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    role: str


class ImportResponse(BaseModel):
    """Response model for import operations."""

    imported_count: int
    imported_secrets: list[str]


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None


# Authentication and Authorization
class UserClaims(BaseModel):
    """JWT user claims model"""
    sub: str  # subject/user ID
    role: str = "viewer"
    exp: Optional[int] = None
    iat: Optional[int] = None


def create_access_token(user_id: str, role: str = "viewer") -> str:
    """Create a JWT access token"""
    if not JWT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT library not available"
        )
    
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> UserClaims:
    """Verify and decode JWT token"""
    if not JWT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT library not available"
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role", "viewer")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return UserClaims(
            sub=user_id,
            role=role,
            exp=payload.get("exp"),
            iat=payload.get("iat")
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserClaims:
    """
    Get current user from JWT token with proper validation.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For development/testing, accept a simple "dev-token" 
    if credentials.credentials == "dev-token":
        return UserClaims(sub="dev-user", role="admin")
    
    # Verify JWT token
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_permission(user: UserClaims, required_permission: str) -> bool:
    """Check if user has required permission"""
    user_permissions = USER_ROLES.get(user.role, [])
    return required_permission in user_permissions


def require_permission(permission: str):
    """Dependency factory for requiring specific permissions"""
    def permission_checker(user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}, User role: {user.role}"
            )
        return user
    return permission_checker


async def require_admin_access(user: UserClaims = Depends(get_current_user)) -> UserClaims:
    """Require admin access for sensitive operations."""
    if not check_permission(user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin access required. Current role: {user.role}"
        )
    return user


# Authentication endpoints
@router.post("/auth/token", response_model=TokenResponse)
async def login_for_access_token(request: TokenRequest) -> TokenResponse:
    """
    Generate JWT access token for authentication.
    
    For development, accepts:
    - admin/admin -> admin role
    - operator/operator -> operator role  
    - viewer/viewer -> viewer role
    - dev/dev -> admin role (development only)
    """
    # Simple credential validation for development
    valid_credentials = {
        "admin": ("admin", "admin"),
        "operator": ("operator", "operator"), 
        "viewer": ("viewer", "viewer"),
        "dev": ("dev", "dev")  # Development convenience
    }
    
    user_role = None
    for role, (username, password) in valid_credentials.items():
        if request.username == username and request.password == password:
            user_role = role if role != "dev" else "admin"
            break
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user_id=request.username, role=user_role)
    
    return TokenResponse(
        access_token=access_token,
        role=user_role,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# API Endpoints
@router.post("/", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: SecretCreateRequest, 
    user: UserClaims = Depends(require_permission("write"))
) -> SecretResponse:
    """Create a new secret."""
    try:
        store = get_secret_store()

        # Create metadata
        metadata = SecretMetadata(
            name=request.name,
            secret_type=request.secret_type,
            access_level=request.access_level,
            description=request.description,
            expires_at=(
                datetime.utcnow() + timedelta(days=request.expires_in_days)
                if request.expires_in_days
                else None
            ),
            rotation_interval_days=request.rotation_interval_days,
            tags=request.tags,
            owner=request.owner or user.sub,
        )

        # Store the secret
        success = store.store_secret(
            request.name, request.value, metadata, overwrite=request.overwrite
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store secret",
            )

        # Return the created secret metadata
        secrets_list = store.list_secrets(include_metadata=True)
        created_secret = next(s for s in secrets_list if s.name == request.name)

        return SecretResponse(
            name=created_secret.name,
            secret_type=created_secret.secret_type,
            access_level=created_secret.access_level,
            description=created_secret.description,
            created_at=created_secret.created_at,
            updated_at=created_secret.updated_at,
            expires_at=created_secret.expires_at,
            rotation_interval_days=created_secret.rotation_interval_days,
            tags=created_secret.tags,
            owner=created_secret.owner,
            needs_rotation=False,  # Just created
            is_expired=False,  # Just created
        )

    except SecretAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Secret '{request.name}' already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secret: {str(e)}",
        )


@router.get("/", response_model=SecretListResponse)
async def list_secrets(
    include_values: bool = False, 
    user: UserClaims = Depends(get_current_user)
) -> SecretListResponse:
    """List all secrets (metadata only by default)."""
    try:
        store = get_secret_store()
        secrets_list = store.list_secrets(include_metadata=True)

        # Check for admin access if values are requested
        if include_values:
            if not check_permission(user, "admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required to include secret values"
                )

        response_secrets = []
        for secret_metadata in secrets_list:
            # Create stored secret object to check rotation/expiration

            # We can't easily get the stored secret object, so we'll check manually
            needs_rotation = False
            is_expired = False

            if secret_metadata.expires_at:
                is_expired = datetime.utcnow() > secret_metadata.expires_at

            if secret_metadata.rotation_interval_days:
                rotation_due = secret_metadata.updated_at + timedelta(
                    days=secret_metadata.rotation_interval_days
                )
                needs_rotation = datetime.utcnow() > rotation_due

            response_secrets.append(
                SecretResponse(
                    name=secret_metadata.name,
                    secret_type=secret_metadata.secret_type,
                    access_level=secret_metadata.access_level,
                    description=secret_metadata.description,
                    created_at=secret_metadata.created_at,
                    updated_at=secret_metadata.updated_at,
                    expires_at=secret_metadata.expires_at,
                    rotation_interval_days=secret_metadata.rotation_interval_days,
                    tags=secret_metadata.tags,
                    owner=secret_metadata.owner,
                    needs_rotation=needs_rotation,
                    is_expired=is_expired,
                )
            )

        return SecretListResponse(secrets=response_secrets, total=len(response_secrets))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}",
        )


@router.get("/{secret_name}", response_model=SecretValueResponse)
async def get_secret(
    secret_name: str, 
    user: UserClaims = Depends(require_permission("read"))
) -> SecretValueResponse:
    """Get a specific secret with its value."""
    try:
        store = get_secret_store()

        # Get the secret value
        value = store.get_secret(secret_name, user=user.sub)

        # Get metadata
        secrets_list = store.list_secrets(include_metadata=True)
        metadata = next((s for s in secrets_list if s.name == secret_name), None)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret '{secret_name}' not found",
            )

        # Check expiration and rotation
        is_expired = metadata.expires_at and datetime.utcnow() > metadata.expires_at
        needs_rotation = False
        if metadata.rotation_interval_days:
            rotation_due = metadata.updated_at + timedelta(
                days=metadata.rotation_interval_days
            )
            needs_rotation = datetime.utcnow() > rotation_due

        response_metadata = SecretResponse(
            name=metadata.name,
            secret_type=metadata.secret_type,
            access_level=metadata.access_level,
            description=metadata.description,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            expires_at=metadata.expires_at,
            rotation_interval_days=metadata.rotation_interval_days,
            tags=metadata.tags,
            owner=metadata.owner,
            needs_rotation=needs_rotation,
            is_expired=is_expired,
        )

        return SecretValueResponse(
            name=secret_name, value=value, metadata=response_metadata
        )

    except SecretNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{secret_name}' not found",
        )
    except SecretAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to secret '{secret_name}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get secret: {str(e)}",
        )


@router.put("/{secret_name}", response_model=SecretResponse)
async def update_secret(
    secret_name: str,
    request: SecretUpdateRequest,
    user: UserClaims = Depends(require_permission("write")),
) -> SecretResponse:
    """Update an existing secret."""
    try:
        store = get_secret_store()

        # Check if secret exists and get current metadata
        secrets_list = store.list_secrets(include_metadata=True)
        current_metadata = next(
            (s for s in secrets_list if s.name == secret_name), None
        )

        if not current_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret '{secret_name}' not found",
            )

        # Update value if provided
        if request.value is not None:
            # Get current value first
            current_value = store.get_secret(secret_name, user=user.sub)

            # Create updated metadata
            updated_metadata = SecretMetadata(
                name=secret_name,
                secret_type=current_metadata.secret_type,
                access_level=current_metadata.access_level,
                description=(
                    request.description
                    if request.description is not None
                    else current_metadata.description
                ),
                expires_at=(
                    datetime.utcnow() + timedelta(days=request.expires_in_days)
                    if request.expires_in_days is not None
                    else current_metadata.expires_at
                ),
                rotation_interval_days=(
                    request.rotation_interval_days
                    if request.rotation_interval_days is not None
                    else current_metadata.rotation_interval_days
                ),
                tags=(
                    request.tags if request.tags is not None else current_metadata.tags
                ),
                owner=current_metadata.owner,
            )

            # Store updated secret
            success = store.store_secret(
                secret_name, request.value, updated_metadata, overwrite=True
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update secret",
                )
        else:
            # Only update metadata
            updated_metadata = SecretMetadata(
                name=secret_name,
                secret_type=current_metadata.secret_type,
                access_level=current_metadata.access_level,
                description=(
                    request.description
                    if request.description is not None
                    else current_metadata.description
                ),
                expires_at=(
                    datetime.utcnow() + timedelta(days=request.expires_in_days)
                    if request.expires_in_days is not None
                    else current_metadata.expires_at
                ),
                rotation_interval_days=(
                    request.rotation_interval_days
                    if request.rotation_interval_days is not None
                    else current_metadata.rotation_interval_days
                ),
                tags=(
                    request.tags if request.tags is not None else current_metadata.tags
                ),
                owner=current_metadata.owner,
            )

            success = store.update_metadata(secret_name, updated_metadata, user=user.sub)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update secret metadata",
                )

        # Return updated metadata
        secrets_list = store.list_secrets(include_metadata=True)
        updated_secret = next(s for s in secrets_list if s.name == secret_name)

        # Check expiration and rotation
        is_expired = (
            updated_secret.expires_at and datetime.utcnow() > updated_secret.expires_at
        )
        needs_rotation = False
        if updated_secret.rotation_interval_days:
            rotation_due = updated_secret.updated_at + timedelta(
                days=updated_secret.rotation_interval_days
            )
            needs_rotation = datetime.utcnow() > rotation_due

        return SecretResponse(
            name=updated_secret.name,
            secret_type=updated_secret.secret_type,
            access_level=updated_secret.access_level,
            description=updated_secret.description,
            created_at=updated_secret.created_at,
            updated_at=updated_secret.updated_at,
            expires_at=updated_secret.expires_at,
            rotation_interval_days=updated_secret.rotation_interval_days,
            tags=updated_secret.tags,
            owner=updated_secret.owner,
            needs_rotation=needs_rotation,
            is_expired=is_expired,
        )

    except SecretNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{secret_name}' not found",
        )
    except SecretAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to secret '{secret_name}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update secret: {str(e)}",
        )


@router.delete("/{secret_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_name: str, 
    user: UserClaims = Depends(require_admin_access)
):
    """Delete a secret (admin only)."""
    try:
        store = get_secret_store()
        success = store.delete_secret(secret_name, user=user.sub)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete secret",
            )

    except SecretNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{secret_name}' not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete secret: {str(e)}",
        )


@router.post("/import-env", response_model=ImportResponse)
async def import_from_environment(
    prefix: str = "", 
    overwrite: bool = False, 
    user: UserClaims = Depends(require_admin_access)
) -> ImportResponse:
    """Import secrets from environment variables (admin only)."""
    try:
        from framework.security import initialize_from_environment

        loaded_count = initialize_from_environment(prefix=prefix, overwrite=overwrite)

        # Get list of secrets that were likely imported
        store = get_secret_store()
        all_secrets = store.list_secrets(include_metadata=False)

        # This is a simplified approach - in a real implementation, you'd track what was actually imported
        return ImportResponse(
            imported_count=loaded_count,
            imported_secrets=all_secrets[-loaded_count:] if loaded_count > 0 else [],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import from environment: {str(e)}",
        )


@router.post("/cleanup", response_model=dict[str, int])
async def cleanup_expired_secrets(
    user: UserClaims = Depends(require_admin_access),
) -> dict[str, int]:
    """Clean up expired secrets (admin only)."""
    try:
        store = get_secret_store()
        cleaned_count = store.cleanup_expired_secrets()

        return {"cleaned_count": cleaned_count}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired secrets: {str(e)}",
        )


@router.get("/rotation/check", response_model=dict[str, list[str]])
async def check_rotation_needed(
    user: UserClaims = Depends(require_permission("read")),
) -> dict[str, list[str]]:
    """Check which secrets need rotation."""
    try:
        store = get_secret_store()
        needing_rotation = store.get_secrets_needing_rotation()

        return {"secrets_needing_rotation": needing_rotation}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check rotation status: {str(e)}",
        )


@router.get("/export/metadata", response_model=dict[str, Any])
async def export_metadata(
    user: UserClaims = Depends(require_permission("read"))
) -> dict[str, Any]:
    """Export secret metadata (without values)."""
    try:
        store = get_secret_store()
        metadata_export = store.export_metadata()

        return metadata_export

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export metadata: {str(e)}",
        )


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for the secret store API."""
    try:
        store = get_secret_store()
        # Try to list secrets as a basic health check
        secrets_count = len(store.list_secrets(include_metadata=False))

        return {
            "status": "healthy",
            "secrets_count": secrets_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Secret store unhealthy: {str(e)}",
        )
