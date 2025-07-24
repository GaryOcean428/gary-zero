# AI Models - Gary-Zero Model Catalog


## Overview

Gary-Zero's AI model catalog has undergone comprehensive modernization to provide users with the latest, most capable AI models while maintaining backward compatibility and clear migration paths.


## Current Model Status (January 2025)

### 📊 Model Statistics

- **Total Modern Models**: 93 active models
- **Deprecated Models Purged**: 45 legacy models removed
- **Supported Providers**: 11 AI providers
- **Specialized Categories**: Voice (5), Code (3), Vision-capable models


## Modern Model Allow-List

### 🤖 OpenAI Models (22 Modern)

**Primary Models:**
- `o3` - Latest reasoning model (January 2025)
- `o1-pro` - Advanced reasoning model
- `o1-mini` - Efficient reasoning model
- `gpt-4.1-mini` - Fast general-purpose model
- `gpt-4o-realtime-preview` - Real-time voice model

**Specialized Models:**
- `text-embedding-3-large` - Advanced embedding model
- `text-embedding-3-small` - Efficient embedding model
- `dall-e-3` - Image generation model

### 🧠 Anthropic Models (9 Modern)

**Claude 4 Series:**
- `claude-sonnet-4-20250514` - Latest Claude 4 Sonnet
- `claude-code` - Specialized code model
- `claude-4-haiku-20250514` - Fast Claude 4 model

**Claude 3.5 Series:**
- `claude-3-5-sonnet` - Claude 3.5 Sonnet
- `claude-3-5-haiku` - Claude 3.5 Haiku

### 🔍 Google Models (10 Modern)

**Gemini 2.0 Series:**
- `gemini-2.0-flash` - Latest Gemini flash model
- `gemini-2.0-pro` - Latest Gemini pro model

**Gemini 1.5 Pro Series:**
- `gemini-1.5-pro-001` - Production Gemini 1.5 Pro
- `gemini-1.5-flash-001` - Production Gemini 1.5 Flash

### ⚡ XAI Models (8 Modern)

**Grok Series:**
- `grok-2-latest` - Latest Grok model
- `grok-2-1212` - Grok 2 December release
- `grok-beta` - Beta Grok model

### 🔮 Perplexity Models (5 Modern)

- `llama-3.1-sonar-large-128k-online` - Large context online model
- `llama-3.1-sonar-small-128k-online` - Efficient online model
- `llama-3.1-sonar-huge-128k-online` - Maximum capability online model

### 🧮 DeepSeek Models (3 Modern)

- `deepseek-chat` - General conversation model
- `deepseek-coder` - Specialized code model

### 🦾 Meta Models (5 Modern)

**Llama 3 Series:**
- `llama-3.2-90b-vision-instruct` - Vision-capable Llama
- `llama-3.1-405b-instruct` - Largest Llama model
- `llama-3.1-70b-instruct` - High-performance Llama


## Release Timeline

### January 2025 - Current

- **Model Catalog Modernization**: Complete overhaul prioritizing post-June 2024 models
- **Legacy Model Purge**: 45 deprecated models removed from active catalog
- **Enhanced Categorization**: Voice, code, and vision-capable models properly categorized

### December 2024

- **OpenAI o3 Integration**: Latest reasoning model added
- **Claude 4 Support**: Next-generation Claude models integrated
- **Gemini 2.0 Support**: Google's latest models added

### June 2024 - Modernization Cutoff

Models released before June 2024 are considered legacy and have been deprecated in favor of newer, more capable alternatives.


## Deprecated Models (Legacy)

The following 45 models have been purged from the active catalog but remain accessible for backward compatibility:

### OpenAI Legacy (10 models)

- `gpt-4` → **Upgrade to**: `o3`
- `gpt-3.5-turbo` → **Upgrade to**: `gpt-4.1-mini`
- `text-embedding-ada-002` → **Upgrade to**: `text-embedding-3-large`

### Anthropic Legacy (6 models)

- `claude-2.0` → **Upgrade to**: `claude-sonnet-4-20250514`
- `claude-instant-1.2` → **Upgrade to**: `claude-4-haiku-20250514`

### Google Legacy (6 models)

