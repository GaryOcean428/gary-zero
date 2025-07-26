# AI Models - Gary-Zero Model Catalog

## Overview

Gary-Zero provides access to modern AI models from verified providers. This catalog includes models
released after June 2024, with a focus on performance, capabilities, and reliability.

⚠️ **Important**: "Computer use" is NOT a model - it's a tool capability. See
[Model Capabilities Guide](./model-capabilities.md) for details.

## Quick Reference

### Default Models (Recommended)
- **Chat**: Claude Sonnet 4 (`claude-sonnet-4-0`)
- **Code**: Claude Sonnet 4 (`claude-sonnet-4-0`)
- **Utility**: GPT-4.1 Mini (`gpt-4.1-mini`)
- **Embeddings**: Text Embedding 3 Large (`text-embedding-3-large`)
- **Browser**: Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Voice**: GPT-4o (`gpt-4o`)

### Model Statistics
- **Total Models**: 47 active models
- **Providers**: 7 verified providers
- **Last Updated**: January 2025

## Providers and Models

### 🤖 Anthropic (5 models)

#### Claude 4 Series (Latest)
- `claude-sonnet-4-0` - Claude 4 Sonnet ⭐ *Recommended for most tasks*
  - Supports computer use via Anthropic API
  - Excellent at code, analysis, and creative tasks
- `claude-opus-4-0` - Claude 4 Opus
  - Most powerful Claude model
  - Best for complex reasoning

#### Claude 3.5 Series
- `claude-3-5-sonnet-latest` - Claude 3.5 Sonnet (Latest)
- `claude-3-5-haiku-latest` - Claude 3.5 Haiku (Latest)
  - Fast and cost-effective

#### Specialized
- `claude-code` - Claude Code (CLI optimized)

### 🔷 OpenAI (18 models)

#### GPT-4.1 Series (Newest)
- `gpt-4.1` - Latest GPT-4.1 model
- `gpt-4.1-mini` - Cost-effective GPT-4.1 ⭐ *Recommended utility model*
- `gpt-4.1-nano` - Ultra-low cost variant

#### Reasoning Models
- `o3` - Advanced reasoning
- `o3-pro` - Enhanced o3 with more compute ⭐ *Best for complex problems*
- `o4-mini` - Efficient reasoning model

#### GPT-4o Series
- `gpt-4o` - GPT-4o with vision
  - Supports computer use via tools
- `gpt-4o-mini` - Cost-effective GPT-4o

#### Transcription Models
- `gpt-4o-transcribe` - Speech-to-text powered by GPT-4o
- `gpt-4o-mini-transcribe` - Lightweight transcription
- `whisper-1` - General-purpose speech recognition

#### Tool-Specific Models
- `gpt-4o-search-preview` - Web search in Chat Completions
- `gpt-4o-mini-search-preview` - Fast web search
- `codex-mini-latest` - Fast code reasoning (CLI)

#### Embedding Models
- `text-embedding-3-small` - Efficient embeddings
- `text-embedding-3-large` - High-quality embeddings ⭐ *Recommended*
- `text-embedding-ada-002` - Legacy embeddings

### 🔍 Google (8 models)

#### Gemini 2.5 Series (Latest)
- `gemini-2.5-pro` - Advanced reasoning
- `gemini-2.5-pro-latest` - Latest 2.5 Pro
- `gemini-2.5-flash` - Fast and efficient
- `gemini-2.5-flash-latest` - Latest 2.5 Flash

#### Gemini 2.0 Series
- `gemini-2.0-flash` - Multimodal capabilities
- `gemini-2.0-flash-latest` - Latest 2.0 Flash

#### CLI Models
- `gemini-cli-chat` - CLI-optimized chat
- `gemini-cli-code` - CLI-optimized code generation

### ⚡ Groq (5 models)

Fast inference hardware-accelerated models:
- `llama-3.1-8b-instant` - Lightning-fast Llama ⭐ *Fastest inference*
- `llama-3.3-70b-versatile` - High-performance Llama
- `moonshotai/kimi-k2-instruct` - Moonshot AI's Kimi
- `qwen/qwen3-32b` - Qwen 3 32B
- `gemma2-9b-it` - Google's Gemma 2

