# Model Verification Action Plan - Complete with All User Requirements

## Quick Reference: What Needs to Be Done

### 1. Update Default Settings (`framework/helpers/settings/types.py`)

Update BOTH chat and code models to Claude Sonnet 4:

```python
# FROM:
"chat_model_name": "claude-3-5-sonnet-20241022",  # Valid but not preferred
"code_model_name": "claude-3-5-sonnet-20241022",  # Should update

# TO:
"chat_model_name": "claude-sonnet-4-0",  # Preferred chat model
"code_model_name": "claude-sonnet-4-0",  # Preferred code model (USER REQUIREMENT)

# Keep browser model as is (Claude 3.5 Sonnet is valid):
"browser_model_name": "claude-3-5-sonnet-20241022",  # ✅ Valid
```

### 2. Clean Model Catalog (`framework/helpers/model_catalog.py`)

**OPENAI** - Keep these models (18 total):

```python
# Core Models
"gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"
"o3", "o3-pro"  # o3-pro is USER REQUIREMENT
"o4-mini"
"gpt-4o", "gpt-4o-mini"  # gpt-4o supports computer use tools

# Transcription Models (USER REQUIREMENT)
"gpt-4o-transcribe"
"gpt-4o-mini-transcribe"
"whisper-1"

# Tool-Specific Models (USER REQUIREMENT)
"gpt-4o-search-preview"
"gpt-4o-mini-search-preview"
"codex-mini-latest"  # CLI model
# NOTE: computer-use-preview REMOVED - it's a tool capability, not a model

# Embedding Models (USER REQUIREMENT)
"text-embedding-3-small"
"text-embedding-3-large"
"text-embedding-ada-002"
```

**ANTHROPIC** - Keep these models:

```python
"claude-sonnet-4-0"  # Supports computer use tools
"claude-opus-4-0"
"claude-3-5-sonnet-latest"
"claude-3-5-haiku-latest"
"claude-code"  # CLI model (USER REQUIREMENT)
```

**GOOGLE** - Only Gemini 2.0+ and CLI models:

```python
# Core Models (2.0 and above only)
"gemini-2.5-pro"
"gemini-2.5-pro-latest"
"gemini-2.5-flash"
"gemini-2.5-flash-latest"
"gemini-2.0-flash"
"gemini-2.0-flash-latest"

# CLI Models (USER REQUIREMENT)
"gemini-cli-chat"
"gemini-cli-code"

# REMOVE all Gemini 1.5, 1.0, experimental, and legacy models
```

**GROQ** - Keep only these specific models:

```python
"llama-3.1-8b-instant"
"llama-3.3-70b-versatile"
"moonshotai/kimi-k2-instruct"  # ADD THIS
"qwen/qwen3-32b"  # ADD THIS
"gemma2-9b-it"
# REMOVE: mixtral-8x7b-32768
```

**XAI** - Add new provider with Grok models:

```python
"XAI": [
    {"value": "grok-4-latest", "label": "Grok 4 Latest", "modern": True},
    {"value": "grok-3", "label": "Grok 3", "modern": True},
    {"value": "grok-3-mini", "label": "Grok 3 Mini", "modern": True},
    {"value": "grok-3-fast", "label": "Grok 3 Fast", "modern": True},
    {"value": "grok-3-mini-fast", "label": "Grok 3 Mini Fast", "modern": True},
]
```

**PERPLEXITY** - Add new provider with sonar models:

```python
"PERPLEXITY": [
    {"value": "sonar", "label": "Sonar", "modern": True},
    {"value": "sonar-pro", "label": "Sonar Pro", "modern": True},
    {"value": "sonar-reasoning", "label": "Sonar Reasoning", "modern": True},
    {"value": "sonar-reasoning-pro", "label": "Sonar Reasoning Pro", "modern": True},
    {"value": "sonar-deep-research", "label": "Sonar Deep Research", "modern": True},
]
```

**QWEN** - Add new provider for CLI:

```python
"QWEN": [
    {"value": "qwen-coder", "label": "Qwen Coder", "modern": True, "code": True},
]
```

**Remove These Providers Entirely**:
- MISTRALAI, OPENAI_AZURE, HUGGINGFACE, CHUTES
- OLLAMA, LMSTUDIO, META (keep Qwen as separate provider)
- SAMBANOVA, DEEPSEEK, OPENROUTER
- OTHER

### 3. Summary of All Models to Keep

**OpenAI (18 models)**:
- Core: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o3, o3-pro, o4-mini, gpt-4o, gpt-4o-mini
- Transcription: gpt-4o-transcribe, gpt-4o-mini-transcribe, whisper-1
- Tool-specific: gpt-4o-search-preview, gpt-4o-mini-search-preview, codex-mini-latest
- Embeddings: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002

**Anthropic (5 models)**:
- claude-sonnet-4-0, claude-opus-4-0, claude-3-5-sonnet-latest, claude-3-5-haiku-latest, claude-code

**Google (8 models)**:
- gemini-2.5-pro, gemini-2.5-pro-latest, gemini-2.5-flash, gemini-2.5-flash-latest
- gemini-2.0-flash, gemini-2.0-flash-latest, gemini-cli-chat, gemini-cli-code

**Groq (5 models)**:
- llama-3.1-8b-instant, llama-3.3-70b-versatile, moonshotai/kimi-k2-instruct
- qwen/qwen3-32b, gemma2-9b-it

**xAI (5 models)**:
- grok-4-latest, grok-3, grok-3-mini, grok-3-fast, grok-3-mini-fast

**Perplexity (5 models)**:
- sonar, sonar-pro, sonar-reasoning, sonar-reasoning-pro, sonar-deep-research

**Qwen (1 model)**:
- qwen-coder

### 4. Total Model Count

**Final count: 47 models** across 7 providers (reduced from 48 - removed computer-use-preview)
- Focused on modern, verified models
- Includes all requested transcription, tool-specific, and CLI models
- Excludes all Gemini 1.5 and below
- Excludes experimental/legacy models (except specified)

### 5. Key Implementation Notes

1. **Claude Sonnet 4 for BOTH chat and code** - Update both defaults
2. **Keep ALL OpenAI specialty models** - Transcription, tools, embeddings
3. **Computer use is a TOOL** - Available with Claude Sonnet 4 and GPT-4o models
4. **Add missing CLI models** - claude-code, qwen-coder, gemini-cli-*
5. **Create new providers** - XAI, PERPLEXITY, QWEN
6. **Strict Gemini filtering** - Only 2.0+ plus CLI models

### 6. Important Clarification

**Computer Use**: This is a tool capability, NOT a separate model. It's available with:
- Claude Sonnet 4 (`claude-sonnet-4-0`)
- GPT-4o models (`gpt-4o`, `gpt-4o-mini`)

Reference: <https://platform.openai.com/docs/guides/tools-computer-use>
