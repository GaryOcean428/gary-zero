"""API handler for getting model parameters for automatic configuration."""

from framework.helpers import model_parameters
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetModelParameters(ApiHandler):
    """API handler to get parameters for a specific model."""
    
    async def process(self, input_data: Input, request: Request) -> Output:
        """Get parameters for the specified model.
        
        Args:
            input_data: Dictionary containing the provider and model name
            request: The request object
            
        Returns:
            Dictionary containing the model parameters
        """
        provider = input_data.get("provider", "")
        model_name = input_data.get("model_name", "")
        
        if not provider or not model_name:
            return {
                "error": "Both provider and model_name parameters are required",
                "parameters": {}
            }
        
        parameters = model_parameters.get_model_parameters(provider, model_name)
        has_specific_params = model_parameters.has_model_parameters(provider, model_name)
        
        return {
            "provider": provider,
            "model_name": model_name,
            "parameters": parameters,
            "has_specific_params": has_specific_params
        }