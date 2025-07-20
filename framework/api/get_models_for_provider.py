"""API handler for getting models for a specific provider."""

from framework.helpers import model_catalog
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetModelsForProvider(ApiHandler):
    """API handler to get available models for a specific provider."""
    
    async def process(self, input_data: Input, request: Request) -> Output:
        """Get models for the specified provider.
        
        Args:
            input_data: Dictionary containing the provider name
            request: The request object
            
        Returns:
            Dictionary containing the list of models for the provider
        """
        provider = input_data.get("provider", "")
        
        if not provider:
            return {"error": "Provider parameter is required", "models": []}
        
        models = model_catalog.get_models_for_provider(provider)
        
        return {
            "provider": provider,
            "models": models,
            "count": len(models)
        }