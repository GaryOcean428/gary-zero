"""
Internal Secret Store for Secure Credential Management.

This module provides a secure, internal secret store for Gary-Zero that holds
API keys, passwords and other sensitive information needed for daily tasks.
It prevents hard-coded secrets and allows agents to access credentials without
exposing them in the repository or environment variables.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, SecretStr, validator

from .audit_logger import AuditEvent, AuditEventType, AuditLevel, AuditLogger

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Types of secrets that can be stored."""

    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    DATABASE_URL = "database_url"
    WEBHOOK_URL = "webhook_url"
    OTHER = "other"


class AccessLevel(str, Enum):
    """Access levels for secrets."""

    PUBLIC = "public"  # Can be read by any component
    RESTRICTED = "restricted"  # Requires specific permissions
    ADMIN = "admin"  # Admin-only access


class SecretMetadata(BaseModel):
    """Metadata for a stored secret."""

    name: str = Field(..., description="Unique name for the secret")
    secret_type: SecretType = Field(
        default=SecretType.OTHER, description="Type of secret"
    )
    access_level: AccessLevel = Field(
        default=AccessLevel.RESTRICTED, description="Access level"
    )
    description: str | None = Field(None, description="Description of the secret")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    rotation_interval_days: int | None = Field(
        None, description="Auto-rotation interval in days"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for organization")
    owner: str | None = Field(None, description="Owner of the secret")

    @validator("name")
    def validate_name(cls, v):
        """Validate secret name format."""
        if not v or not v.strip():
            raise ValueError("Secret name cannot be empty")
        if len(v) > 100:
            raise ValueError("Secret name cannot exceed 100 characters")
        # Allow alphanumeric, underscore, hyphen, and dot
        if not all(c.isalnum() or c in "_-./" for c in v):
            raise ValueError(
                "Secret name can only contain alphanumeric characters, underscore, hyphen, and dot"
            )
        return v.strip()


class StoredSecret(BaseModel):
    """A secret with its metadata."""

    metadata: SecretMetadata
    encrypted_value: bytes = Field(..., description="Encrypted secret value")

    def is_expired(self) -> bool:
        """Check if the secret is expired."""
        if not self.metadata.expires_at:
            return False
        return datetime.utcnow() > self.metadata.expires_at

    def needs_rotation(self) -> bool:
        """Check if the secret needs rotation."""
        if not self.metadata.rotation_interval_days:
            return False
        rotation_due = self.metadata.updated_at + timedelta(
            days=self.metadata.rotation_interval_days
        )
        return datetime.utcnow() > rotation_due


class SecretStoreConfig(BaseModel):
    """Configuration for the secret store."""

    store_path: Path = Field(
        default=Path("secrets/store.encrypted"), description="Path to store file"
    )
    encryption_key: bytes | None = Field(
        None, description="Encryption key (auto-generated if not provided)"
    )
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_retention_days: int = Field(
        default=30, description="Backup retention period"
    )
    max_secrets: int = Field(default=1000, description="Maximum number of secrets")


class SecretStoreError(Exception):
    """Base exception for secret store operations."""

    pass


class SecretNotFoundError(SecretStoreError):
    """Raised when a secret is not found."""

    pass


class SecretAccessDeniedError(SecretStoreError):
    """Raised when access to a secret is denied."""

    pass


class SecretAlreadyExistsError(SecretStoreError):
    """Raised when trying to create a secret that already exists."""

    pass


class InternalSecretStore:
    """
    Internal secret store with encryption at rest and access control.

    Provides secure storage for API keys, passwords, and other sensitive
    information with encryption, access control, and audit logging.
    """

    def __init__(self, config: SecretStoreConfig | None = None):
        """
        Initialize the secret store.

        Args:
            config: Configuration for the secret store
        """
        self.config = config or SecretStoreConfig()
        self._lock = threading.RLock()
        self._secrets: dict[str, StoredSecret] = {}
        self._fernet: Fernet | None = None

        # Initialize audit logger if enabled
        self.audit_logger = AuditLogger() if self.config.enable_audit_logging else None

        # Initialize encryption and load existing secrets
        self._initialize_encryption()
        self._load_secrets()

        logger.info(f"Secret store initialized with {len(self._secrets)} secrets")

    def _initialize_encryption(self):
        """Initialize encryption key and Fernet instance."""
        # Get or generate encryption key
        if self.config.encryption_key:
            key = self.config.encryption_key
        else:
            # Try to load from environment or generate new
            key_env = os.getenv("SECRET_STORE_KEY")
            if key_env:
                try:
                    # Try to decode as base64 first
                    import base64

                    key = base64.urlsafe_b64decode(key_env)
                    if len(key) != 32:
                        raise ValueError("Key must be 32 bytes")
                except Exception:
                    # If that fails, generate a key from the string using a hash
                    import hashlib

                    key = hashlib.sha256(key_env.encode()).digest()
                    # Convert to base64 for Fernet
                    import base64

                    key = base64.urlsafe_b64encode(key)
            else:
                key = Fernet.generate_key()
                logger.warning(
                    "Generated new encryption key. Store SECRET_STORE_KEY environment variable to persist."
                )

        self._fernet = Fernet(key)

    def _load_secrets(self):
        """Load secrets from the store file."""
        if not self.config.store_path.exists():
            logger.info("No existing secret store found, starting with empty store")
            return

        try:
            with open(self.config.store_path, "rb") as f:
                encrypted_data = f.read()

            # Decrypt the store data
            decrypted_data = self._fernet.decrypt(encrypted_data)
            store_data = json.loads(decrypted_data.decode())

            # Load secrets
            for name, secret_data in store_data.get("secrets", {}).items():
                metadata_dict = secret_data["metadata"]

                # Handle datetime deserialization
                for key, value in metadata_dict.items():
                    if key in ["created_at", "updated_at", "expires_at"] and isinstance(
                        value, str
                    ):
                        try:
                            metadata_dict[key] = datetime.fromisoformat(value)
                        except ValueError:
                            # If parsing fails, use current time for created_at/updated_at, None for expires_at
                            if key in ["created_at", "updated_at"]:
                                metadata_dict[key] = datetime.utcnow()
                            else:
                                metadata_dict[key] = None

                metadata = SecretMetadata.parse_obj(metadata_dict)
                encrypted_value = secret_data["encrypted_value"].encode()
                self._secrets[name] = StoredSecret(
                    metadata=metadata, encrypted_value=encrypted_value
                )

            logger.info(f"Loaded {len(self._secrets)} secrets from store")

        except Exception as e:
            logger.error(f"Failed to load secret store: {e}")
            # Continue with empty store rather than failing
            self._secrets = {}

    def _save_secrets(self):
        """Save secrets to the store file."""
        try:
            # Ensure directory exists
            self.config.store_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for storage
            store_data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "secrets": {},
            }

            for name, secret in self._secrets.items():
                # Convert metadata to dict and handle datetime serialization
                metadata_dict = secret.metadata.dict()
                for key, value in metadata_dict.items():
                    if isinstance(value, datetime):
                        metadata_dict[key] = value.isoformat()

                store_data["secrets"][name] = {
                    "metadata": metadata_dict,
                    "encrypted_value": secret.encrypted_value.decode(),
                }

            # Encrypt and save
            data_bytes = json.dumps(store_data).encode()
            encrypted_data = self._fernet.encrypt(data_bytes)

            # Atomic write
            temp_path = self.config.store_path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                f.write(encrypted_data)
            temp_path.replace(self.config.store_path)

            logger.debug(f"Saved {len(self._secrets)} secrets to store")

        except Exception as e:
            logger.error(f"Failed to save secret store: {e}")
            raise SecretStoreError(f"Failed to save secrets: {e}")

    def _log_access(
        self,
        operation: str,
        secret_name: str,
        success: bool = True,
        details: str | None = None,
        user: str | None = None,
    ):
        """Log secret access for audit purposes."""
        if not self.audit_logger:
            return

        event_type = (
            AuditEventType.SYSTEM_EVENT
            if success
            else AuditEventType.SECURITY_VIOLATION
        )
        level = AuditLevel.INFO if success else AuditLevel.WARNING

        message = f"Secret store {operation}: {secret_name}"
        if details:
            message += f" - {details}"

        event = AuditEvent(
            event_type=event_type,
            level=level,
            message=message,
            timestamp=time.time(),
            user_id=user,
            tool_name="secret_store",
            metadata={
                "operation": operation,
                "secret_name": secret_name,
                "success": success,
            },
        )

        self.audit_logger.log_event(event)

    def store_secret(
        self,
        name: str,
        value: str | SecretStr,
        metadata: SecretMetadata | None = None,
        overwrite: bool = False,
    ) -> bool:
        """
        Store a secret with encryption.

        Args:
            name: Name of the secret
            value: Secret value to store
            metadata: Optional metadata for the secret
            overwrite: Whether to overwrite existing secret

        Returns:
            True if stored successfully

        Raises:
            SecretAlreadyExistsError: If secret exists and overwrite=False
            SecretStoreError: If storage fails
        """
        with self._lock:
            # Check if secret already exists
            if name in self._secrets and not overwrite:
                self._log_access("store", name, False, "Secret already exists")
                raise SecretAlreadyExistsError(f"Secret '{name}' already exists")

            # Check store limits
            if (
                len(self._secrets) >= self.config.max_secrets
                and name not in self._secrets
            ):
                raise SecretStoreError(
                    f"Maximum number of secrets ({self.config.max_secrets}) reached"
                )

            try:
                # Extract string value from SecretStr if needed
                secret_value = (
                    value.get_secret_value()
                    if isinstance(value, SecretStr)
                    else str(value)
                )

                # Encrypt the secret value
                encrypted_value = self._fernet.encrypt(secret_value.encode())

                # Create or update metadata
                if metadata is None:
                    metadata = SecretMetadata(name=name)
                else:
                    metadata.name = name
                    metadata.updated_at = datetime.utcnow()

                # Store the secret
                self._secrets[name] = StoredSecret(
                    metadata=metadata, encrypted_value=encrypted_value
                )

                # Save to disk
                self._save_secrets()

                operation = "update" if name in self._secrets else "create"
                self._log_access(
                    operation, name, True, f"Secret {operation}d successfully"
                )

                logger.info(f"Secret '{name}' stored successfully")
                return True

            except Exception as e:
                self._log_access("store", name, False, f"Storage failed: {e}")
                logger.error(f"Failed to store secret '{name}': {e}")
                raise SecretStoreError(f"Failed to store secret: {e}")

    def get_secret(
        self,
        name: str,
        access_level: AccessLevel | None = None,
        user: str | None = None,
    ) -> str:
        """
        Retrieve a secret value.

        Args:
            name: Name of the secret
            access_level: Required access level for the operation
            user: User requesting the secret

        Returns:
            Decrypted secret value

        Raises:
            SecretNotFoundError: If secret doesn't exist
            SecretAccessDeniedError: If access is denied
            SecretStoreError: If retrieval fails
        """
        with self._lock:
            if name not in self._secrets:
                self._log_access("get", name, False, "Secret not found", user)
                raise SecretNotFoundError(f"Secret '{name}' not found")

            secret = self._secrets[name]

            # Check if secret is expired
            if secret.is_expired():
                self._log_access("get", name, False, "Secret expired", user)
                raise SecretStoreError(f"Secret '{name}' has expired")

            # Check access level (simplified for now)
            if (
                access_level
                and secret.metadata.access_level == AccessLevel.ADMIN
                and access_level != AccessLevel.ADMIN
            ):
                self._log_access("get", name, False, "Insufficient access level", user)
                raise SecretAccessDeniedError(
                    f"Insufficient access level for secret '{name}'"
                )

            try:
                # Decrypt the secret value
                decrypted_value = self._fernet.decrypt(secret.encrypted_value).decode()

                self._log_access(
                    "get", name, True, "Secret retrieved successfully", user
                )
                return decrypted_value

            except Exception as e:
                self._log_access("get", name, False, f"Decryption failed: {e}", user)
                logger.error(f"Failed to decrypt secret '{name}': {e}")
                raise SecretStoreError(f"Failed to retrieve secret: {e}")

    def delete_secret(self, name: str, user: str | None = None) -> bool:
        """
        Delete a secret.

        Args:
            name: Name of the secret to delete
            user: User requesting the deletion

        Returns:
            True if deleted successfully

        Raises:
            SecretNotFoundError: If secret doesn't exist
        """
        with self._lock:
            if name not in self._secrets:
                self._log_access("delete", name, False, "Secret not found", user)
                raise SecretNotFoundError(f"Secret '{name}' not found")

            try:
                del self._secrets[name]
                self._save_secrets()

                self._log_access(
                    "delete", name, True, "Secret deleted successfully", user
                )
                logger.info(f"Secret '{name}' deleted successfully")
                return True

            except Exception as e:
                self._log_access("delete", name, False, f"Deletion failed: {e}", user)
                logger.error(f"Failed to delete secret '{name}': {e}")
                raise SecretStoreError(f"Failed to delete secret: {e}")

    def list_secrets(
        self, include_metadata: bool = True, user: str | None = None
    ) -> list[str] | list[SecretMetadata]:
        """
        List all available secrets.

        Args:
            include_metadata: Whether to include metadata or just names
            user: User requesting the list

        Returns:
            List of secret names or metadata objects
        """
        with self._lock:
            self._log_access(
                "list", "all", True, f"Listed {len(self._secrets)} secrets", user
            )

            if include_metadata:
                return [secret.metadata for secret in self._secrets.values()]
            else:
                return list(self._secrets.keys())

    def update_metadata(
        self, name: str, metadata: SecretMetadata, user: str | None = None
    ) -> bool:
        """
        Update metadata for an existing secret.

        Args:
            name: Name of the secret
            metadata: New metadata
            user: User requesting the update

        Returns:
            True if updated successfully

        Raises:
            SecretNotFoundError: If secret doesn't exist
        """
        with self._lock:
            if name not in self._secrets:
                self._log_access(
                    "update_metadata", name, False, "Secret not found", user
                )
                raise SecretNotFoundError(f"Secret '{name}' not found")

            try:
                metadata.name = name  # Ensure name consistency
                metadata.updated_at = datetime.utcnow()

                # Keep the encrypted value, update metadata
                self._secrets[name].metadata = metadata
                self._save_secrets()

                self._log_access(
                    "update_metadata", name, True, "Metadata updated successfully", user
                )
                logger.info(f"Metadata for secret '{name}' updated successfully")
                return True

            except Exception as e:
                self._log_access(
                    "update_metadata", name, False, f"Update failed: {e}", user
                )
                logger.error(f"Failed to update metadata for secret '{name}': {e}")
                raise SecretStoreError(f"Failed to update metadata: {e}")

    def load_from_environment(
        self,
        env_mappings: dict[str, str] | None = None,
        prefix: str = "",
        overwrite: bool = False,
    ) -> int:
        """
        Load secrets from environment variables.

        Args:
            env_mappings: Optional mapping of env var names to secret names
            prefix: Optional prefix to filter environment variables
            overwrite: Whether to overwrite existing secrets

        Returns:
            Number of secrets loaded
        """
        loaded_count = 0

        # Default mappings for common API keys
        default_mappings = {
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GOOGLE_API_KEY": "google_api_key",
            "GEMINI_API_KEY": "gemini_api_key",
            "GROQ_API_KEY": "groq_api_key",
            "PERPLEXITY_API_KEY": "perplexity_api_key",
            "XAI_API_KEY": "xai_api_key",
            "HUGGINGFACE_TOKEN": "huggingface_token",
            "E2B_API_KEY": "e2b_api_key",
            "TOOLHOUSE_API_KEY": "toolhouse_api_key",
            "JWT_SECRET": "jwt_secret",
            "SESSION_SECRET": "session_secret",
            "ENCRYPTION_KEY": "encryption_key",
            "DATABASE_URL": "database_url",
            "SUPABASE_URL": "supabase_url",
            "SUPABASE_ANON_KEY": "supabase_anon_key",
            "SUPABASE_SERVICE_ROLE_KEY": "supabase_service_role_key",
        }

        mappings = env_mappings or default_mappings

        with self._lock:
            for env_var, secret_name in mappings.items():
                # Apply prefix filter if specified
                if prefix and not env_var.startswith(prefix):
                    continue

                value = os.getenv(env_var)
                if value:
                    try:
                        # Determine secret type based on name
                        secret_type = SecretType.API_KEY
                        if "password" in secret_name.lower():
                            secret_type = SecretType.PASSWORD
                        elif "token" in secret_name.lower():
                            secret_type = SecretType.TOKEN
                        elif "url" in secret_name.lower():
                            secret_type = (
                                SecretType.DATABASE_URL
                                if "database" in secret_name.lower()
                                else SecretType.WEBHOOK_URL
                            )
                        elif "secret" in secret_name.lower():
                            secret_type = SecretType.OTHER

                        metadata = SecretMetadata(
                            name=secret_name,
                            secret_type=secret_type,
                            description=f"Loaded from environment variable {env_var}",
                            tags=["environment", "auto-loaded"],
                        )

                        if self.store_secret(
                            secret_name, value, metadata, overwrite=overwrite
                        ):
                            loaded_count += 1
                            logger.info(
                                f"Loaded secret '{secret_name}' from environment variable '{env_var}'"
                            )

                    except SecretAlreadyExistsError:
                        if not overwrite:
                            logger.debug(
                                f"Secret '{secret_name}' already exists, skipping"
                            )
                    except Exception as e:
                        logger.error(f"Failed to load secret from '{env_var}': {e}")

        logger.info(f"Loaded {loaded_count} secrets from environment variables")
        return loaded_count

    def cleanup_expired_secrets(self) -> int:
        """
        Remove expired secrets.

        Returns:
            Number of secrets cleaned up
        """
        cleaned_count = 0

        with self._lock:
            expired_secrets = [
                name for name, secret in self._secrets.items() if secret.is_expired()
            ]

            for name in expired_secrets:
                try:
                    self.delete_secret(name, user="system")
                    cleaned_count += 1
                    logger.info(f"Cleaned up expired secret '{name}'")
                except Exception as e:
                    logger.error(f"Failed to cleanup expired secret '{name}': {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired secrets")

        return cleaned_count

    def get_secrets_needing_rotation(self) -> list[str]:
        """
        Get list of secrets that need rotation.

        Returns:
            List of secret names needing rotation
        """
        with self._lock:
            return [
                name
                for name, secret in self._secrets.items()
                if secret.needs_rotation()
            ]

    def export_metadata(self) -> dict[str, Any]:
        """
        Export store metadata (without secret values).

        Returns:
            Dictionary containing store metadata
        """
        with self._lock:
            return {
                "total_secrets": len(self._secrets),
                "secrets": {
                    name: secret.metadata.dict()
                    for name, secret in self._secrets.items()
                },
                "store_path": str(self.config.store_path),
                "export_timestamp": datetime.utcnow().isoformat(),
            }


