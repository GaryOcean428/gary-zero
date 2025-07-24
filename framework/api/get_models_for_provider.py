"""API handler for getting models for a specific provider."""

from framework.helpers import model_catalog
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetModelsForProvider(ApiHandler):
    """API handler to get available models for a specific provider."""

    async def process(self, input_data: Input, request: Request) -> Output:
        """Get models for the specified provider, prioritizing modern models.

        Args:
            input_data: Dictionary containing the provider name
            request: The request object

        Returns:
            Dictionary containing the list of models for the provider
        """
        provider = input_data.get("provider", "")

        if not provider:
            return {"error": "Provider parameter is required", "models": []}

        # Prioritize modern models first, fallback to all models if none available
        models = model_catalog.get_modern_models_for_provider(provider)
        if not models:
            models = model_catalog.get_models_for_provider(provider)

        return {
            "provider": provider,
            "models": models,
            "count": len(models),
            "modern_count": len(model_catalog.get_modern_models_for_provider(provider)),
            "deprecated_count": len(
                model_catalog.get_deprecated_models_for_provider(provider)
            ),
        }
