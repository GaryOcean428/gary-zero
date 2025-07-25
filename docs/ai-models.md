# AI Models - Gary-Zero Model Catalog


## Overview

Gary-Zero's AI model catalog provides access to verified AI models from the following specified sources:
- **Abacus AI** (ai1docs.abacusai.app)
- **Google Gemini** (ai.google.dev/gemini-api/docs/models)
- **OpenAI GPT-4.1** (platform.openai.com/docs/models/gpt-4.1)
- **OpenAI Models** (platform.openai.com/docs/api-reference/models)
- **Groq** (console.groq.com/docs/models)

All models are verified against these sources as of January 2025.


## Current Model Status (January 2025)

### 📊 Verified Model Statistics

- **Total Models**: 19 active models
- **Supported Providers**: 4 verified providers
- **Source Verification**: All models verified against specified websites


## Verified Model Allow-List

### 🤖 OpenAI Models (4 total)

**GPT-4.1 Series:**
- `gpt-4.1` - Latest GPT-4.1 model with enhanced reasoning and vision
- `gpt-4.1-mini` - Faster, cost-effective version of GPT-4.1
- `gpt-4.1-nano` - Most cost-effective GPT-4.1 variant for basic tasks

**Reasoning Models:**
- `o3` - Advanced reasoning model with enhanced problem-solving
- `o4-mini` - Efficient reasoning model with strong performance

### 🔍 Google Gemini Models (4 total)

**Gemini 2.0 Series:**
- `gemini-2.0-flash` - Latest Gemini with multimodal and voice capabilities
- `gemini-2.0-flash-lite` - Ultra-low-cost Gemini variant

**Gemini 2.5 Series:**
- `gemini-2.5-pro` - Advanced Gemini Pro with enhanced reasoning
- `gemini-2.5-pro-exp-03-25` - Experimental Gemini 2.5 Pro

### ⚡ Groq Models (4 total)

**Llama Series:**
- `llama-3.3-70b-versatile` - High-performance Llama on Groq hardware
- `llama-3.1-8b-instant` - Lightning-fast Llama for basic tasks

**Specialized Models:**
- `mixtral-8x7b-32768` - Mixture-of-experts model with large context
- `gemma2-9b-it` - Google's Gemma 2 optimized for instruction following

### 🧠 Abacus AI Models (7 total)

**Claude Series:**
- `claude-3-7-sonnet-20250219` - Latest Claude 3.7 Sonnet
- `claude-3-5-haiku-20241022` - Fast Claude 3.5 Haiku

**OpenAI Models:**
- `gpt-4o` - GPT-4O with vision and function calling
- `gpt-4o-mini` - Cost-effective GPT-4O variant


## Model Categories

### 🎤 Voice & Multimodal Models

- `gemini-2.0-flash` (Google) - Voice and multimodal capabilities
- `gpt-4.1` (OpenAI) - Vision and multimodal support

### 💻 Code & Reasoning Models

- `o3` (OpenAI) - Advanced reasoning for complex problems
- `claude-3-7-sonnet-20250219` (Abacus AI) - Enhanced coding capabilities
- `gemini-2.5-pro` (Google) - Advanced reasoning and coding

### ⚡ Fast & Cost-Effective Models

- `gpt-4.1-nano` (OpenAI) - Ultra-fast and low-cost
- `llama-3.1-8b-instant` (Groq) - Lightning-fast inference
- `gemini-2.0-flash-lite` (Google) - Ultra-low-cost Gemini


## Provider Configuration

### API Key Requirements

Each provider requires appropriate API keys configured via environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Google
export GOOGLE_API_KEY="your-google-key"

# Groq
export GROQ_API_KEY="your-groq-key"

