"""
Tests for model modernization functionality.

This module tests the updated model catalog and settings to ensure:
1. Modern models are preferred by default
2. Voice and code model helper functions work correctly
3. New voice and code model sections are properly configured
"""

from unittest.mock import Mock

from framework.helpers.model_catalog import (
    get_code_models_for_provider,
    get_deprecated_models_for_provider,
    get_modern_models_for_provider,
    get_voice_models_for_provider,
    is_model_deprecated,
    is_model_modern,
)


class TestModelCatalogModernization:
    """Test model catalog modernization features."""

    def test_modern_models_priority(self):
        """Test that modern models are returned correctly."""
        # Test with OPENAI which has many modern models
        modern_openai = get_modern_models_for_provider("OPENAI")
        assert len(modern_openai) > 0

        # First model should be o3 (most recent)
        assert modern_openai[0]["value"] == "o3"
        assert modern_openai[0]["modern"] is True

        # All returned models should be modern
        for model in modern_openai:
            assert model.get("modern", False) is True

    def test_deprecated_models_separation(self):
        """Test that deprecated models are correctly identified."""
        # Test with OPENAI which has deprecated models
        deprecated_openai = get_deprecated_models_for_provider("OPENAI")
        assert len(deprecated_openai) > 0

        # Should include models like gpt-4, gpt-3.5-turbo
        deprecated_values = [m["value"] for m in deprecated_openai]
        assert "gpt-4" in deprecated_values
        assert "gpt-3.5-turbo" in deprecated_values

        # All returned models should be deprecated
        for model in deprecated_openai:
            assert model.get("deprecated", False) is True

    def test_voice_models_identification(self):
        """Test that voice models are correctly identified."""
        # Test OPENAI voice models
        voice_openai = get_voice_models_for_provider("OPENAI")
        assert len(voice_openai) > 0

        # Should include realtime models
        voice_values = [m["value"] for m in voice_openai]
        assert "gpt-4o-realtime-preview" in voice_values
        assert "gpt-4o-audio" in voice_values

        # All returned models should have voice capability
        for model in voice_openai:
            assert model.get("voice", False) is True

        # Test GOOGLE voice models
        voice_google = get_voice_models_for_provider("GOOGLE")
        voice_values_google = [m["value"] for m in voice_google]
        assert "gemini-2.5-flash-preview-tts" in voice_values_google
        assert "gemini-2.5-pro-preview-tts" in voice_values_google

    def test_code_models_identification(self):
        """Test that code models are correctly identified."""
        # Test ANTHROPIC code models
        code_anthropic = get_code_models_for_provider("ANTHROPIC")
        assert len(code_anthropic) > 0

        code_values = [m["value"] for m in code_anthropic]
        assert "claude-code" in code_values

        # Test DEEPSEEK code models
        code_deepseek = get_code_models_for_provider("DEEPSEEK")
        assert len(code_deepseek) > 0

        code_values_deepseek = [m["value"] for m in code_deepseek]
        assert "deepseek-coder" in code_values_deepseek

    def test_model_status_helpers(self):
        """Test helper functions for checking model status."""
        # Test modern model detection
        assert is_model_modern("OPENAI", "o3") is True
        assert is_model_modern("ANTHROPIC", "claude-3-5-sonnet-20241022") is True

        # Test deprecated model detection
        assert is_model_deprecated("OPENAI", "gpt-4") is True
        assert is_model_deprecated("OPENAI", "gpt-3.5-turbo") is True

        # Test that modern models are not deprecated
        assert is_model_deprecated("OPENAI", "o3") is False
        assert is_model_deprecated("ANTHROPIC", "claude-3-5-sonnet-20241022") is False

    def test_fallback_behavior(self):
        """Test fallback behavior for providers without modern models."""
        # Test with a provider that might not have modern models
        modern_other = get_modern_models_for_provider("OTHER")
        # OTHER provider has no modern models, should return empty list
        assert len(modern_other) == 0

    def test_nonexistent_provider(self):
        """Test behavior with nonexistent provider."""
        modern_fake = get_modern_models_for_provider("NONEXISTENT")
        assert len(modern_fake) == 0

        voice_fake = get_voice_models_for_provider("NONEXISTENT")
        assert len(voice_fake) == 0

        code_fake = get_code_models_for_provider("NONEXISTENT")
        assert len(code_fake) == 0


