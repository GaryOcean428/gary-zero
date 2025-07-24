"""Integration tests for model validation in settings API endpoints.

This module tests the UI → API round-trip functionality for model selection
validation, ensuring that only modern models or embedding models are accepted.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from framework.api.settings_get import GetSettings
from framework.api.settings_set import SetSettings
from framework.helpers.api import Request


class TestModelValidationAPI:
    """Test class for model validation in settings API."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.remote_addr = "127.0.0.1"
        request.headers = {}
        return request

    @pytest.fixture
    def mock_app(self):
        """Create a mock Flask app instance."""
        app = Flask(__name__)
        return app

    @pytest.fixture
    def settings_get_handler(self, mock_app):
        """Create a GetSettings handler instance."""
        return GetSettings(mock_app, None)

    @pytest.fixture
    def settings_set_handler(self, mock_app):
        """Create a SetSettings handler instance."""
        return SetSettings(mock_app, None)

    @pytest.fixture
    def sample_valid_settings(self):
        """Sample settings data with modern models."""
        return {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-3-5-sonnet-latest"}
                    ]
                },
                {
                    "id": "embed_model", 
                    "fields": [
                        {"id": "embed_model_provider", "value": "OPENAI"},
                        {"id": "embed_model_name", "value": "text-embedding-3-large"}
                    ]
                }
            ]
        }

    @pytest.fixture
    def sample_invalid_settings(self):
        """Sample settings data with non-modern models."""
        return {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-2-legacy"}  # Invalid: not modern
                    ]
                },
                {
                    "id": "util_model",
                    "fields": [
                        {"id": "util_model_provider", "value": "OPENAI"},
                        {"id": "util_model_name", "value": "gpt-3.5-turbo"}  # Invalid: not modern
                    ]
                }
            ]
        }

    @patch('framework.helpers.settings.get_settings')
    async def test_get_settings_returns_valid_structure(
        self, mock_get_settings, settings_get_handler, mock_request
    ):
        """Test that get_settings returns valid settings structure."""
        # Mock the settings response
        mock_settings = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest",
            "embed_model_provider": "OPENAI", 
            "embed_model_name": "text-embedding-3-large",
            "api_keys": {}
        }
        mock_get_settings.return_value = mock_settings

        # Call the handler
        result = await settings_get_handler.process({}, mock_request)

        # Verify structure
        assert "settings" in result
        assert "sections" in result["settings"]
        assert len(result["settings"]["sections"]) > 0

    @patch('framework.helpers.settings.convert_in')
    @patch('framework.helpers.settings.set_settings')
    async def test_valid_models_pass_validation(
        self, mock_set_settings, mock_convert_in, 
        settings_set_handler, mock_request, sample_valid_settings
    ):
        """Test that valid modern models pass validation."""
        # Mock the conversion
        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest",
            "embed_model_provider": "OPENAI",
            "embed_model_name": "text-embedding-3-large"
        }

        # Should not raise an exception
        result = await settings_set_handler.process(sample_valid_settings, mock_request)
        
        # Verify settings were processed
        assert "settings" in result
        mock_set_settings.assert_called_once()

    @patch('framework.helpers.settings.convert_in')
    async def test_invalid_models_fail_validation(
        self, mock_convert_in, settings_set_handler, 
        mock_request, sample_invalid_settings
    ):
        """Test that invalid non-modern models fail validation."""
        # Mock the conversion to return invalid models
        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-2-legacy",  # Invalid
            "util_model_provider": "OPENAI", 
            "util_model_name": "gpt-3.5-turbo"  # Invalid
        }

        # Should raise a 400 error
        with pytest.raises(Exception) as exc_info:
            await settings_set_handler.process(sample_invalid_settings, mock_request)
        
        # In a real Flask app, this would be a werkzeug.exceptions.BadRequest
        # But in our test, flask.abort will raise a different exception

    @patch('framework.helpers.settings.convert_in')
    @patch('framework.helpers.settings.set_settings')
    async def test_embedding_models_exemption(
        self, mock_set_settings, mock_convert_in,
        settings_set_handler, mock_request
    ):
        """Test that embedding models are exempt from modern-only rule."""
        # Test with embedding models that might not be marked as modern
        embedding_settings = {
            "sections": [
                {
                    "id": "embed_model",
                    "fields": [
                        {"id": "embed_model_provider", "value": "OPENAI"},
                        {"id": "embed_model_name", "value": "text-embedding-3-small"}
                    ]
                }
            ]
        }
        
        mock_convert_in.return_value = {
            "embed_model_provider": "OPENAI",
            "embed_model_name": "text-embedding-3-small"
        }

        # Should pass validation due to embedding exemption
        result = await settings_set_handler.process(embedding_settings, mock_request)
        
        assert "settings" in result
        mock_set_settings.assert_called_once()

    @patch('framework.helpers.settings.convert_in')
    async def test_nonexistent_model_fails_validation(
        self, mock_convert_in, settings_set_handler, mock_request
    ):
        """Test that non-existent models fail validation."""
        nonexistent_settings = {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-nonexistent-model"}
                    ]
                }
            ]
        }
        
        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-nonexistent-model"
        }

        # Should raise a 400 error for non-existent model
        with pytest.raises(Exception):
            await settings_set_handler.process(nonexistent_settings, mock_request)

    @patch('framework.helpers.settings.convert_in')
    @patch('framework.helpers.settings.set_settings')
    async def test_partial_settings_validation(
        self, mock_set_settings, mock_convert_in,
        settings_set_handler, mock_request
    ):
        """Test validation with partial settings updates."""
        # Test with only some model fields present
        partial_settings = {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-3-5-sonnet-latest"}
                    ]
                }
            ]
        }
        
        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest",
            # Other fields might be None or missing
            "util_model_provider": None,
            "util_model_name": None
        }

        # Should pass validation for present fields, ignore missing ones
        result = await settings_set_handler.process(partial_settings, mock_request)
        
        assert "settings" in result
        mock_set_settings.assert_called_once()

    @patch('framework.helpers.settings.convert_in')
    @patch('framework.helpers.settings.set_settings')
    async def test_multiple_model_types_validation(
        self, mock_set_settings, mock_convert_in,
        settings_set_handler, mock_request
    ):
        """Test validation across multiple model types."""
        multi_model_settings = {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-3-5-sonnet-latest"}
                    ]
                },
                {
                    "id": "coding_agent",
                    "fields": [
                        {"id": "coding_agent_provider", "value": "OPENAI"},
                        {"id": "coding_agent_name", "value": "o1-mini"}
                    ]
                },
                {
                    "id": "browser_model",
                    "fields": [
                        {"id": "browser_model_provider", "value": "ANTHROPIC"},
                        {"id": "browser_model_name", "value": "claude-3-5-haiku-latest"}
                    ]
                }
            ]
        }
        
        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest",
            "coding_agent_provider": "OPENAI",
            "coding_agent_name": "o1-mini",
            "browser_model_provider": "ANTHROPIC",
            "browser_model_name": "claude-3-5-haiku-latest"
        }

        # All models should pass validation
        result = await settings_set_handler.process(multi_model_settings, mock_request)
        
        assert "settings" in result
        mock_set_settings.assert_called_once()