- `gemini-1.5-pro` → **Upgrade to**: `gemini-2.0-flash`
- `text-bison-001` → **Upgrade to**: `gemini-2.0-pro`

### Other Providers (23 models)

Various legacy models across Groq, MistralAI, HuggingFace, Ollama, and other providers.


## Migration Guide

### Automatic Migration

Gary-Zero automatically handles migration for most scenarios:

1. **Intelligent Fallback**: Deprecated models automatically fall back to modern equivalents
2. **Settings Migration**: User configurations are automatically updated to modern models
3. **Backward Compatibility**: Existing configurations continue to work during transition

### Manual Migration Steps

#### 1. Update Default Models

```bash
# Check current model configuration
python -c "from framework.helpers.settings import get_setting; print(get_setting('chat_model_name'))"

# Update to modern models via UI Settings → Agent Configuration
```

#### 2. API Integration Updates

```python
# Old approach (deprecated)
model = "gpt-4"

# New approach (modern)
from framework.helpers.model_catalog import get_recommended_model_for_provider
model = get_recommended_model_for_provider("OPENAI")  # Returns "o3"
```

#### 3. Environment Variable Updates

```bash
# Update environment variables to use modern models
export CHAT_MODEL_NAME="claude-sonnet-4-20250514"
export UTILITY_MODEL_NAME="gpt-4.1-mini"
export EMBEDDING_MODEL_NAME="text-embedding-3-large"
```


## Model Categories

### 🎤 Voice Models (5 total)

Models with real-time voice capabilities:
- `gpt-4o-realtime-preview` (OpenAI)
- `gemini-2.0-flash` (Google)
- Additional voice-capable models across providers

### 💻 Code Models (3 total)

Specialized for programming tasks:
- `claude-code` (Anthropic)
- `deepseek-coder` (DeepSeek)
- Code-optimized variants

### 👁️ Vision Models

Models with image understanding capabilities:
- `claude-sonnet-4-20250514` (Vision-capable)
- `gpt-4.1-mini` (Vision-capable)
- `llama-3.2-90b-vision-instruct` (Meta)


## Provider Configuration

### API Key Requirements

Each provider requires appropriate API keys configured via environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Google
export GOOGLE_API_KEY="your-google-key"

# See CREDENTIALS_MANAGEMENT.md for complete list
```

### Rate Limits and Quotas

- **OpenAI**: Tier-based rate limits based on API usage
- **Anthropic**: Model-specific rate limits and context windows
- **Google**: Daily quotas and per-minute limits
- **XAI**: Beta access limitations


## Troubleshooting

### Common Issues

#### Model Not Available

```
Error: Model 'gpt-4' not found in catalog
```

**Solution**: Update to modern equivalent (`o3`) or enable legacy model support.

#### Authentication Failures

```
Error: Invalid API key for provider
```

**Solution**: Verify API keys in Settings → Authentication or environment variables.

#### Rate Limit Exceeded

```
Error: Rate limit exceeded for model
```

**Solution**: Switch to alternative model or implement request throttling.

### Model Validation

```python
# Validate model availability
from framework.helpers.model_catalog import is_model_modern
print(is_model_modern("OPENAI", "o3"))  # True
print(is_model_modern("OPENAI", "gpt-4"))  # False
```


## Future Roadmap

### Q1 2025

- Additional Gemini 2.0 model variants
- Enhanced voice model support
- Improved code model capabilities

### Q2 2025

- Complete legacy model removal (Phase 2)
- New provider integrations
- Advanced model routing capabilities

### Q3 2025

- Model performance analytics
- Usage optimization recommendations
- Custom model fine-tuning support


## Related Documentation

- [DEPRECATION_STRATEGY.md](../DEPRECATION_STRATEGY.md) - Detailed deprecation timeline
- [MODEL_MODERNIZATION_AUDIT_REPORT.md](../MODEL_MODERNIZATION_AUDIT_REPORT.md) - Technical audit results
- [CREDENTIALS_MANAGEMENT.md](../CREDENTIALS_MANAGEMENT.md) - Authentication setup
- [Settings Documentation](../docs/usage.md) - UI configuration guide

---

**Last Updated**: January 2025
**Version**: 1.0
**Status**: Production Ready
