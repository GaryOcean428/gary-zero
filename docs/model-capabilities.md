# AI Model Capabilities Guide

This document provides a comprehensive overview of the capabilities available with different AI models in Gary-Zero,
including tools, integrations, and special features.

## Overview

AI model capabilities extend beyond basic text generation. Modern models support various tools and
integrations that enable them to:
- Control computers and browsers
- Execute code and commands
- Search the web
- Access file systems
- Integrate with external services via MCP

## Important Distinction: Models vs Tools

**Models** are the AI language models themselves (e.g., `claude-sonnet-4-0`, `gpt-4o`).

**Tools** are capabilities that models can use (e.g., computer use, web search, MCP servers).

⚠️ **Note**: "Computer use" is NOT a model - it's a tool capability available with certain models.

## Provider Capabilities

### Anthropic (Claude)

#### Models with Computer Use
- **Claude Sonnet 4** (`claude-sonnet-4-0`)
  - ✅ Computer Use via Anthropic's Computer Use API
  - ✅ Screenshot analysis
  - ✅ Mouse and keyboard control
  - ✅ Window management

#### Other Capabilities
- **Vision**: All Claude models
- **Code Generation**: All models, especially `claude-code`
- **Function Calling**: All Claude 3.5+ models
- **MCP Support**: All models

### OpenAI

#### Models with Computer Use
- **GPT-4o** (`gpt-4o`, `gpt-4o-mini`)
  - ✅ Computer Use via tool integrations
  - ✅ Browser automation
  - ✅ File system access

#### Specialized Models
- **Transcription**:
  - `gpt-4o-transcribe` - Speech-to-text powered by GPT-4o
  - `gpt-4o-mini-transcribe` - Lightweight transcription
  - `whisper-1` - General-purpose speech recognition

- **Web Search**:
  - `gpt-4o-search-preview` - Web search in Chat Completions
  - `gpt-4o-mini-search-preview` - Fast, affordable web search

- **Code**:
  - `codex-mini-latest` - Fast reasoning for code generation

#### Other Capabilities
- **Vision**: GPT-4o, GPT-4.1 models
- **Function Calling**: All GPT models
- **Embeddings**: `text-embedding-3-small`, `text-embedding-3-large`, `text-embedding-ada-002`
- **MCP Support**: All models

### Google (Gemini)

#### Core Capabilities
- **Vision**: All Gemini 2.0+ models
- **Voice**: TTS models (when available)
- **Code Generation**: All models, especially `gemini-cli-code`
- **Function Calling**: All Gemini models
- **MCP Support**: All models

#### CLI Integration
- `gemini-cli-chat` - CLI-optimized chat interface
- `gemini-cli-code` - CLI-optimized code generation

### Other Providers

#### Groq
- **Fast Inference**: All models optimized for speed
- **Function Calling**: Supported
- **MCP Support**: All models

#### Perplexity
- **Web Search**: Built-in web search for all Sonar models
- **Real-time Information**: All models have internet access
- **Deep Research**: `sonar-deep-research` for comprehensive analysis

#### xAI (Grok)
- **Vision**: Grok 2 Vision models
- **Function Calling**: All Grok 3+ models
- **MCP Support**: All models

## Tool Capabilities

### Computer Use

Computer use allows AI models to control desktop applications, browsers, and system functions.

**Available with**:
- Claude Sonnet 4 (via Anthropic Computer Use API)
- GPT-4o models (via tool integrations)

**Capabilities**:
- Screenshot capture and analysis
- Mouse movement and clicking
- Keyboard input
- Window management
- Application control

**Configuration** (in settings):

```python
"computer_use_enabled": True,
"computer_use_require_approval": False,
"computer_use_screenshot_interval": 1.0,
"computer_use_max_actions_per_session": 50
```

### MCP (Model Context Protocol)

MCP enables models to interact with external tools and services.

**Available with**: All modern models

**Built-in MCP Servers**:
- `filesystem` - File system access
- `github` - GitHub repository interaction
- `memory` - Persistent memory storage
- `mcp-browserbase` - Browser automation
- `mcp-taskmanager` - Task management

**Learn more**: See [MCP Integration Guide](./mcp-integration.md)

