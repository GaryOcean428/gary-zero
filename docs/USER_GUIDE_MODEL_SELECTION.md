# Gary-Zero Model Selection Guide


## Overview

Gary-Zero now features an advanced model catalog that prioritizes the latest and most capable AI models. This guide explains the new model selection features and how to get the best performance from your AI assistant.


## What's New

### Modern Model Priority

Gary-Zero now automatically shows you the newest and most capable models first. When you open model selection dropdowns, you'll see models like:

- **OpenAI o3** - OpenAI's latest reasoning model
- **Claude 4 Sonnet** - Anthropic's most advanced model
- **Gemini 2.0 Flash** - Google's newest multimodal model

### Specialized Model Types

Gary-Zero now supports different types of models optimized for specific tasks:

#### 🎙️ Voice Models

For real-time voice conversations and speech-to-speech interactions:
- **OpenAI GPT-4o Realtime** - Natural voice conversations
- **Google Gemini Live** - Multimodal voice interactions

#### 💻 Code Models

For programming, development, and technical tasks:
- **Claude Code** - Specialized for code analysis and generation
- **DeepSeek Coder** - Optimized for programming tasks

#### 👁️ Vision Models

For analyzing images, documents, and visual content:
- **Claude 4 Sonnet** - Advanced vision capabilities
- **GPT-4o** - Multimodal understanding


## How to Access Model Settings

1. **Open Settings**: Click the ⚙️ Settings button in the sidebar
2. **Navigate to Agent Settings**: Click the "Agent Settings" tab
3. **Find Model Sections**: Scroll to find different model configuration sections


## Model Configuration Sections

### Chat Model

Your primary conversational model for general interactions.

**Recommended**: Claude 4 Sonnet (default)
- Best overall performance for complex reasoning
- Large 200K token context window
- Advanced vision capabilities

### Voice Model

For voice-to-voice conversations and speech interactions.

**Configuration Options**:
- **Architecture**:
  - *Speech-to-Speech* (realtime) - Direct voice interaction
  - *Chained* (transcribe → LLM → TTS) - Traditional pipeline
- **Transport**: WebSocket or WebRTC for real-time connections

**Recommended**: OpenAI GPT-4o Realtime (default)
- Natural conversation flow
- Low latency for real-time interaction
- High-quality voice synthesis

### Code Model

For programming assistance, code review, and development tasks.

**Recommended**: Claude Code (default)
- Specialized for code understanding
- Advanced debugging capabilities
- Multi-language support

### Utility Model

For quick tasks like summarization, organization, and simple queries.

**Recommended**: GPT-4.1 Mini (default)
- Fast response times
- Cost-effective for simple tasks
- Large context window

### Browser Model

For web automation and visual web page analysis.

**Recommended**: Claude 4 Sonnet with Vision (default)
- Advanced visual understanding
- Web element recognition
- Complex page analysis


## Getting Started

### Quick Setup (Recommended)

Gary-Zero comes pre-configured with optimal model defaults. For most users, no changes are needed! The system automatically uses:

- **Chat**: Claude 4 Sonnet
- **Voice**: OpenAI GPT-4o Realtime
- **Code**: Claude Code
- **Utility**: GPT-4.1 Mini

### Custom Configuration

To customize your model selection:

1. **Open Settings** → **Agent Settings**
2. **Choose your preferred provider** from the dropdown
3. **Select your preferred model** from the filtered list
4. **Adjust advanced settings** if needed (context length, rate limits)
5. **Click Apply** to save changes


## Understanding Model Types

### Modern vs Legacy Models

- **Modern Models** (post-June 2024): Latest capabilities, best performance
- **Legacy Models** (pre-June 2024): Older models, available as fallbacks

Gary-Zero automatically shows modern models first, but legacy models remain available if needed.

### Model Capabilities

Look for capability indicators next to model names:

- 🎙️ **Voice** - Supports voice interaction
- 💻 **Code** - Optimized for programming
- 👁️ **Vision** - Can analyze images and visual content

### Context Windows

Different models support different context sizes:

- **Large Context** (200K+ tokens): Complex documents, long conversations
- **Medium Context** (32K-128K tokens): Standard conversations, documents
- **Standard Context** (8K-32K tokens): Quick tasks, simple queries


