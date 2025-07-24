#!/usr/bin/env python3
"""
Test Kali Service Integration for Gary-Zero.

This module tests the integration with the Kali Linux Docker service
deployed on Railway, validating service discovery, connectivity, and
command execution capabilities.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.helpers.execution_mode import (
    get_execution_config,
    get_execution_info,
    should_use_kali_service,
)
from framework.helpers.kali_service import (
    KaliServiceConnector,
    get_kali_service,
    is_kali_service_available,
)


class TestKaliServiceConnector:
    """Test cases for KaliServiceConnector."""

    def setup_method(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_vars = {
            "KALI_SHELL_URL": "http://test-kali.railway.internal:8080",
            "KALI_SHELL_HOST": "test-kali.railway.internal",
            "KALI_SHELL_PORT": "8080",
            "KALI_USERNAME": "testuser",
            "KALI_PASSWORD": "testpass",
            "KALI_PUBLIC_URL": "https://test-kali.up.railway.app",
        }

        # Apply environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value

    def teardown_method(self):
        """Clean up test environment."""
        # Remove test environment variables
        for key in self.env_vars.keys():
            if key in os.environ:
                del os.environ[key]

    def test_kali_connector_initialization(self):
        """Test KaliServiceConnector initialization."""
        connector = KaliServiceConnector()

        assert connector.base_url == "http://test-kali.railway.internal:8080"
        assert connector.host == "test-kali.railway.internal"
        assert connector.port == 8080
        assert connector.username == "testuser"
        assert connector.password == "testpass"
        assert connector.public_url == "https://test-kali.up.railway.app"

    @patch("requests.Session.get")
    def test_is_available_success(self, mock_get):
        """Test successful service availability check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        connector = KaliServiceConnector()
        assert connector.is_available() is True

        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_is_available_failure(self, mock_get):
        """Test failed service availability check."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        connector = KaliServiceConnector()
        assert connector.is_available() is False

    @patch("requests.Session.get")
    def test_get_service_info_success(self, mock_get):
        """Test successful service info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service": "kali-linux-docker",
            "version": "2024.1",
            "status": "running",
        }
        mock_get.return_value = mock_response

        connector = KaliServiceConnector()
        info = connector.get_service_info()

        assert info["service"] == "kali-linux-docker"
        assert info["version"] == "2024.1"
        assert info["status"] == "running"

    @patch("requests.Session.post")
    def test_execute_command_success(self, mock_post):
        """Test successful command execution."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "stdout": "Linux kali 5.15.0\n",
            "stderr": "",
            "exit_code": 0,
        }
        mock_post.return_value = mock_response

        connector = KaliServiceConnector()
        result = connector.execute_command("uname -a")

        assert result["success"] is True
        assert "Linux kali" in result["stdout"]
        assert result["exit_code"] == 0

    @patch("requests.Session.post")
    def test_execute_command_failure(self, mock_post):
        """Test failed command execution."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        connector = KaliServiceConnector()
        result = connector.execute_command("invalid_command")

        assert result["success"] is False
        assert "HTTP 500" in result["error"]

    @patch("requests.Session.post")
    def test_run_security_scan(self, mock_post):
        """Test security scan execution."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "stdout": "Nmap scan report for target.com\n22/tcp open ssh\n80/tcp open http\n",
            "stderr": "",
            "exit_code": 0,
        }
        mock_post.return_value = mock_response

        connector = KaliServiceConnector()
        result = connector.run_security_scan("target.com", "basic")

        assert result["success"] is True
        assert "Nmap scan report" in result["stdout"]
        assert "22/tcp open ssh" in result["stdout"]

    @patch("requests.Session.post")
    def test_get_kali_tools(self, mock_post):
        """Test Kali tools listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "stdout": "nmap\nnikto\nsqlmap\nmetasploit-framework\n",
            "stderr": "",
            "exit_code": 0,
        }
        mock_post.return_value = mock_response

        connector = KaliServiceConnector()
        result = connector.get_kali_tools()

        assert result["success"] is True
        assert "nmap" in result["stdout"]
        assert "nikto" in result["stdout"]


