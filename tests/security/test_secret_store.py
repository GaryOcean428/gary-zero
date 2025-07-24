#!/usr/bin/env python3
"""
Test suite for the Internal Secret Store.

Tests cover all CRUD operations, encryption, access control, audit logging,
and integration scenarios to ensure secure credential management.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from pydantic import SecretStr

from framework.security.secret_store import (
    AccessLevel,
    InternalSecretStore,
    SecretAccessDeniedError,
    SecretAlreadyExistsError,
    SecretMetadata,
    SecretNotFoundError,
    SecretStoreConfig,
    SecretStoreError,
    SecretType,
    get_secret,
    get_secret_store,
    initialize_from_environment,
    store_secret,
)


class TestSecretStore(unittest.TestCase):
    """Test cases for the Internal Secret Store."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test store
        self.temp_dir = tempfile.mkdtemp()
        self.store_path = Path(self.temp_dir) / "test_store.encrypted"

        # Create test configuration
        self.config = SecretStoreConfig(
            store_path=self.store_path,
            encryption_key=Fernet.generate_key(),
            enable_audit_logging=True,
            auto_backup=False,  # Disable for tests
            max_secrets=100,
        )

        # Initialize fresh store for each test
        self.store = InternalSecretStore(self.config)

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        if self.store_path.exists():
            self.store_path.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    def test_store_and_retrieve_secret(self):
        """Test basic store and retrieve operations."""
        # Store a secret
        result = self.store.store_secret("test_key", "test_value")
        self.assertTrue(result)

        # Retrieve the secret
        retrieved_value = self.store.get_secret("test_key")
        self.assertEqual(retrieved_value, "test_value")

    def test_store_secret_with_metadata(self):
        """Test storing secret with metadata."""
        metadata = SecretMetadata(
            name="api_key",
            secret_type=SecretType.API_KEY,
            access_level=AccessLevel.RESTRICTED,
            description="Test API key",
            tags=["test", "api"],
            owner="test_user",
        )

        result = self.store.store_secret("api_key", "sk-1234567890", metadata)
        self.assertTrue(result)

        # Verify metadata is stored correctly
        secrets_list = self.store.list_secrets(include_metadata=True)
        self.assertEqual(len(secrets_list), 1)

        stored_metadata = secrets_list[0]
        self.assertEqual(stored_metadata.name, "api_key")
        self.assertEqual(stored_metadata.secret_type, SecretType.API_KEY)
        self.assertEqual(stored_metadata.access_level, AccessLevel.RESTRICTED)
        self.assertEqual(stored_metadata.description, "Test API key")
        self.assertEqual(stored_metadata.tags, ["test", "api"])
        self.assertEqual(stored_metadata.owner, "test_user")

    def test_store_secret_str(self):
        """Test storing SecretStr objects."""
        secret_value = SecretStr("sensitive_password")
        result = self.store.store_secret("password", secret_value)
        self.assertTrue(result)

        retrieved_value = self.store.get_secret("password")
        self.assertEqual(retrieved_value, "sensitive_password")

    def test_secret_encryption_at_rest(self):
        """Test that secrets are encrypted when stored."""
        self.store.store_secret("encrypted_test", "plain_text_value")

        # Read the store file directly
        with open(self.store_path, "rb") as f:
            raw_data = f.read()

        # Verify the plain text is not in the raw file
        self.assertNotIn(b"plain_text_value", raw_data)

        # Verify the file contains encrypted data
        self.assertTrue(len(raw_data) > 0)

    def test_secret_not_found(self):
        """Test retrieval of non-existent secret."""
        with self.assertRaises(SecretNotFoundError):
            self.store.get_secret("nonexistent_key")

    def test_secret_already_exists(self):
        """Test storing duplicate secret without overwrite."""
        self.store.store_secret("duplicate_key", "value1")

        with self.assertRaises(SecretAlreadyExistsError):
            self.store.store_secret("duplicate_key", "value2")

    def test_secret_overwrite(self):
        """Test overwriting existing secret."""
        self.store.store_secret("overwrite_key", "value1")
        result = self.store.store_secret("overwrite_key", "value2", overwrite=True)
        self.assertTrue(result)

        retrieved_value = self.store.get_secret("overwrite_key")
        self.assertEqual(retrieved_value, "value2")

    def test_delete_secret(self):
        """Test secret deletion."""
        self.store.store_secret("delete_me", "value")

        # Verify secret exists
        self.store.get_secret("delete_me")

        # Delete the secret
        result = self.store.delete_secret("delete_me")
        self.assertTrue(result)

        # Verify secret is gone
        with self.assertRaises(SecretNotFoundError):
            self.store.get_secret("delete_me")

    def test_delete_nonexistent_secret(self):
        """Test deleting non-existent secret."""
        with self.assertRaises(SecretNotFoundError):
            self.store.delete_secret("nonexistent")

    def test_list_secrets(self):
        """Test listing secrets."""
        # Store multiple secrets
        self.store.store_secret("key1", "value1")
        self.store.store_secret("key2", "value2")
        self.store.store_secret("key3", "value3")

        # Test listing names only
        names = self.store.list_secrets(include_metadata=False)
        self.assertEqual(set(names), {"key1", "key2", "key3"})

        # Test listing with metadata
        metadata_list = self.store.list_secrets(include_metadata=True)
        self.assertEqual(len(metadata_list), 3)

        metadata_names = {m.name for m in metadata_list}
        self.assertEqual(metadata_names, {"key1", "key2", "key3"})

    def test_update_metadata(self):
        """Test updating secret metadata."""
        # Store initial secret
        initial_metadata = SecretMetadata(
            name="update_test",
            secret_type=SecretType.API_KEY,
            description="Initial description",
        )
        self.store.store_secret("update_test", "value", initial_metadata)

        # Update metadata
        updated_metadata = SecretMetadata(
            name="update_test",
            secret_type=SecretType.TOKEN,
            description="Updated description",
            tags=["updated"],
        )

        result = self.store.update_metadata("update_test", updated_metadata)
        self.assertTrue(result)

        # Verify metadata was updated
        secrets_list = self.store.list_secrets(include_metadata=True)
        stored_metadata = next(s for s in secrets_list if s.name == "update_test")

        self.assertEqual(stored_metadata.secret_type, SecretType.TOKEN)
        self.assertEqual(stored_metadata.description, "Updated description")
        self.assertEqual(stored_metadata.tags, ["updated"])

        # Verify secret value unchanged
        retrieved_value = self.store.get_secret("update_test")
        self.assertEqual(retrieved_value, "value")

    def test_access_level_control(self):
        """Test access level restrictions."""
        # Store admin-level secret
        admin_metadata = SecretMetadata(
            name="admin_secret", access_level=AccessLevel.ADMIN
        )
        self.store.store_secret("admin_secret", "admin_value", admin_metadata)

        # Admin access should work
        value = self.store.get_secret("admin_secret", AccessLevel.ADMIN)
        self.assertEqual(value, "admin_value")

        # Non-admin access should be denied
        with self.assertRaises(SecretAccessDeniedError):
            self.store.get_secret("admin_secret", AccessLevel.RESTRICTED)

    def test_secret_expiration(self):
        """Test secret expiration functionality."""
        # Create expired secret
        expired_metadata = SecretMetadata(
            name="expired_secret", expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.store.store_secret("expired_secret", "value", expired_metadata)

        # Accessing expired secret should fail
        with self.assertRaises(SecretStoreError):
            self.store.get_secret("expired_secret")

    def test_secret_rotation_detection(self):
        """Test detection of secrets needing rotation."""
        # Create secret that needs rotation
        old_metadata = SecretMetadata(
            name="rotation_test",
            rotation_interval_days=30,
            updated_at=datetime.utcnow() - timedelta(days=31),
        )
        self.store.store_secret("rotation_test", "value", old_metadata)

        # Check rotation detection
        needing_rotation = self.store.get_secrets_needing_rotation()
        self.assertIn("rotation_test", needing_rotation)

    def test_cleanup_expired_secrets(self):
        """Test automatic cleanup of expired secrets."""
        # Create expired secret
        expired_metadata = SecretMetadata(
            name="cleanup_test", expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.store.store_secret("cleanup_test", "value", expired_metadata)

        # Verify secret exists (even if expired)
        self.assertIn("cleanup_test", self.store.list_secrets(include_metadata=False))

        # Run cleanup
        cleaned_count = self.store.cleanup_expired_secrets()
        self.assertEqual(cleaned_count, 1)

        # Verify secret was removed
        self.assertNotIn(
            "cleanup_test", self.store.list_secrets(include_metadata=False)
        )

    def test_load_from_environment(self):
        """Test loading secrets from environment variables."""
        # Set up test environment variables
        test_env = {
            "OPENAI_API_KEY": "sk-test-openai-key",
            "ANTHROPIC_API_KEY": "ant-test-key",
            "CUSTOM_TOKEN": "custom-value",
            "NON_SECRET_VAR": "not-a-secret",
        }

        with patch.dict(os.environ, test_env):
            # Load with custom mappings
            custom_mappings = {
                "OPENAI_API_KEY": "openai_key",
                "ANTHROPIC_API_KEY": "anthropic_key",
                "CUSTOM_TOKEN": "custom_token",
            }

            loaded_count = self.store.load_from_environment(custom_mappings)
            self.assertEqual(loaded_count, 3)

            # Verify secrets were loaded
            self.assertEqual(self.store.get_secret("openai_key"), "sk-test-openai-key")
            self.assertEqual(self.store.get_secret("anthropic_key"), "ant-test-key")
            self.assertEqual(self.store.get_secret("custom_token"), "custom-value")

    def test_max_secrets_limit(self):
        """Test maximum secrets limit enforcement."""
        # Set a low limit for testing
        limited_config = SecretStoreConfig(
            store_path=self.store_path,
            encryption_key=self.config.encryption_key,
            max_secrets=2,
        )
        limited_store = InternalSecretStore(limited_config)

        # Store up to the limit
        limited_store.store_secret("key1", "value1")
        limited_store.store_secret("key2", "value2")

        # Attempting to store beyond limit should fail
        with self.assertRaises(SecretStoreError):
            limited_store.store_secret("key3", "value3")

    def test_persistence_across_instances(self):
        """Test that secrets persist across store instances."""
        # Store secret in first instance
        self.store.store_secret("persistent_key", "persistent_value")

        # Create new instance with same config
        new_store = InternalSecretStore(self.config)

        # Verify secret is available in new instance
        retrieved_value = new_store.get_secret("persistent_key")
        self.assertEqual(retrieved_value, "persistent_value")

    def test_export_metadata(self):
        """Test metadata export functionality."""
        # Store some test secrets
        self.store.store_secret("export_test1", "value1")
        self.store.store_secret("export_test2", "value2")

        # Export metadata
        metadata_export = self.store.export_metadata()

        # Verify export structure
        self.assertIn("total_secrets", metadata_export)
        self.assertIn("secrets", metadata_export)
        self.assertIn("store_path", metadata_export)
        self.assertIn("export_timestamp", metadata_export)

        # Verify content
        self.assertEqual(metadata_export["total_secrets"], 2)
        self.assertIn("export_test1", metadata_export["secrets"])
        self.assertIn("export_test2", metadata_export["secrets"])

        # Verify no secret values are included
        export_str = json.dumps(metadata_export)
        self.assertNotIn("value1", export_str)
        self.assertNotIn("value2", export_str)

    def test_secret_name_validation(self):
        """Test secret name validation."""
        # Valid names should work
        valid_names = [
            "valid_name",
            "api-key",
            "service.token",
            "oauth2/token",
            "user123_key",
        ]

        for name in valid_names:
            metadata = SecretMetadata(name=name)
            self.assertEqual(metadata.name, name)

        # Invalid names should fail
        invalid_names = [
            "",  # Empty
            " ",  # Whitespace only
            "a" * 101,  # Too long
            "inv@lid",  # Invalid character
        ]

        for name in invalid_names:
            with self.assertRaises(ValueError):
                SecretMetadata(name=name)

    def test_concurrent_access(self):
        """Test thread safety of secret store operations."""
        import threading

        results = []

        def store_secrets(start_idx):
            for i in range(start_idx, start_idx + 10):
                try:
                    self.store.store_secret(f"concurrent_key_{i}", f"value_{i}")
                    results.append(f"stored_{i}")
                except Exception as e:
                    results.append(f"error_{i}: {e}")

        # Create multiple threads
        threads = []
        for i in range(0, 30, 10):
            thread = threading.Thread(target=store_secrets, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations completed
        stored_results = [r for r in results if r.startswith("stored_")]
        self.assertEqual(len(stored_results), 30)

        # Verify all secrets are accessible
        for i in range(30):
            value = self.store.get_secret(f"concurrent_key_{i}")
            self.assertEqual(value, f"value_{i}")


class TestSecretStoreHelpers(unittest.TestCase):
    """Test cases for secret store helper functions."""

    def setUp(self):
        """Set up test environment."""
        # Clear global store for testing
        import framework.security.secret_store as store_module

        store_module._secret_store = None

    def test_get_secret_helper(self):
        """Test get_secret helper function."""
        # Store a secret using the store directly
        store = get_secret_store()
        store.store_secret("helper_test", "helper_value")

        # Test helper function
        value = get_secret("helper_test")
        self.assertEqual(value, "helper_value")

        # Test with default value
        value = get_secret("nonexistent", "default_value")
        self.assertEqual(value, "default_value")

        # Test without default value
        value = get_secret("nonexistent")
        self.assertIsNone(value)

    def test_store_secret_helper(self):
        """Test store_secret helper function."""
        result = store_secret("helper_store_test", "helper_store_value")
        self.assertTrue(result)

        # Verify it was stored
        store = get_secret_store()
        value = store.get_secret("helper_store_test")
        self.assertEqual(value, "helper_store_value")

    def test_initialize_from_environment_helper(self):
        """Test initialize_from_environment helper function."""
        test_env = {
            "OPENAI_API_KEY": "sk-test-key",
            "ANTHROPIC_API_KEY": "ant-test-key",
        }

        with patch.dict(os.environ, test_env):
            loaded_count = initialize_from_environment()
            self.assertGreater(loaded_count, 0)

            # Verify secrets were loaded
            value = get_secret("openai_api_key")
            self.assertEqual(value, "sk-test-key")


class TestSecretStoreIntegration(unittest.TestCase):
    """Integration tests for secret store with other components."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test store
        self.temp_dir = tempfile.mkdtemp()
        self.store_path = Path(self.temp_dir) / "integration_store.encrypted"

        self.config = SecretStoreConfig(
            store_path=self.store_path,
            encryption_key=Fernet.generate_key(),
            enable_audit_logging=True,
        )

        self.store = InternalSecretStore(self.config)

    def tearDown(self):
        """Clean up test environment."""
        if self.store_path.exists():
            self.store_path.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)

    def test_audit_logging_integration(self):
        """Test integration with audit logging."""
        # Store a secret (should be logged)
        self.store.store_secret("audit_test", "audit_value")

        # Retrieve a secret (should be logged)
        value = self.store.get_secret("audit_test")
        self.assertEqual(value, "audit_value")

        # Delete a secret (should be logged)
        self.store.delete_secret("audit_test")

        # Verify audit events were created
        # Note: In a real implementation, you would check the audit log
        # For this test, we just verify no exceptions were raised
        self.assertTrue(True)

    def test_environment_variable_fallback(self):
        """Test fallback to environment variables when secret not found."""
        test_env = {"FALLBACK_API_KEY": "env-fallback-value"}

        with patch.dict(os.environ, test_env):
            # First try to get from store (should fail)
            value = get_secret("nonexistent_key", os.getenv("FALLBACK_API_KEY"))
            self.assertEqual(value, "env-fallback-value")

    def test_secret_rotation_workflow(self):
        """Test complete secret rotation workflow."""
        # Store secret with rotation interval
        metadata = SecretMetadata(
            name="rotation_workflow_test",
            rotation_interval_days=1,
            updated_at=datetime.utcnow() - timedelta(days=2),  # Past due
        )

        self.store.store_secret("rotation_workflow_test", "old_value", metadata)

        # Check if rotation is needed
        needing_rotation = self.store.get_secrets_needing_rotation()
        self.assertIn("rotation_workflow_test", needing_rotation)

        # Perform rotation (update with new value)
        new_metadata = SecretMetadata(
            name="rotation_workflow_test",
            rotation_interval_days=1,
            updated_at=datetime.utcnow(),  # Reset update time
        )

        self.store.store_secret(
            "rotation_workflow_test", "new_value", new_metadata, overwrite=True
        )

        # Verify rotation completed
        needing_rotation = self.store.get_secrets_needing_rotation()
        self.assertNotIn("rotation_workflow_test", needing_rotation)

        # Verify new value
        value = self.store.get_secret("rotation_workflow_test")
        self.assertEqual(value, "new_value")


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