## Voice Model Setup

### Architecture Options

**Speech-to-Speech (Recommended)**
- Direct voice-to-voice interaction
- Lowest latency
- Most natural conversation flow
- Requires voice-capable models

**Chained Pipeline**
- Traditional transcription → processing → synthesis
- Works with any chat model
- Higher latency but more flexible
- Good fallback option

### Transport Protocols

**WebSocket (Recommended)**
- Standard web protocol
- Reliable connection
- Good for most users

**WebRTC**
- Peer-to-peer connection
- Lower latency
- Advanced option for optimal performance


## Code Model Configuration

### When to Use Code Models

- Writing or reviewing code
- Debugging problems
- Architecture discussions
- Technical documentation
- API integration

### Code Model Features

- **Syntax highlighting** understanding
- **Multi-language support** (Python, JavaScript, Go, etc.)
- **Code completion** and suggestions
- **Bug detection** and fixes
- **Documentation generation**


## Best Practices

### Choosing the Right Model

**For General Chat**: Claude 4 Sonnet
- Best reasoning and conversation quality
- Handles complex topics well
- Large context for long discussions

**For Quick Questions**: GPT-4.1 Mini (Utility)
- Fast responses
- Cost-effective
- Good for simple tasks

**For Programming**: Claude Code
- Specialized for development
- Better code understanding
- Helpful debugging assistance

**For Voice Chat**: OpenAI GPT-4o Realtime
- Natural voice interaction
- Low latency
- High-quality speech

### Performance Tips

1. **Use appropriate model types** for different tasks
2. **Adjust context length** based on your needs
3. **Enable vision** only when analyzing images
4. **Set rate limits** if using API quotas
5. **Test voice settings** for optimal audio quality


## Troubleshooting

### Common Issues

**Model not responding**
- Check your API keys in External Services
- Verify model is available for your provider
- Try switching to a different model

**Voice not working**
- Ensure microphone permissions are granted
- Check voice model configuration
- Try switching transport protocol

**Slow responses**
- Consider using a smaller/faster model for simple tasks
- Check your internet connection
- Verify rate limit settings

### Getting Help

If you encounter issues:

1. **Check the activity monitor** for error messages
2. **Try a different model** to isolate the problem
3. **Review your API key configuration**
4. **Check the model's availability status**


## API Keys Required

To use different providers, you'll need API keys:

- **OpenAI**: For GPT models, o3, voice features
- **Anthropic**: For Claude models, Claude Code
- **Google**: For Gemini models, Gemini Live
- **DeepSeek**: For DeepSeek Coder

Add your API keys in **Settings** → **External Services** → **API Keys**.


## Advanced Features

### Rate Limiting

Control usage and costs by setting limits:
- **Requests per minute**: Limit API calls
- **Input tokens per minute**: Control input processing
- **Output tokens per minute**: Control response generation

### Model Parameters

Customize model behavior with additional parameters:
- **Temperature**: Control creativity vs consistency
- **Max tokens**: Limit response length
- **Top-p**: Adjust response diversity

### Context Management

Optimize context usage:
- **Context length**: Total available tokens
- **History allocation**: Portion reserved for chat history
- **Auto-optimization**: Automatic history summarization


## What's Coming Next

Future enhancements planned:
- **Dynamic model discovery** from providers
- **Model performance analytics**
- **Usage optimization suggestions**
- **Advanced voice customization**
- **Multi-model conversations**

---


## Quick Reference

| Task Type | Recommended Model | Why |
|-----------|------------------|-----|
| **General Chat** | Claude 4 Sonnet | Best reasoning, large context |
| **Voice Chat** | GPT-4o Realtime | Natural speech, low latency |
| **Programming** | Claude Code | Code-specialized, debugging |
| **Quick Tasks** | GPT-4.1 Mini | Fast, efficient, cost-effective |
| **Web Browsing** | Claude 4 Sonnet | Vision capabilities, web understanding |
| **Document Analysis** | Claude 4 Sonnet | Large context, vision support |

**Default Configuration**: Gary-Zero comes optimally configured out of the box. Most users won't need to change anything!

---

*This guide covers the new model selection features in Gary-Zero. For technical details, see the developer documentation.*
