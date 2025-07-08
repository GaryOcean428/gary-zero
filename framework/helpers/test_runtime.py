"""Test script for the refactored runtime module."""

# Standard library imports
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock external dependencies before importing the module
sys.modules["langchain_anthropic"] = MagicMock()
sys.modules["langchain_anthropic.chat_models"] = MagicMock()
sys.modules["langchain_anthropic.chat_models.base"] = MagicMock()

# Add parent directory to path to allow importing from the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the settings module to avoid loading real settings
sys.modules["python.helpers.settings"] = MagicMock()
sys.modules["python.helpers.dotenv"] = MagicMock()
sys.modules["python.helpers.rfc"] = MagicMock()

# Now import the module under test
with patch.dict(
    "sys.modules",
    {
        "settings": MagicMock(),
        "dotenv": MagicMock(),
        "rfc": MagicMock(),
    },
):
    # Local application imports
    from framework.helpers import runtime


class TestRuntimeState(unittest.TestCase):
    """Test the RuntimeState class and its functionality."""

    def setUp(self):
        """Reset the RuntimeState instance before each test."""
        runtime.RuntimeState._instance = None
        runtime.RuntimeState._initialized = False

    def test_singleton_pattern(self):
        """Test that only one instance of RuntimeState exists."""
        instance1 = runtime.RuntimeState.get_instance()
        instance2 = runtime.RuntimeState.get_instance()
        self.assertIs(instance1, instance2)

    def test_parse_args(self):
        """Test argument parsing."""
        test_args = ["--port", "8080", "--development", "True"]
        with patch.object(sys, "argv", ["test"] + test_args):
            runtime.initialize()
            self.assertEqual(runtime.get_arg("port"), 8080)
            self.assertTrue(runtime.get_arg("development"))

    def test_get_arg_default(self):
        """Test getting an argument with a default value."""
        runtime.initialize()
        self.assertIsNone(runtime.get_arg("nonexistent"))
        self.assertEqual(runtime.get_arg("nonexistent", "default"), "default")

    def test_has_arg(self):
        """Test checking if an argument exists."""
        test_args = ["--port", "8080"]
        with patch.object(sys, "argv", ["test"] + test_args):
            runtime.initialize()
            self.assertTrue(runtime.has_arg("port"))
            self.assertFalse(runtime.has_arg("nonexistent"))

    def test_is_dockerized(self):
        """Test dockerized environment detection."""
        with patch.object(runtime, "get_arg", return_value=True):
            self.assertTrue(runtime.is_dockerized())
        with patch.object(runtime, "get_arg", return_value=False):
            self.assertFalse(runtime.is_dockerized())

    def test_get_local_url(self):
        """Test getting local URL based on environment."""
        with patch.object(runtime, "is_dockerized", return_value=True):
            self.assertEqual(runtime.get_local_url(), "host.docker.internal")
        with patch.object(runtime, "is_dockerized", return_value=False):
            self.assertEqual(runtime.get_local_url(), "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
