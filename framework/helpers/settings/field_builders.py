from typing import Any

import models
from framework.helpers.settings.constants import PASSWORD_PLACEHOLDER
from framework.helpers.settings.types import Settings, SettingsField


class FieldBuilder:
    """Builder for creating setting fields."""

    @staticmethod
    def _get_api_key_field(
        settings: Settings, provider: str, title: str
    ) -> SettingsField:
        key = settings["api_keys"].get(provider, models.get_api_key(provider))
        return {
            "id": f"api_key_{provider}",
            "title": title,
            "type": "password",
            "value": (PASSWORD_PLACEHOLDER if key and key != "None" else ""),
        }

    @staticmethod
    def create_api_key_fields(settings: Settings) -> list[SettingsField]:
        """Create API key fields for various model providers."""
        fields: list[SettingsField] = []
        fields.append(FieldBuilder._get_api_key_field(settings, "openai", "OpenAI API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "anthropic", "Anthropic API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "chutes", "Chutes API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "deepseek", "DeepSeek API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "google", "Google API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "groq", "Groq API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "huggingface", "HuggingFace API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "mistralai", "MistralAI API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "openrouter", "OpenRouter API Key"))
        fields.append(FieldBuilder._get_api_key_field(settings, "sambanova", "Sambanova API Key"))
        return fields

    @staticmethod
    def create_model_fields(
        model_type: str,
        settings: Settings,
        model_providers: Any,  # models.ModelProvider
        include_vision: bool = False,
        include_context_length: bool = False,
        include_context_history: bool = False,
        model_params_description: str = ""
    ) -> list[SettingsField]:
        """Create common model configuration fields."""
        fields: list[SettingsField] = []

        fields.append(
            {
                "id": f"{model_type}_model_provider",
                "title": f"{model_type.capitalize()} model provider",
                "description": f"Select provider for {model_type} model used by the framework",
                "type": "select",
                "value": settings[f"{model_type}_model_provider"],
                "options": [{"value": p.name, "label": p.value} for p in model_providers],
            }
        )
        fields.append(
            {
                "id": f"{model_type}_model_name",
                "title": f"{model_type.capitalize()} model name",
                "description": "Exact name of model from selected provider",
                "type": "text",
                "value": settings[f"{model_type}_model_name"],
            }
        )

        if include_context_length:
            fields.append(
                {
                    "id": f"{model_type}_model_ctx_length",
                    "title": f"{model_type.capitalize()} model context length",
                    "description": (
                        "Maximum number of tokens in the context window for LLM. System "
                        "prompt, chat history, RAG and response all count towards this limit."
                    ),
                    "type": "number",
                    "value": settings[f"{model_type}_model_ctx_length"],
                }
            )

        if include_context_history:
            fields.append(
                {
                    "id": f"{model_type}_model_ctx_history",
                    "title": "Context window space for chat history",
                    "description": (
                        "Portion of context window dedicated to chat history visible to the agent. "
                        "Chat history will automatically be optimized to fit. Smaller size will "
                        "result in shorter and more summarized history. The remaining space will "
                        "be used for system prompt, RAG and response."
                    ),
                    "type": "range",
                    "min": 0.01,
                    "max": 1,
                    "step": 0.01,
                    "value": settings[f"{model_type}_model_ctx_history"],
                }
            )

        if include_vision:
            fields.append(
                {
                    "id": f"{model_type}_model_vision",
                    "title": "Supports Vision",
                    "description": (
                        "Models capable of Vision can for example natively see the content of "
                        "image attachments."
                    ),
                    "type": "switch",
                    "value": settings[f"{model_type}_model_vision"],
                }
            )

        # Rate limit fields
        for limit_type in ["requests", "input", "output"]:
            # Only add output limit for chat/util models
            if limit_type == "output" and model_type == "embed":
                continue
            fields.append({
                "id": f"{model_type}_model_rl_{limit_type}",
                "title": f"{limit_type.capitalize()} tokens per minute limit"
                if limit_type != "requests" else f"{limit_type.capitalize()} per minute limit",
                "description": (
                    f"Limits the number of {limit_type} "
                    f"{'tokens ' if limit_type != 'requests' else ''}"
                    f"per minute to the {model_type} model. "
                    "Waits if the limit is exceeded. "
                    "Set to 0 to disable rate limiting."
                ),
                "type": "number",
                "value": settings[f"{model_type}_model_rl_{limit_type}"],
            })

        if model_params_description:
            fields.append(
                {
                    "id": f"{model_type}_model_kwargs",
                    "title": f"{model_type.capitalize()} model additional parameters",
                    "description": model_params_description,
                    "type": "textarea",
                    "value": settings[f"{model_type}_model_kwargs"], # This will be converted later
                }
            )
        return fields
