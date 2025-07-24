"""API handler for getting current active model information."""

import models
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetCurrentModel(ApiHandler):
    """API handler to get information about the currently active model."""

    async def process(self, input_data: Input, request: Request) -> Output:
        """Get current model information.

        Args:
            input_data: Dictionary (unused)
            request: The request object

        Returns:
            Dictionary containing current model information
        """
        try:
            # Get current model settings
            current_provider = models.get_model_provider()
            current_model = models.get_model_name()

            # Get model display name/label
            from framework.helpers.model_catalog import get_models_for_provider

            provider_models = get_models_for_provider(current_provider)

            model_label = current_model
            for model in provider_models:
                if model.get("value") == current_model:
                    model_label = model.get("label", current_model)
                    break

            # Determine model type and capabilities
            model_type = "chat"  # default
            capabilities = []

            # Check if it's a voice model
            from framework.helpers.model_catalog import get_voice_models_for_provider

            voice_models = get_voice_models_for_provider(current_provider)
            if any(m.get("value") == current_model for m in voice_models):
                model_type = "voice"
                capabilities.append("voice")

            # Check if it's a code model
            from framework.helpers.model_catalog import get_code_models_for_provider

            code_models = get_code_models_for_provider(current_provider)
            if any(m.get("value") == current_model for m in code_models):
                model_type = "code"
                capabilities.append("code")

            # Check for vision capability
            vision_enabled = models.get_model_vision()
            if vision_enabled:
                capabilities.append("vision")

            return {
                "provider": current_provider,
                "model_name": current_model,
                "model_label": model_label,
                "model_type": model_type,
                "capabilities": capabilities,
                "display_name": f"{model_label} ({current_provider.upper()})",
            }

        except Exception as e:
            return {
                "error": f"Failed to get current model info: {str(e)}",
                "provider": "unknown",
                "model_name": "unknown",
                "model_label": "Unknown Model",
                "model_type": "chat",
                "capabilities": [],
                "display_name": "Unknown Model",
            }
