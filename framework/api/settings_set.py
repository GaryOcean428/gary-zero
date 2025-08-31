from flask import abort

from framework.helpers import settings
from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.model_catalog import validate_model_selection


class SetSettings(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        """Process a settings update request.

        This handler validates the selected model names against the provider
        catalogue and applies the new settings. Any validation failures
        return a 400 response with detailed error information instead of
        propagating exceptions and causing a 500 response. Unexpected
        exceptions are caught and rethrown to the top-level handler so
        the API error wrapper can format them appropriately.

        Args:
            input_data: The posted settings payload.
            request: The Flask request object.

        Returns:
            A dictionary containing the updated settings on success.
        """
        try:
            # Validate model selections before processing
            validation_errors = []

            # Model validation pairs - (provider_field, model_field, description)
            model_fields = [
                ("chat_model_provider", "chat_model_name", "Chat model"),
                ("util_model_provider", "util_model_name", "Utility model"),
                ("embed_model_provider", "embed_model_name", "Embedding model"),
                ("browser_model_provider", "browser_model_name", "Browser model"),
                ("coding_agent_provider", "coding_agent_name", "Coding agent model"),
                (
                    "supervisor_agent_provider",
                    "supervisor_agent_name",
                    "Supervisor agent model",
                ),
            ]

            # Extract settings to validate
            try:
                temp_settings = settings.convert_in(input_data)
            except Exception as e:
                # If settings conversion fails, return a validation error
                abort(
                    400,
                    description={
                        "error": "Invalid settings format",
                        "message": f"Failed to parse settings: {e}",
                    },
                )
                return {}  # abort will raise

            # Validate each selected model
            for provider_field, model_field, description in model_fields:
                provider = temp_settings.get(provider_field)
                model = temp_settings.get(model_field)

                if provider and model:
                    if not validate_model_selection(provider, model):
                        validation_errors.append(
                            f"{description} '{model}' from provider '{provider}' is not valid. "
                            "Only modern models (post-June 2024) or embedding models are allowed."
                        )

            # Return validation errors with 400 status if any found
            if validation_errors:
                abort(
                    400,
                    description={
                        "error": "Model validation failed",
                        "message": "One or more selected models are not allowed",
                        "validation_errors": validation_errors,
                        "help": "Please select modern models (released after June 2024) or embedding models",
                    },
                )
                return {}

            # Proceed with normal settings processing if validation passes
            settings_data = settings.convert_in(input_data)
            settings.set_settings(settings_data)
            return {"settings": settings_data}
        except Exception:
            # Re-raise exceptions so ApiHandler can handle them and return 500
            raise