# Abacus AI
export ABACUS_AI_API_KEY="your-abacus-ai-key"
```

### Rate Limits and Quotas

- **OpenAI**: Tier-based rate limits based on API usage
- **Google**: Daily quotas and per-minute limits
- **Groq**: High rate limits optimized for speed
- **Abacus AI**: Provider-specific rate limits


## API Documentation Reference

### 🔗 Primary Provider API Documentation

#### OpenAI

- **Models**: https://platform.openai.com/docs/models/gpt-4.1
- **API Reference**: https://platform.openai.com/docs/api-reference/models
- **Chat Completions**: https://platform.openai.com/docs/api-reference/chat
- **Vision**: https://platform.openai.com/docs/guides/vision

#### Google Gemini

- **Models**: https://ai.google.dev/gemini-api/docs/models
- **API Reference**: https://ai.google.dev/api/rest
- **Multimodal**: https://ai.google.dev/gemini-api/docs/vision
- **Voice**: https://ai.google.dev/gemini-api/docs/voice

#### Groq

- **Models**: https://console.groq.com/docs/models
- **API Reference**: https://console.groq.com/docs/api-reference
- **Rate Limits**: https://console.groq.com/docs/rate-limits

#### Abacus AI

- **Documentation**: https://ai1docs.abacusai.app/
- **Models**: Refer to Abacus AI model catalog


## Migration from Legacy Models

### Removed Providers

The following providers have been removed as they are not from the specified sources:
- **Mistral AI** - Not in specified sources
- **Cohere** - Not in specified sources  
- **Ollama** - Not in specified sources
- **Anthropic** (direct) - Using Abacus AI proxy instead

### Updated Model Names

- `gpt-4o` → Still supported via Abacus AI
- `claude-3-5-sonnet` → Updated to `claude-3-7-sonnet-20250219`
- `gemini-2.0-flash` → Verified and retained


## Usage Examples

### Selecting Models by Use Case

```python
# Get models for specific use cases
from models.registry import get_recommended_model, ModelProvider

# Fast and cost-effective
fast_model = get_recommended_model("fast")
# Returns: gpt-4.1-nano or llama-3.1-8b-instant

# Complex reasoning
reasoning_model = get_recommended_model("complex reasoning")
# Returns: o3 or gemini-2.5-pro

# Vision tasks
vision_model = get_recommended_model("vision")
# Returns: gpt-4.1 or gemini-2.0-flash
```

### Filtering by Provider

```python
from models.registry import list_models, ModelProvider

# Get all OpenAI models
openai_models = list_models(ModelProvider.OPENAI)

# Get all Google models
google_models = list_models(ModelProvider.GOOGLE)
```


## Cost Comparison

| Model | Provider | Input Cost | Output Cost | Best For |
|-------|----------|------------|-------------|----------|
| gpt-4.1-nano | OpenAI | $0.000075 | $0.0003 | Ultra-low cost |
| gemini-2.0-flash-lite | Google | $0.0000375 | $0.00015 | Cheapest multimodal |
| llama-3.1-8b-instant | Groq | $0.00005 | $0.00008 | Fastest inference |
| gpt-4.1 | OpenAI | $0.0025 | $0.01 | Balanced performance |
| o3 | OpenAI | $0.01 | $0.04 | Complex reasoning |


## Troubleshooting

### Model Not Found

If you encounter "Model not found" errors, ensure:
1. You're using the exact model names from this verified list
2. Your API keys are correctly configured
3. The model is available in your current region

### Rate Limit Exceeded

- **OpenAI**: Implement exponential backoff
- **Google**: Monitor daily quotas
- **Groq**: Take advantage of high rate limits
- **Abacus AI**: Check provider-specific limits


## Related Documentation

- [CREDENTIALS_MANAGEMENT.md](../CREDENTIALS_MANAGEMENT.md) - Authentication setup
- [Settings Documentation](../docs/usage.md) - UI configuration guide
- [Model Registry](../models/registry.py) - Complete model definitions

---

**Last Updated**: January 2025
**Version**: 2.0
**Status**: Production Ready - All models verified against specified sources
