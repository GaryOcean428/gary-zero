from framework.helpers import settings
from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.model_catalog import validate_model_selection
from flask import abort


class SetSettings(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        # Validate model selections before processing
        validation_errors = []
        
        # Model validation pairs - (provider_field, model_field, description)
        model_fields = [
            ('chat_model_provider', 'chat_model_name', 'Chat model'),
            ('util_model_provider', 'util_model_name', 'Utility model'), 
            ('embed_model_provider', 'embed_model_name', 'Embedding model'),
            ('browser_model_provider', 'browser_model_name', 'Browser model'),
            ('coding_agent_provider', 'coding_agent_name', 'Coding agent model'),
            ('supervisor_agent_provider', 'supervisor_agent_name', 'Supervisor agent model')
        ]
        
        # Extract settings to validate
        temp_settings = settings.convert_in(input_data)
        
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
            abort(400, description={
                "error": "Model validation failed",
                "message": "One or more selected models are not allowed",
                "validation_errors": validation_errors,
                "help": "Please select modern models (released after June 2024) or embedding models"
            })
        
        # Proceed with normal settings processing if validation passes
        settings_data = settings.convert_in(input_data)
        settings.set_settings(settings_data)
        return {"settings": settings_data}
