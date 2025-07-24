"""Unit tests for the validate_model_selection function.

This module tests the core validation logic for model selection,
ensuring proper enforcement of modern-only policy with embedding exemptions.
"""

import pytest
from unittest.mock import patch
from framework.helpers.model_catalog import validate_model_selection


class TestValidateModelSelection:
    """Test class for validate_model_selection function."""

    def test_valid_modern_model_passes(self):
        """Test that a valid modern model passes validation."""
        # Use a known modern model from the catalog
        assert validate_model_selection("ANTHROPIC", "claude-3-5-sonnet-latest") is True
        assert validate_model_selection("OPENAI", "o1-mini") is True
        assert validate_model_selection("GOOGLE", "gemini-2.0-flash") is True

    def test_valid_embedding_model_passes(self):
        """Test that embedding models pass validation (exemption)."""
        # Test with embedding models
        assert validate_model_selection("OPENAI", "text-embedding-3-large") is True
        assert validate_model_selection("OPENAI", "text-embedding-3-small") is True

    def test_nonexistent_model_fails(self):
        """Test that non-existent models fail validation."""
        assert validate_model_selection("ANTHROPIC", "claude-nonexistent") is False
        assert validate_model_selection("OPENAI", "gpt-nonexistent") is False
        assert validate_model_selection("GOOGLE", "gemini-fake-model") is False

    def test_nonexistent_provider_fails(self):
        """Test that non-existent providers fail validation."""
        assert validate_model_selection("FAKE_PROVIDER", "some-model") is False
        assert validate_model_selection("", "claude-3-5-sonnet-latest") is False

    def test_empty_parameters_fail(self):
        """Test that empty parameters fail validation."""
        assert validate_model_selection("", "") is False
        assert validate_model_selection("ANTHROPIC", "") is False
        assert validate_model_selection("", "claude-3-5-sonnet-latest") is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_non_modern_non_embedding_model_fails(self, mock_get_models):
        """Test that non-modern, non-embedding models fail validation."""
        # Mock a non-modern model
        mock_get_models.return_value = [
            {
                "value": "old-model-v1",
                "label": "Old Model V1",
                "modern": False,  # Not modern
                "release_date": "2023-01-01"
            }
        ]
        
        assert validate_model_selection("TEST_PROVIDER", "old-model-v1") is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_embedding_model_without_modern_flag_passes(self, mock_get_models):
        """Test that embedding models pass even without modern flag."""
        # Mock an embedding model without modern flag
        mock_get_models.return_value = [
            {
                "value": "text-embedding-custom",
                "label": "Custom Text Embedding",
                "modern": False,  # Not explicitly modern
                "release_date": "2023-01-01"
            }
        ]
        
        # Should pass due to "embedding" in name
        assert validate_model_selection("TEST_PROVIDER", "text-embedding-custom") is True

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_modern_model_passes(self, mock_get_models):
        """Test that models marked as modern pass validation."""
        # Mock a modern model
        mock_get_models.return_value = [
            {
                "value": "new-model-v2",
                "label": "New Model V2", 
                "modern": True,  # Explicitly modern
                "release_date": "2024-08-01"
            }
        ]
        
        assert validate_model_selection("TEST_PROVIDER", "new-model-v2") is True

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_model_with_missing_modern_flag_fails(self, mock_get_models):
        """Test that models missing modern flag fail validation."""
        # Mock a model with no modern flag (defaults to False)
        mock_get_models.return_value = [
            {
                "value": "ambiguous-model",
                "label": "Ambiguous Model",
                # No modern flag - should default to False
                "release_date": "2024-01-01"
            }
        ]
        
        assert validate_model_selection("TEST_PROVIDER", "ambiguous-model") is False

    def test_case_insensitive_embedding_detection(self):
        """Test that embedding detection is case-insensitive."""
        with patch('framework.helpers.model_catalog.get_models_for_provider') as mock_get_models:
            # Mock models with different cases of "embedding"
            mock_get_models.return_value = [
                {
                    "value": "TEXT-EMBEDDING-UPPER",
                    "label": "Upper Case Embedding",
                    "modern": False
                },
                {
                    "value": "text-Embedding-mixed",
                    "label": "Mixed Case Embedding", 
                    "modern": False
                }
            ]
            
            assert validate_model_selection("TEST_PROVIDER", "TEXT-EMBEDDING-UPPER") is True
            assert validate_model_selection("TEST_PROVIDER", "text-Embedding-mixed") is True

    def test_embedding_in_middle_of_name(self):
        """Test that 'embedding' detection works when in middle of model name."""
        with patch('framework.helpers.model_catalog.get_models_for_provider') as mock_get_models:
            mock_get_models.return_value = [
                {
                    "value": "custom-embedding-v2",
                    "label": "Custom Embedding V2",
                    "modern": False
                }
            ]
            
            assert validate_model_selection("TEST_PROVIDER", "custom-embedding-v2") is True

    def test_partial_embedding_match_fails(self):
        """Test that partial matches of 'embedding' don't trigger exemption."""
        with patch('framework.helpers.model_catalog.get_models_for_provider') as mock_get_models:
            mock_get_models.return_value = [
                {
                    "value": "embed-model",  # "embed" but not "embedding"
                    "label": "Embed Model",
                    "modern": False
                }
            ]
            
            assert validate_model_selection("TEST_PROVIDER", "embed-model") is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_both_modern_and_embedding_passes(self, mock_get_models):
        """Test that models that are both modern and embedding pass validation."""
        mock_get_models.return_value = [
            {
                "value": "modern-text-embedding",
                "label": "Modern Text Embedding",
                "modern": True  # Both modern AND embedding
            }
        ]
        
        assert validate_model_selection("TEST_PROVIDER", "modern-text-embedding") is True

    def test_validation_with_real_catalog_models(self):
        """Test validation using actual models from the catalog."""
        # Test some real models from different providers
        
        # Modern chat models should pass
        assert validate_model_selection("ANTHROPIC", "claude-3-5-sonnet-latest") is True
        assert validate_model_selection("OPENAI", "o1-mini") is True
        assert validate_model_selection("GOOGLE", "gemini-2.0-flash") is True
        
        # Modern embedding models should pass  
        assert validate_model_selection("OPENAI", "text-embedding-3-large") is True
        assert validate_model_selection("OPENAI", "text-embedding-3-small") is True
        
        # Test with providers that have no modern models
        # Note: These should fail if no models exist for the provider
        assert validate_model_selection("MISTRALAI", "any-model") is False
        assert validate_model_selection("OPENAI_AZURE", "any-model") is False

    def test_multiple_validation_calls(self):
        """Test multiple consecutive validation calls for consistency."""
        # Test the same model multiple times to ensure consistent results
        model_provider = "ANTHROPIC"
        model_name = "claude-3-5-sonnet-latest"
        
        for _ in range(5):
            assert validate_model_selection(model_provider, model_name) is True
        
        # Test invalid model multiple times
        invalid_model = "claude-invalid-model"
        for _ in range(5):
            assert validate_model_selection(model_provider, invalid_model) is False


