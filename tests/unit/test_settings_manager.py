"""Unit tests for SettingsManager volume path refactoring."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from framework.helpers import files
from framework.helpers.settings_manager import SettingsManager


class TestSettingsManagerVolumeRefactor(unittest.TestCase):
    """Test SettingsManager refactoring to use volume path."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        # Reset the singleton instance before each test
        SettingsManager._instance = None

        # Mock the get_data_path to use our test directory
        self.data_dir_patcher = patch.dict(
            os.environ, {"DATA_DIR": os.path.join(self.test_dir, "data")}
        )
        self.data_dir_patcher.start()
        self.addCleanup(self.data_dir_patcher.stop)

        # Mock get_abs_path to use our test directory for legacy path
        self.abs_path_patcher = patch(
            "framework.helpers.files.get_abs_path",
            side_effect=lambda path: os.path.join(self.test_dir, path),
        )
        self.abs_path_patcher.start()
        self.addCleanup(self.abs_path_patcher.stop)

    def test_get_data_path_helper(self):
        """Test that get_data_path helper works correctly."""
        # Test with default DATA_DIR
        with patch.dict(os.environ, {"DATA_DIR": "/app/data"}, clear=False):
            result = files.get_data_path("settings.json")
            self.assertEqual(result, "/app/data/settings.json")

        # Test with empty relative path
        with patch.dict(os.environ, {"DATA_DIR": "/app/data"}, clear=False):
            result = files.get_data_path()
            self.assertEqual(result, "/app/data")

        # Test with custom DATA_DIR
        with patch.dict(os.environ, {"DATA_DIR": "/custom/path"}, clear=False):
            result = files.get_data_path("settings.json")
            self.assertEqual(result, "/custom/path/settings.json")

    def test_settings_manager_uses_data_path(self):
        """Test that SettingsManager uses the new data path."""
        manager = SettingsManager()
        expected_path = os.path.join(self.test_dir, "data", "settings.json")
        self.assertEqual(manager._settings_file, expected_path)

    def test_directory_creation_in_data_path(self):
        """Test that directory creation works under /app/data."""
        # Mock default settings to avoid circular imports
        mock_settings = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-20241022",
        }

        with patch(
            "framework.helpers.settings_manager.get_default_settings"
        ) as mock_get_default:
            mock_get_default.return_value = mock_settings
            with patch(
                "framework.helpers.settings_manager.normalize_settings"
            ) as mock_normalize:
                mock_normalize.side_effect = lambda x: x or mock_settings

                manager = SettingsManager()

                # Set some settings to trigger file creation
                manager.set_settings(mock_settings, apply=False)

                # Verify the directory was created
                data_dir = os.path.join(self.test_dir, "data")
                self.assertTrue(os.path.exists(data_dir))

                # Verify the settings file was created
                settings_file = os.path.join(data_dir, "settings.json")
                self.assertTrue(os.path.exists(settings_file))

    def test_backward_compatibility_migration(self):
        """Test migration from legacy /app/tmp/settings.json to new location."""
        # Create legacy settings file
        legacy_dir = os.path.join(self.test_dir, "tmp")
        os.makedirs(legacy_dir, exist_ok=True)
        legacy_file = os.path.join(legacy_dir, "settings.json")

        legacy_settings = {
            "chat_model_provider": "OPENAI",
            "chat_model_name": "gpt-4",
            "test_value": "legacy_data",
        }

        with open(legacy_file, "w") as f:
            json.dump(legacy_settings, f)

        # Mock required functions to avoid circular imports
        with patch(
            "framework.helpers.settings_manager.get_default_settings"
        ) as mock_get_default:
            mock_get_default.return_value = legacy_settings
            with patch(
                "framework.helpers.settings_manager.normalize_settings"
            ) as mock_normalize:
                mock_normalize.side_effect = lambda x: x or legacy_settings

                # Create SettingsManager instance (should trigger migration)
                manager = SettingsManager()
                settings = manager.get_settings()

                # Verify migration occurred
                new_file = os.path.join(self.test_dir, "data", "settings.json")
                self.assertTrue(os.path.exists(new_file))

                # Verify the content was migrated correctly
                with open(new_file) as f:
                    migrated_settings = json.load(f)

                self.assertEqual(migrated_settings["test_value"], "legacy_data")
                self.assertEqual(migrated_settings["chat_model_provider"], "OPENAI")

    def test_no_migration_when_new_file_exists(self):
        """Test that no migration occurs if new file already exists."""
        # Create both legacy and new settings files
        legacy_dir = os.path.join(self.test_dir, "tmp")
        os.makedirs(legacy_dir, exist_ok=True)
        legacy_file = os.path.join(legacy_dir, "settings.json")

        legacy_settings = {"test_value": "legacy_data"}
        with open(legacy_file, "w") as f:
            json.dump(legacy_settings, f)

        # Create new settings file
        new_dir = os.path.join(self.test_dir, "data")
        os.makedirs(new_dir, exist_ok=True)
        new_file = os.path.join(new_dir, "settings.json")

        new_settings = {"test_value": "new_data"}
        with open(new_file, "w") as f:
            json.dump(new_settings, f)

        # Mock required functions
        with patch(
            "framework.helpers.settings_manager.get_default_settings"
        ) as mock_get_default:
            mock_get_default.return_value = new_settings
            with patch(
                "framework.helpers.settings_manager.normalize_settings"
            ) as mock_normalize:
                mock_normalize.side_effect = lambda x: x or new_settings

                # Create SettingsManager instance
                manager = SettingsManager()
                settings = manager.get_settings()

                # Verify the new file content is preserved (no migration)
                with open(new_file) as f:
                    current_settings = json.load(f)

                self.assertEqual(current_settings["test_value"], "new_data")

    def test_no_migration_when_legacy_file_not_exists(self):
        """Test that no migration occurs if legacy file doesn't exist."""
        # Mock required functions
        mock_settings = {"chat_model_provider": "ANTHROPIC"}

        with patch(
            "framework.helpers.settings_manager.get_default_settings"
        ) as mock_get_default:
            mock_get_default.return_value = mock_settings
            with patch(
                "framework.helpers.settings_manager.normalize_settings"
            ) as mock_normalize:
                mock_normalize.side_effect = lambda x: x or mock_settings

                # Create SettingsManager instance
                manager = SettingsManager()
                settings = manager.get_settings()

                # Verify only the default settings are present
                self.assertEqual(settings["chat_model_provider"], "ANTHROPIC")

    def test_migration_handles_file_errors_gracefully(self):
        """Test that migration handles file operation errors gracefully."""
        # Create legacy settings file
        legacy_dir = os.path.join(self.test_dir, "tmp")
        os.makedirs(legacy_dir, exist_ok=True)
        legacy_file = os.path.join(legacy_dir, "settings.json")

        legacy_settings = {"test_value": "legacy_data"}
        with open(legacy_file, "w") as f:
            json.dump(legacy_settings, f)

        # Mock shutil.copy2 to raise an exception
        with patch(
            "framework.helpers.settings_manager.shutil.copy2",
            side_effect=OSError("Permission denied"),
        ):
            with patch(
                "framework.helpers.settings_manager.get_default_settings"
            ) as mock_get_default:
                mock_get_default.return_value = legacy_settings
                with patch(
                    "framework.helpers.settings_manager.normalize_settings"
                ) as mock_normalize:
                    mock_normalize.side_effect = lambda x: x or legacy_settings

                    # Create SettingsManager instance (should not raise exception)
                    manager = SettingsManager()
                    settings = manager.get_settings()

                    # Verify it falls back to default settings
                    self.assertIsNotNone(settings)

    def test_env_override_data_dir(self):
        """Test that DATA_DIR environment variable can override the data directory."""
        custom_data_dir = os.path.join(self.test_dir, "custom_data")

        with patch.dict(os.environ, {"DATA_DIR": custom_data_dir}):
            manager = SettingsManager()
            expected_path = os.path.join(custom_data_dir, "settings.json")
            self.assertEqual(manager._settings_file, expected_path)

    def test_persistence_across_manager_instances(self):
        """Test that settings persist correctly across SettingsManager instances."""
        # Create first manager instance and set some settings
        mock_settings = {
            "chat_model_provider": "ANTHROPIC",
            "test_persistence": "persistent_value",
        }

        with patch(
            "framework.helpers.settings_manager.get_default_settings"
        ) as mock_get_default:
            mock_get_default.return_value = mock_settings
            with patch(
                "framework.helpers.settings_manager.normalize_settings"
            ) as mock_normalize:
                mock_normalize.side_effect = lambda x: x or mock_settings

                manager1 = SettingsManager()
                manager1.set_settings(mock_settings, apply=False)

                # Reset singleton to simulate new instance
                SettingsManager._instance = None

                # Create second manager instance
                manager2 = SettingsManager()
                settings = manager2.get_settings()

                # Verify settings persisted
                self.assertEqual(settings.get("test_persistence"), "persistent_value")


if __name__ == "__main__":
    unittest.main()


def test_settings_persist_across_instances():
    """Ensure settings persist correctly across different instances."""
    # Set initial settings
    manager1 = SettingsManager()
    manager1.set_settings({"test_key": "initial_value"}, apply=False)

    # Retrieve settings using a new instance
    SettingsManager._instance = None
    manager2 = SettingsManager()
    settings = manager2.get_settings()

    assert settings.get("test_key") == "initial_value"


def test_default_util_model():
    """Ensure the default utility model name is set correctly."""
    manager = SettingsManager()
    settings = manager.get_settings()

    assert settings.get("util_model_name") == "gpt-4o-mini"


def test_model_catalog_validation():
    """Assert that modern and valid models are loaded properly."""
    from framework.helpers.model_catalog import MODEL_CATALOG

    # Check if all models marked as modern have valid data
    for provider, models in MODEL_CATALOG.items():
        for model in models:
            if "modern" in model and model["modern"]:
                assert "release_date" in model and model["release_date"] > "2024-06-01"
                assert len(model["value"]) > 0