class TestExecutionModeIntegration:
    """Test cases for execution mode integration with Kali service."""

    def setup_method(self):
        """Set up test environment."""
        self.env_vars = {
            "KALI_SHELL_URL": "http://test-kali.railway.internal:8080",
            "KALI_SHELL_HOST": "test-kali.railway.internal",
            "KALI_SHELL_PORT": "8080",
            "KALI_USERNAME": "testuser",
            "KALI_PASSWORD": "testpass",
        }

        for key, value in self.env_vars.items():
            os.environ[key] = value

    def teardown_method(self):
        """Clean up test environment."""
        for key in self.env_vars.keys():
            if key in os.environ:
                del os.environ[key]

        # Clean up CODE_EXECUTION_MODE
        if "CODE_EXECUTION_MODE" in os.environ:
            del os.environ["CODE_EXECUTION_MODE"]

    def test_should_use_kali_service_explicit(self):
        """Test explicit Kali service mode selection."""
        os.environ["CODE_EXECUTION_MODE"] = "kali"
        assert should_use_kali_service() is True

    @patch("framework.helpers.kali_service.is_kali_service_available")
    def test_should_use_kali_service_auto_detect(self, mock_is_available):
        """Test auto-detection of Kali service."""
        mock_is_available.return_value = True
        assert should_use_kali_service() is True

        mock_is_available.return_value = False
        assert should_use_kali_service() is False

    def test_get_execution_config_kali(self):
        """Test execution configuration for Kali service."""
        os.environ["CODE_EXECUTION_MODE"] = "kali"

        config = get_execution_config()

        assert config["method"] == "kali"
        assert config["host"] == "test-kali.railway.internal"
        assert config["port"] == 8080
        assert config["username"] == "testuser"
        assert config["password"] == "testpass"

    @patch("framework.helpers.kali_service.is_kali_service_available")
    def test_get_execution_info_kali(self, mock_is_available):
        """Test execution info display for Kali service."""
        os.environ["CODE_EXECUTION_MODE"] = "kali"
        mock_is_available.return_value = True

        info = get_execution_info()

        assert "Kali service execution" in info
        assert "test-kali.railway.internal:8080" in info
        assert "✅" in info


class TestServiceFactoryFunctions:
    """Test cases for service factory functions."""

    def test_get_kali_service_no_config(self):
        """Test factory function with no configuration."""
        # Ensure no Kali environment variables are set
        for key in ["KALI_SHELL_URL", "KALI_SHELL_HOST"]:
            if key in os.environ:
                del os.environ[key]

        service = get_kali_service()
        assert service is None

    @patch("framework.helpers.kali_service.KaliServiceConnector.is_available")
    def test_get_kali_service_available(self, mock_is_available):
        """Test factory function with available service."""
        os.environ["KALI_SHELL_URL"] = "http://test-kali.railway.internal:8080"
        mock_is_available.return_value = True

        service = get_kali_service()
        assert service is not None
        assert isinstance(service, KaliServiceConnector)

        # Clean up
        service.close()

    @patch("framework.helpers.kali_service.KaliServiceConnector.is_available")
    def test_get_kali_service_unavailable(self, mock_is_available):
        """Test factory function with unavailable service."""
        os.environ["KALI_SHELL_URL"] = "http://test-kali.railway.internal:8080"
        mock_is_available.return_value = False

        service = get_kali_service()
        assert service is None

    @patch("framework.helpers.kali_service.get_kali_service")
    def test_is_kali_service_available_true(self, mock_get_service):
        """Test service availability check - available."""
        mock_connector = Mock()
        mock_connector.is_available.return_value = True
        mock_get_service.return_value = mock_connector

        assert is_kali_service_available() is True
        mock_connector.close.assert_called_once()

    @patch("framework.helpers.kali_service.get_kali_service")
    def test_is_kali_service_available_false(self, mock_get_service):
        """Test service availability check - unavailable."""
        mock_get_service.return_value = None

        assert is_kali_service_available() is False


def test_integration_scenario():
    """Integration test simulating real Railway deployment scenario."""
    # Set up Railway-like environment
    env_vars = {
        "RAILWAY_ENVIRONMENT": "production",
        "CODE_EXECUTION_MODE": "kali",
        "KALI_SHELL_URL": "http://kali-linux-docker.railway.internal:8080",
        "KALI_SHELL_HOST": "kali-linux-docker.railway.internal",
        "KALI_SHELL_PORT": "8080",
        "KALI_USERNAME": "GaryOcean",
        "KALI_PASSWORD": "I.Am.Dev.1",
        "KALI_PUBLIC_URL": "https://kali-linux-docker.up.railway.app",
    }

    try:
        # Apply environment
        for key, value in env_vars.items():
            os.environ[key] = value

        # Test configuration
        config = get_execution_config()
        assert config["method"] == "kali"
        assert config["url"] == "http://kali-linux-docker.railway.internal:8080"

        # Test service detection
        assert should_use_kali_service() is True

        # Test connector initialization
        connector = KaliServiceConnector()
        assert connector.base_url == "http://kali-linux-docker.railway.internal:8080"
        assert connector.username == "GaryOcean"

    finally:
        # Clean up environment
        for key in env_vars:
            if key in os.environ:
                del os.environ[key]


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