class TestValidateModelSelectionEdgeCases:
    """Test edge cases for validate_model_selection function."""

    def test_none_parameters(self):
        """Test behavior with None parameters."""
        # These should not crash but return False
        assert validate_model_selection(None, "some-model") is False
        assert validate_model_selection("ANTHROPIC", None) is False
        assert validate_model_selection(None, None) is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_empty_provider_catalog(self, mock_get_models):
        """Test with provider that has no models."""
        mock_get_models.return_value = []
        
        assert validate_model_selection("EMPTY_PROVIDER", "any-model") is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_provider_catalog_with_malformed_data(self, mock_get_models):
        """Test with malformed model data in catalog."""
        # Mock catalog with missing required fields
        mock_get_models.return_value = [
            {"label": "Missing Value Field"},  # No "value" field
            {"value": "missing-label"},        # No "label" field
            {}                                 # Empty dict
        ]
        
        # Should handle malformed data gracefully
        assert validate_model_selection("TEST_PROVIDER", "missing-value") is False
        assert validate_model_selection("TEST_PROVIDER", "missing-label") is False

    @patch('framework.helpers.model_catalog.get_models_for_provider')
    def test_model_with_unexpected_data_types(self, mock_get_models):
        """Test with unexpected data types in model metadata."""
        mock_get_models.return_value = [
            {
                "value": "test-model",
                "label": "Test Model",
                "modern": "true",  # String instead of boolean
            },
            {
                "value": "test-model-2", 
                "label": "Test Model 2",
                "modern": 1,  # Integer instead of boolean
            }
        ]
        
        # Should handle type coercion gracefully
        # Truthy values should be treated as True
        assert validate_model_selection("TEST_PROVIDER", "test-model") is True
        assert validate_model_selection("TEST_PROVIDER", "test-model-2") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