### 🌐 Perplexity (5 models)

All models include built-in web search:
- `sonar` - Lightweight search
- `sonar-pro` - Enhanced search
- `sonar-reasoning` - Real-time reasoning with search
- `sonar-reasoning-pro` - Advanced reasoning ⭐ *Best for research*
- `sonar-deep-research` - Expert-level research

### 🚀 xAI (8 models)

#### Grok 4 Series (Latest)
- `grok-4-latest` - Latest Grok 4
- `grok-4-0709` - Grok 4 stable

#### Grok 3 Series
- `grok-3` - Grok 3 base
- `grok-3-fast` - Fast variant
- `grok-3-mini` - Smaller model
- `grok-3-mini-fast` - Fast mini

#### Grok 2 Series
- `grok-2-1212` - Grok 2
- `grok-2-vision-1212` - Grok 2 with vision

### 📝 Qwen (1 model)

- `qwen-coder` - Specialized code generation (CLI)

## Model Selection by Use Case

### 🖥️ Computer Use & Automation
**Best**: Claude Sonnet 4 (`claude-sonnet-4-0`)
- Native computer use support
- Screenshot analysis
- Desktop control

**Alternative**: GPT-4o (`gpt-4o`)
- Browser automation
- Tool integration

### 🔍 Web Search & Research
**Best**: Perplexity Sonar models
- `sonar-reasoning-pro` - For complex research
- `sonar-deep-research` - For comprehensive analysis

**Alternative**: OpenAI search preview models
- `gpt-4o-search-preview`
- `gpt-4o-mini-search-preview`

### 💻 Code Generation
**Best**: Claude Sonnet 4 (`claude-sonnet-4-0`)
**Alternatives**:
- `claude-code` - CLI optimized
- `codex-mini-latest` - Fast code reasoning
- `gemini-cli-code` - Google's code model

### 👁️ Vision & Multimodal
**Best Options**:
- `gpt-4o` - OpenAI's multimodal
- `claude-sonnet-4-0` - Anthropic's vision
- `gemini-2.5-pro` - Google's multimodal
- `grok-2-vision-1212` - xAI's vision model

### ⚡ Fast Inference
**Fastest**: `llama-3.1-8b-instant` (Groq)
**Alternatives**:
- `gpt-4.1-nano` - OpenAI's fastest
- `claude-3-5-haiku-latest` - Anthropic's fast model
- `grok-3-mini-fast` - xAI's fast variant

### 🎯 Complex Reasoning
**Best**: `o3-pro` (OpenAI)
**Alternatives**:
- `o3` - Standard advanced reasoning
- `claude-opus-4-0` - Anthropic's most powerful
- `sonar-reasoning-pro` - With web search

## Important Notes

### Computer Use is a Tool, Not a Model

⚠️ **Common Misconception**: "computer-use-preview" is NOT a model name.

**Computer use** is a capability available with:
- Claude Sonnet 4 (via Anthropic's Computer Use API)
- GPT-4o models (via tool integrations)

See [Computer Use Guide](./computer-use-guide.md) for implementation details.

### Model Capabilities vs Models

**Models** are the AI language models (e.g., `claude-sonnet-4-0`)

**Capabilities** are what models can do:
- Computer use
- Web search
- Code execution
- MCP integration
- Vision processing
- Voice transcription

See [Model Capabilities Guide](./model-capabilities.md) for full details.

## Provider Configuration

### API Key Setup

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Google
export GOOGLE_API_KEY="AIza..."

# Groq
export GROQ_API_KEY="gsk_..."

# Perplexity
export PERPLEXITY_API_KEY="pplx-..."

# xAI
export XAI_API_KEY="xai-..."

# Qwen
export QWEN_API_KEY="qwen-..."
```

### Gary-Zero Configuration

In `framework/helpers/settings/types.py`:

```python
# Recommended defaults
"chat_model_provider": "ANTHROPIC",
"chat_model_name": "claude-sonnet-4-0",

"code_model_provider": "ANTHROPIC",
"code_model_name": "claude-sonnet-4-0",

"util_model_provider": "OPENAI",
"util_model_name": "gpt-4.1-mini",

"embed_model_provider": "OPENAI",
"embed_model_name": "text-embedding-3-large",
```

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
