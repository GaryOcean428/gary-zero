# Model Catalog Framework Documentation

## Overview

The Gary-Zero framework features a comprehensive model catalog system that prioritizes modern AI models while maintaining backward compatibility. This system supports multiple model types including chat, utility, voice, code, and browser models.

## Architecture

### Model Classification System

Models are classified using a three-tier system:

1. **Modern Models** (`modern: true`) - Released after June 2024
2. **Deprecated Models** (`deprecated: true`) - Released before June 2024
3. **Specialized Models** - Flagged with specific capabilities:
   - `voice: true` - Voice-to-voice capable models
   - `code: true` - Code-specific optimization models

### Model Catalog Structure

The main catalog is located in `framework/helpers/model_catalog.py`:

```python
MODEL_CATALOG: dict[str, list[dict[str, str]]] = {
    "OPENAI": [
        # Modern models listed first
        {"value": "o3", "label": "o3", "modern": True, "release_date": "2025-01-31"},
        {"value": "gpt-4o-realtime-preview", "label": "GPT-4o Realtime Preview", 
         "modern": True, "voice": True, "release_date": "2024-10-01"},
        # Legacy models follow
        {"value": "gpt-4", "label": "GPT-4", "deprecated": True, "release_date": "2023-03-14"},
    ]
}
```

## API Functions

### Core Helper Functions

#### `get_models_for_provider(provider_name: str)`
Returns all models for a provider in catalog order (modern first).

#### `get_modern_models_for_provider(provider_name: str)`
Returns only modern models (post-June 2024) for a provider.

#### `get_deprecated_models_for_provider(provider_name: str)`
Returns only deprecated models (pre-June 2024) for a provider.

#### `get_voice_models_for_provider(provider_name: str)`
Returns voice-capable models for a provider.

#### `get_code_models_for_provider(provider_name: str)`
Returns code-oriented models for a provider.

### Global Functions

#### `get_all_modern_models()`
Returns all modern models across all providers.

#### `get_all_voice_models()`
Returns all voice-capable models across all providers.

#### `get_all_code_models()`
Returns all code-oriented models across all providers.

### Validation Functions

#### `is_model_modern(provider_name: str, model_name: str)`
Checks if a specific model is flagged as modern.

#### `is_model_deprecated(provider_name: str, model_name: str)`
Checks if a specific model is flagged as deprecated.

#### `is_valid_model_for_provider(provider_name: str, model_name: str)`
Validates that a model exists for the given provider.

## API Endpoints

### `/get_models_for_provider`
**POST** endpoint that returns models for a provider, prioritizing modern models.

**Request:**
```json
{"provider": "OPENAI"}
```

**Response:**
```json
{
  "provider": "OPENAI",
  "models": [...],
  "count": 32,
  "modern_count": 22,
  "deprecated_count": 10
}
```

### `/get_voice_models`
**POST** endpoint for voice-capable models.

### `/get_code_models`
**POST** endpoint for code-specific models.

### `/get_current_model`
**POST** endpoint returning current active model information with capabilities.

## Settings Integration

### Model Types Supported

The settings system supports these model configurations:

1. **Chat Model** - Primary conversational model
2. **Utility Model** - Lightweight tasks (summarization, etc.)
3. **Embedding Model** - Vector/semantic search
4. **Browser Model** - Web automation with vision
5. **Voice Model** - Speech-to-speech interactions
6. **Code Model** - Development and programming tasks

### Default Modern Models

```python
DEFAULT_SETTINGS = {
    "chat_model_name": "claude-sonnet-4-20250514",      # Claude 4 Sonnet
    "util_model_name": "gpt-4.1-mini",                  # GPT-4.1 Mini
    "embed_model_name": "gpt-4.1-embeddings",           # GPT-4.1 Embeddings
    "browser_model_name": "claude-sonnet-4-20250514",   # Claude 4 Sonnet
    "voice_model_name": "gpt-4o-realtime-preview",      # OpenAI Realtime
    "code_model_name": "claude-code",                    # Claude Code
}
```

