"""
Unit tests for AI model registry.
"""

from models.registry import ModelCapability, ModelConfig, ModelProvider, ModelRegistry


class TestModelRegistry:
    """Test cases for the ModelRegistry class."""

    def test_model_registration(self):
        """Test model registration."""
        registry = ModelRegistry()

        # Clear existing models for clean test
        registry.models.clear()

        test_model = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="test-model",
            display_name="Test Model",
            max_tokens=1000,
            context_window=4000,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
            capabilities=[ModelCapability.TEXT_GENERATION],
            recommended_for=["testing"]
        )

        registry.register_model(test_model)

        assert "test-model" in registry.models
        assert registry.get_model("test-model") == test_model

    def test_list_models_by_provider(self, model_registry):
        """Test listing models by provider."""
        openai_models = model_registry.list_models(ModelProvider.OPENAI)
        anthropic_models = model_registry.list_models(ModelProvider.ANTHROPIC)

        assert len(openai_models) > 0
        assert len(anthropic_models) > 0
        assert all(m.provider == ModelProvider.OPENAI for m in openai_models)
        assert all(m.provider == ModelProvider.ANTHROPIC for m in anthropic_models)

    def test_get_models_by_capability(self, model_registry):
        """Test getting models by capability."""
        coding_models = model_registry.get_models_by_capability(ModelCapability.CODE_GENERATION)
        vision_models = model_registry.get_models_by_capability(ModelCapability.VISION)

        assert len(coding_models) > 0
        assert len(vision_models) > 0
        assert all(ModelCapability.CODE_GENERATION in m.capabilities for m in coding_models)
        assert all(ModelCapability.VISION in m.capabilities for m in vision_models)

    def test_get_recommended_model(self, model_registry):
        """Test getting recommended model for use case."""
        coding_model = model_registry.get_recommended_model("coding")
        fast_model = model_registry.get_recommended_model("fast")

        assert coding_model is not None
        assert "coding" in coding_model.recommended_for

        if fast_model:
            assert "fast" in fast_model.recommended_for

    def test_cost_estimation(self, model_registry):
        """Test cost estimation."""
        model_name = "gpt-4o"
        cost = model_registry.get_cost_estimate(model_name, 1000, 500)

        assert cost > 0

        # Test with unknown model
        cost_unknown = model_registry.get_cost_estimate("unknown-model", 1000, 500)
        assert cost_unknown == 0.0

    def test_usage_stats_update(self, model_registry):
        """Test usage statistics tracking."""
        model_name = "gpt-4o"

        # Update usage stats
        model_registry.update_usage_stats(
            model_name=model_name,
            tokens_used=1000,
            response_time=2.5,
            success=True,
            cost=0.025
        )

        stats = model_registry.get_usage_stats(model_name)
        assert stats is not None
        assert stats.total_requests >= 1
        assert stats.total_tokens >= 1000
        assert stats.total_cost >= 0.025
        assert stats.success_rate > 0
        assert stats.last_used is not None

    def test_model_availability(self, model_registry):
        """Test model availability checks."""
        available_models = [m for m in model_registry.list_models() if m.is_available]
        unavailable_models = [m for m in model_registry.list_models() if not m.is_available]

        assert len(available_models) > 0
        # Most models should be available by default

    def test_rate_limits(self, model_registry):
        """Test rate limit information."""
        models_with_limits = [
            m for m in model_registry.list_models()
            if m.rate_limit_rpm is not None or m.rate_limit_tpm is not None
        ]

        assert len(models_with_limits) > 0

        for model in models_with_limits:
            if model.rate_limit_rpm:
                assert model.rate_limit_rpm > 0
            if model.rate_limit_tpm:
                assert model.rate_limit_tpm > 0