class TestFieldBuilderModernization:
    """Test field builder uses modern models by default."""

    def test_field_builder_modern_preference(self):
        """Test that field builder prefers modern models."""
        from framework.helpers.settings.field_builders import FieldBuilder

        # Mock models module
        mock_model_provider = Mock()
        mock_model_provider.OPENAI = "OPENAI"

        # Mock settings
        mock_settings = {
            "chat_model_provider": "OPENAI",
            "chat_model_name": "gpt-4o",
            "chat_model_ctx_length": 4096,
            "chat_model_ctx_history": 0.5,
            "chat_model_vision": True,
            "chat_model_rl_requests": 0,
            "chat_model_rl_input": 0,
            "chat_model_rl_output": 0,
            "chat_model_kwargs": {},
        }

        # Create fields
        fields = FieldBuilder.create_model_fields(
            "chat",
            mock_settings,
            [mock_model_provider.OPENAI],  # Pass as list to avoid iteration error
            include_vision=True,
            include_context_length=True,
            include_context_history=True,
        )

        # Find model name field
        model_name_field = None
        for field in fields:
            if field["id"] == "chat_model_name":
                model_name_field = field
                break

        assert model_name_field is not None
        assert len(model_name_field["options"]) > 0

        # First option should be a modern model (o3)
        first_option = model_name_field["options"][0]
        assert first_option["value"] == "o3"


class TestNewSections:
    """Test new voice and code model sections."""

    def test_voice_model_section_structure(self):
        """Test voice model section has correct structure."""
        from framework.helpers.settings.section_builders import SectionBuilder

        # Mock settings
        mock_settings = {
            "voice_model_provider": "OPENAI",
            "voice_model_name": "gpt-4o-realtime-preview",
            "voice_architecture": "speech_to_speech",
            "voice_transport": "websocket",
            "voice_model_rl_requests": 0,
            "voice_model_rl_input": 0,
            "voice_model_rl_output": 0,
            "voice_model_kwargs": {},
        }

        section = SectionBuilder.build_voice_model_section(mock_settings)

        assert section["id"] == "voice_model"
        assert section["title"] == "Voice Model"
        assert section["tab"] == "agent"
        assert len(section["fields"]) > 0

        # Check for voice-specific fields
        field_ids = [field["id"] for field in section["fields"]]
        assert "voice_architecture" in field_ids
        assert "voice_transport" in field_ids
        assert "voice_model_provider" in field_ids
        assert "voice_model_name" in field_ids

    def test_code_model_section_structure(self):
        """Test code model section has correct structure."""
        from framework.helpers.settings.section_builders import SectionBuilder

        # Mock settings
        mock_settings = {
            "code_model_provider": "ANTHROPIC",
            "code_model_name": "claude-code",
            "code_model_rl_requests": 0,
            "code_model_rl_input": 0,
            "code_model_rl_output": 0,
            "code_model_kwargs": {},
        }

        section = SectionBuilder.build_code_model_section(mock_settings)

        assert section["id"] == "code_model"
        assert section["title"] == "Code Model"
        assert section["tab"] == "agent"
        assert len(section["fields"]) > 0

        # Check for standard model fields
        field_ids = [field["id"] for field in section["fields"]]
        assert "code_model_provider" in field_ids
        assert "code_model_name" in field_ids

    def test_voice_section_options(self):
        """Test voice section has correct options."""
        from framework.helpers.settings.section_builders import SectionBuilder

        mock_settings = {
            "voice_model_provider": "OPENAI",
            "voice_model_name": "gpt-4o-realtime-preview",
            "voice_architecture": "speech_to_speech",
            "voice_transport": "websocket",
            "voice_model_rl_requests": 0,
            "voice_model_rl_input": 0,
            "voice_model_rl_output": 0,
            "voice_model_kwargs": {},
        }

        section = SectionBuilder.build_voice_model_section(mock_settings)

        # Find architecture field
        arch_field = None
        transport_field = None
        for field in section["fields"]:
            if field["id"] == "voice_architecture":
                arch_field = field
            elif field["id"] == "voice_transport":
                transport_field = field

        assert arch_field is not None
        assert len(arch_field["options"]) == 2
        arch_values = [opt["value"] for opt in arch_field["options"]]
        assert "speech_to_speech" in arch_values
        assert "chained" in arch_values

        assert transport_field is not None
        assert len(transport_field["options"]) == 2
        transport_values = [opt["value"] for opt in transport_field["options"]]
        assert "websocket" in transport_values
        assert "webrtc" in transport_values