class TestUIAPIRoundTrip:
    """Test UI to API round-trip functionality."""

    @pytest.fixture
    def mock_flask_app(self):
        """Create a Flask app for testing."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    @patch('framework.helpers.settings.get_settings')
    @patch('framework.helpers.settings.set_settings')
    @patch('framework.helpers.settings.convert_in')
    @patch('framework.helpers.settings.convert_out')
    async def test_full_round_trip_valid_settings(
        self, mock_convert_out, mock_convert_in, mock_set_settings, 
        mock_get_settings, mock_flask_app
    ):
        """Test complete round-trip: UI → API → validation → storage."""
        
        # Setup mock responses
        mock_get_settings.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest"
        }
        
        mock_convert_out.return_value = {
            "sections": [
                {
                    "id": "chat_model",
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "claude-3-5-sonnet-latest"}
                    ]
                }
            ]
        }

        mock_convert_in.return_value = {
            "chat_model_provider": "ANTHROPIC",
            "chat_model_name": "claude-3-5-sonnet-latest"
        }

        # Create handlers
        get_handler = GetSettings(mock_flask_app, None)
        set_handler = SetSettings(mock_flask_app, None)
        
        mock_request = MagicMock()
        mock_request.remote_addr = "127.0.0.1"

        # Step 1: Get current settings (simulating UI load)
        get_result = await get_handler.process({}, mock_request)
        assert "settings" in get_result

        # Step 2: Modify and send back settings (simulating UI save)
        modified_settings = get_result["settings"]
        set_result = await set_handler.process(modified_settings, mock_request)
        
        # Verify the round-trip completed successfully
        assert "settings" in set_result
        mock_set_settings.assert_called_once()

    async def test_round_trip_with_validation_error(self, mock_flask_app):
        """Test round-trip with validation errors."""
        # This test would ideally use a real Flask test client
        # but for now we'll test the validation logic directly
        
        set_handler = SetSettings(mock_flask_app, None)
        mock_request = MagicMock()
        
        invalid_settings = {
            "sections": [
                {
                    "id": "chat_model", 
                    "fields": [
                        {"id": "chat_model_provider", "value": "ANTHROPIC"},
                        {"id": "chat_model_name", "value": "invalid-model"}
                    ]
                }
            ]
        }

        with patch('framework.helpers.settings.convert_in') as mock_convert_in:
            mock_convert_in.return_value = {
                "chat_model_provider": "ANTHROPIC",
                "chat_model_name": "invalid-model"
            }
            
            # Should raise validation error
            with pytest.raises(Exception):
                await set_handler.process(invalid_settings, mock_request)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