### Web Search

**Native Support**:
- OpenAI: `web_search_preview` tool
- Perplexity: Built into all Sonar models

**Via MCP**: Available to all models through MCP servers

### Code Execution

**Native Support**:
- OpenAI: Code interpreter tool
- Anthropic: Code execution environments

**Via Integration**:
- E2B (sandboxed execution)
- Local execution with approval

## Capability Matrix

| Provider | Model | Computer Use | Web Search | Code Exec | Vision | Voice | MCP |
|----------|-------|--------------|------------|-----------|---------|--------|-----|
| Anthropic | Claude Sonnet 4 | ✅ Native | Via MCP | ✅ | ✅ | ❌ | ✅ |
| Anthropic | Claude 3.5 Sonnet | ❌ | Via MCP | ✅ | ✅ | ❌ | ✅ |
| OpenAI | GPT-4o | ✅ Tool | ✅ Native | ✅ | ✅ | ❌ | ✅ |
| OpenAI | GPT-4.1 | ❌ | ✅ Native | ✅ | ✅ | ❌ | ✅ |
| Google | Gemini 2.5 | ❌ | Via MCP | ✅ | ✅ | ✅* | ✅ |
| Groq | Llama models | ❌ | Via MCP | Via MCP | ❌ | ❌ | ✅ |
| Perplexity | Sonar models | ❌ | ✅ Native | ❌ | ❌ | ❌ | ✅ |
| xAI | Grok 3/4 | ❌ | Via MCP | Via MCP | ✅** | ❌ | ✅ |

\* When TTS models are available
\** Grok 2 Vision models only

## Best Practices

### Choosing Models by Capability

**For Computer Use**:
1. **Primary**: Claude Sonnet 4 - Most advanced computer use
2. **Alternative**: GPT-4o - Good browser automation

**For Web Search**:
1. **Primary**: Perplexity Sonar models - Built-in search
2. **Alternative**: OpenAI with search preview tools

**For Code Generation**:
1. **Primary**: Claude Sonnet 4 or Claude Code
2. **Alternative**: Codex Mini Latest, Gemini CLI Code

**For Vision Tasks**:
1. **Primary**: GPT-4o or Claude models
2. **Alternative**: Gemini 2.0+ models

**For Fast Inference**:
1. **Primary**: Groq models (Llama variants)
2. **Alternative**: GPT-4.1-nano, Claude Haiku

### Combining Capabilities

Many tasks benefit from combining multiple capabilities:

```python
# Example: Web research with code generation
1. Use Perplexity Sonar to search for information
2. Use Claude Sonnet 4 to generate code based on findings
3. Use E2B to test the code in a sandbox

# Example: Automated testing
1. Use Claude Sonnet 4 with computer use to navigate UI
2. Use GPT-4o to analyze screenshots
3. Use MCP task manager to track test results
```

## Configuration Examples

### Enabling Computer Use

```python
# In framework/helpers/settings/types.py
"computer_use_enabled": True,
"computer_use_require_approval": False,  # Auto-approve actions
"computer_use_screenshot_interval": 1.0,  # Seconds between screenshots
"computer_use_max_actions_per_session": 50
```

### Configuring MCP Servers

```python
# In settings
"mcp_servers": "filesystem,github,memory,mcp-browserbase",
"mcp_client_init_timeout": 30,
"mcp_client_tool_timeout": 300
```

### Model Selection for Capabilities

```python
# For computer use tasks
"browser_model_provider": "ANTHROPIC",
"browser_model_name": "claude-sonnet-4-0",

# For code generation
"code_model_provider": "ANTHROPIC",
"code_model_name": "claude-sonnet-4-0",

# For fast utility tasks
"util_model_provider": "OPENAI",
"util_model_name": "gpt-4.1-mini"
```

## Related Documentation

- [AI Models List](./ai-models.md) - Complete list of available models
- [MCP Integration Guide](./mcp-integration.md) - Setting up MCP servers
- [Computer Use Guide](./computer-use-guide.md) - Detailed computer control guide
- [Model Selection Guide](./USER_GUIDE_MODEL_SELECTION.md) - Choosing the right model

---

**Last Updated**: January 2025
**Version**: 1.0
