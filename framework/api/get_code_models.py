"""API handler for getting code-capable models."""

from framework.helpers import model_catalog
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetCodeModels(ApiHandler):
    """API handler to get available code-capable models."""

    async def process(self, input_data: Input, request: Request) -> Output:
        """Get code-capable models.
        
        Args:
            input_data: Dictionary (may contain optional provider filter)
            request: The request object
            
        Returns:
            Dictionary containing the list of code-capable models
        """
        provider = input_data.get("provider", "")

        if provider:
            # Get code models for specific provider
            models = model_catalog.get_code_models_for_provider(provider)
        else:
            # Get all code models across all providers
            models = model_catalog.get_all_code_models()

        return {
            "provider": provider or "all",
            "models": models,
            "count": len(models)
        }