### Voice Model Configuration

Voice models support additional settings:

- **Architecture**: `speech_to_speech` (realtime) or `chained` (transcribe → LLM → TTS)
- **Transport**: `websocket` or `webrtc` for realtime connections

## UI Integration

### Model Prioritization

The field builder automatically prioritizes modern models:

```python
# In field_builders.py
provider_models = get_modern_models_for_provider(current_provider)
if not provider_models:
    provider_models = get_models_for_provider(current_provider)  # Fallback
```

### Dynamic Model Indicator

The UI displays current model information with capabilities:

```javascript
// Shows current model with real-time updates
x-text="currentModel.model_label || 'Loading...'"
```

### Settings Sections

Voice and code models have dedicated UI sections:

- **Voice Model Section**: Architecture and transport configuration
- **Code Model Section**: Development-specific model selection

## Adding New Models

### Step 1: Add to Catalog

Add new models to the appropriate provider section in `MODEL_CATALOG`:

```python
"PROVIDER_NAME": [
    # Add at top for modern models
    {"value": "new-model-v2", "label": "New Model v2", 
     "modern": True, "release_date": "2024-12-01"},
    # Or add special capabilities
    {"value": "new-voice-model", "label": "New Voice Model", 
     "modern": True, "voice": True, "release_date": "2024-12-01"},
]
```

### Step 2: Update Tests

Add test cases to `test_model_modernization.py`:

```python
test_cases = [
    ("PROVIDER_NAME", "new-model-v2", "2024-12-01"),
]
```

### Step 3: Verify Integration

Run tests to ensure proper integration:

```bash
python test_model_modernization.py
```

## Best Practices

### Model Flagging

- **Always flag modern models** with `modern: true`
- **Always flag deprecated models** with `deprecated: true`
- **Never mark a model as both modern and deprecated**
- **Include accurate release dates** for all models
- **Use specific capability flags** (`voice`, `code`) when applicable

### Ordering

- **Modern models first** in each provider section
- **Most capable models first** within modern section
- **Deprecated models at end** of each provider section

### Naming

- **Consistent labeling** with official model names
- **Clear version indicators** when multiple versions exist
- **Provider suffixes** for clarity in cross-provider contexts

## Migration Guide

### From Legacy Models

When updating from deprecated models:

1. **Check for modern equivalent**: Use `get_modern_models_for_provider()`
2. **Update configuration gradually**: Use fallback mechanism
3. **Test functionality**: Ensure feature parity
4. **Update documentation**: Reflect new model choices

### Configuration Updates

Existing configurations automatically benefit from modern model prioritization without breaking changes.

## Troubleshooting

### Common Issues

1. **Empty model lists**: Check provider name spelling
2. **Legacy models appearing**: Verify modern models exist for provider
3. **Missing capabilities**: Ensure proper flags in catalog
4. **API errors**: Validate provider and model names

### Debug Commands

```python
# Test provider models
from framework.helpers.model_catalog import *
models = get_modern_models_for_provider("OPENAI")
print(f"Found {len(models)} modern OpenAI models")

# Verify model existence
is_valid = is_valid_model_for_provider("OPENAI", "o3")
print(f"Model valid: {is_valid}")
```

## Future Enhancements

### Planned Features

- **Dynamic model discovery** from provider APIs
- **Usage analytics** for model selection optimization
- **Automatic deprecation warnings** for old models
- **Model performance benchmarking** integration

### Extension Points

The system is designed for extensibility:

- **Custom capability flags** for new model types
- **Provider-specific configurations** for unique features
- **Integration hooks** for external model registries
- **Validation plugins** for model verification

---

This documentation provides comprehensive guidance for working with the modern model catalog system in Gary-Zero. For implementation details, refer to the source code in `framework/helpers/model_catalog.py` and related modules.