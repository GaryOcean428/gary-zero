"""API handler for getting voice-capable models."""

from framework.helpers import model_catalog
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetVoiceModels(ApiHandler):
    """API handler to get available voice-capable models."""

    async def process(self, input_data: Input, request: Request) -> Output:
        """Get voice-capable models.

        Args:
            input_data: Dictionary (may contain optional provider filter)
            request: The request object

        Returns:
            Dictionary containing the list of voice-capable models
        """
        provider = input_data.get("provider", "")

        if provider:
            # Get voice models for specific provider
            models = model_catalog.get_voice_models_for_provider(provider)
        else:
            # Get all voice models across all providers
            models = model_catalog.get_all_voice_models()

        return {"provider": provider or "all", "models": models, "count": len(models)}