# Global secret store instance
_secret_store: InternalSecretStore | None = None
_store_lock = threading.Lock()


def get_secret_store(config: SecretStoreConfig | None = None) -> InternalSecretStore:
    """
    Get the global secret store instance.

    Args:
        config: Configuration for the secret store (only used on first call)

    Returns:
        Global secret store instance
    """
    global _secret_store

    with _store_lock:
        if _secret_store is None:
            _secret_store = InternalSecretStore(config)
        return _secret_store


def get_secret(
    name: str, default: str | None = None, access_level: AccessLevel | None = None
) -> str | None:
    """
    Helper function to get a secret value.

    Args:
        name: Name of the secret
        default: Default value if secret not found
        access_level: Required access level

    Returns:
        Secret value or default
    """
    try:
        store = get_secret_store()
        return store.get_secret(name, access_level)
    except (SecretNotFoundError, SecretAccessDeniedError):
        return default
    except Exception as e:
        logger.warning(f"Failed to retrieve secret '{name}': {e}")
        return default


def store_secret(
    name: str,
    value: str | SecretStr,
    metadata: SecretMetadata | None = None,
    overwrite: bool = False,
) -> bool:
    """
    Helper function to store a secret.

    Args:
        name: Name of the secret
        value: Secret value
        metadata: Optional metadata
        overwrite: Whether to overwrite existing secret

    Returns:
        True if stored successfully
    """
    try:
        store = get_secret_store()
        return store.store_secret(name, value, metadata, overwrite)
    except Exception as e:
        logger.error(f"Failed to store secret '{name}': {e}")
        return False


def initialize_from_environment(prefix: str = "", overwrite: bool = False) -> int:
    """
    Initialize secret store from environment variables.

    Args:
        prefix: Optional prefix to filter environment variables
        overwrite: Whether to overwrite existing secrets

    Returns:
        Number of secrets loaded
    """
    store = get_secret_store()
    return store.load_from_environment(prefix=prefix, overwrite=overwrite)
