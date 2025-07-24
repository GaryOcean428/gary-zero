"""
FastAPI endpoints for Secret Store management.

This module provides REST API endpoints for managing secrets through
the Gary-Zero internal secret store with proper authentication and
access control.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from framework.security import (
    AccessLevel,
    SecretAccessDeniedError,
    SecretAlreadyExistsError,
    SecretMetadata,
    SecretNotFoundError,
    SecretType,
    get_secret_store,
)

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


class ImportResponse(BaseModel):
    """Response model for import operations."""

    imported_count: int
    imported_secrets: list[str]


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None


# Authentication and Authorization
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Get current user from JWT token.

    For this demo, we'll use a simple token validation.
    In production, implement proper JWT validation.
    """
    # TODO: Implement proper JWT validation
    # For now, accept any token and return a generic user
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return "api_user"  # In production, extract from JWT


async def require_admin_access(user: str = Depends(get_current_user)) -> str:
    """Require admin access for sensitive operations."""
    # TODO: Implement proper role checking
    # For now, allow all authenticated users
    return user


# API Endpoints
@router.post("/", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: SecretCreateRequest, user: str = Depends(get_current_user)
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
            expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days)
            if request.expires_in_days
            else None,
            rotation_interval_days=request.rotation_interval_days,
            tags=request.tags,
            owner=request.owner or user,
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
    include_values: bool = False, user: str = Depends(get_current_user)
) -> SecretListResponse:
    """List all secrets (metadata only by default)."""
    try:
        store = get_secret_store()
        secrets_list = store.list_secrets(include_metadata=True)

        # Check for admin access if values are requested
        if include_values:
            # This should require admin access
            await require_admin_access(user)

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
    secret_name: str, user: str = Depends(get_current_user)
) -> SecretValueResponse:
    """Get a specific secret with its value."""
    try:
        store = get_secret_store()

        # Get the secret value
        value = store.get_secret(secret_name, user=user)

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
    user: str = Depends(get_current_user),
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
            current_value = store.get_secret(secret_name, user=user)

            # Create updated metadata
            updated_metadata = SecretMetadata(
                name=secret_name,
                secret_type=current_metadata.secret_type,
                access_level=current_metadata.access_level,
                description=request.description
                if request.description is not None
                else current_metadata.description,
                expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days)
                if request.expires_in_days is not None
                else current_metadata.expires_at,
                rotation_interval_days=request.rotation_interval_days
                if request.rotation_interval_days is not None
                else current_metadata.rotation_interval_days,
                tags=request.tags
                if request.tags is not None
                else current_metadata.tags,
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
                description=request.description
                if request.description is not None
                else current_metadata.description,
                expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days)
                if request.expires_in_days is not None
                else current_metadata.expires_at,
                rotation_interval_days=request.rotation_interval_days
                if request.rotation_interval_days is not None
                else current_metadata.rotation_interval_days,
                tags=request.tags
                if request.tags is not None
                else current_metadata.tags,
                owner=current_metadata.owner,
            )

            success = store.update_metadata(secret_name, updated_metadata, user=user)
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
async def delete_secret(secret_name: str, user: str = Depends(require_admin_access)):
    """Delete a secret (admin only)."""
    try:
        store = get_secret_store()
        success = store.delete_secret(secret_name, user=user)

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
    prefix: str = "", overwrite: bool = False, user: str = Depends(require_admin_access)
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
    user: str = Depends(require_admin_access),
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
    user: str = Depends(get_current_user),
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
async def export_metadata(user: str = Depends(get_current_user)) -> dict[str, Any]:
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
