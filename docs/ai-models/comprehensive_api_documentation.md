# Comprehensive AI API Documentation

This document provides detailed technical specifications and implementation guides for all major AI providers' APIs, compiled from official sources as of July 2025.

## Table of Contents
1. [OpenAI](#openai)
2. [Google Gemini](#google-gemini)
3. [xAI (Grok)](#xai-grok)
4. [Groq](#groq)
5. [Anthropic Claude](#anthropic-claude)
6. [Perplexity AI](#perplexity-ai)
7. [Moonshot AI](#moonshot-ai)
8. [Qwen (Alibaba)](#qwen-alibaba)

---

## OpenAI

### API Endpoints
**Base URL**: `https://api.openai.com/v1`

#### Core Endpoints
- **Chat Completions**: `POST /chat/completions`
- **Responses API**: `POST /responses` (new unified API)
- **Completions**: `POST /completions` (legacy)
- **Images**: `POST /images/generations`, `POST /images/edits`, `POST /images/variations`
- **Audio**: `POST /audio/transcriptions`, `POST /audio/translations`, `POST /audio/speech`
- **Embeddings**: `POST /embeddings`
- **Files**: `POST /files`, `GET /files`, `GET /files/{file_id}`, `DELETE /files/{file_id}`
- **Fine-tuning**: `POST /fine_tuning/jobs`, `GET /fine_tuning/jobs`
- **Moderation**: `POST /moderations`
- **Models**: `GET /models`, `GET /models/{model}`
- **Assistants**: `POST /assistants`, `GET /assistants/{assistant_id}`
- **Batches**: `POST /batches`, `GET /batches/{batch_id}`

#### Realtime API
- **WebSocket**: `wss://api.openai.com/v1/realtime`

### Authentication
```bash
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Chat Completions Example
```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=150
)
```

#### Responses API Example (New)
```python
response = client.responses.create(
    model="gpt-4.1",
    input="Write a one-sentence bedtime story about a unicorn.",
    tools=[{"type": "web_search_preview"}]
)
print(response.output_text)
```

#### cURL Example
```bash
curl "https://api.openai.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Rate Limits
- **Tier-based system** with automatic upgrades based on usage
- **RPM (Requests Per Minute)**: 500-10,000+ depending on tier
- **TPM (Tokens Per Minute)**: 30,000-5,000,000+ depending on model and tier
- **Batch API**: 50% discount for async processing

### Error Codes
- **400**: Bad Request - Invalid request format
- **401**: Unauthorized - Invalid API key
- **403**: Forbidden - Country/region not supported
- **429**: Rate limit exceeded
- **500**: Server error
- **503**: Service unavailable

### SDKs
- **Python**: `pip install openai`
- **Node.js**: `npm install openai`
- **Ruby**: `gem install ruby-openai`
- **Go**: Official Go client available
- **Java**: Community-maintained clients
- **.NET**: Official .NET client

### Pricing (USD per 1M tokens)

#### Latest Models
| Model | Input | Cached Input | Output |
|-------|-------|--------------|--------|
| GPT-4.1 | $2.00 | $0.50 | $8.00 |
| GPT-4.1 mini | $0.40 | $0.10 | $1.60 |
| GPT-4.1 nano | $0.10 | $0.025 | $0.40 |
| OpenAI o3 | $2.00 | $0.50 | $8.00 |
| OpenAI o4-mini | $1.10 | $0.275 | $4.40 |

#### Realtime API
| Model | Text Input | Text Output | Audio Input | Audio Output |
|-------|------------|-------------|-------------|--------------|
| GPT-4o | $5.00 | $20.00 | $40.00 | $80.00 |
| GPT-4o mini | $0.60 | $2.40 | $10.00 | $20.00 |

#### Built-in Tools
- **Code Interpreter**: $0.03 per call
- **File Search Storage**: $0.10/GB/day (first GB free)
- **File Search Tool Call**: $2.50/1k calls
- **Web Search**: $25.00/1k calls (gpt-4o/4.1), $10.00/1k calls (o3/o4-mini)

### Technical Specifications
- **Context Windows**: Up to 128K tokens (varies by model)
- **Max Output**: Up to 4,096 tokens
- **Supported Formats**: Text, images, audio, PDFs
- **Function Calling**: JSON schema-based tool definitions
- **Streaming**: Server-Sent Events (SSE)
- **Vision**: Image analysis and generation capabilities

### Code Examples

#### Streaming Response
```python
stream = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

#### Function Calling
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=tools
)
```

---

## Google Gemini

### API Endpoints
**Base URL**: `https://generativelanguage.googleapis.com/v1beta`

#### Core Endpoints
- **Generate Content**: `POST /models/{model}:generateContent`
- **Stream Generate**: `POST /models/{model}:streamGenerateContent`
- **Count Tokens**: `POST /models/{model}:countTokens`
- **Embed Content**: `POST /models/{model}:embedContent`
- **Batch Embed**: `POST /models/{model}:batchEmbedContent`
- **List Models**: `GET /models`
- **Get Model**: `GET /models/{model}`

#### Live API (Real-time)
- **WebSocket**: Real-time audio/video streaming

### Authentication
```bash
x-goog-api-key: YOUR_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Python Example
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words"
)
print(response.text)
```

#### JavaScript Example
```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});
const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: "Explain how AI works in a few words"
});
console.log(response.text);
```

#### cURL Example
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {"parts": [{"text": "Explain how AI works"}]}
    ]
  }'
```

### Rate Limits

#### Free Tier
| Model | RPM | TPM | RPD |
|-------|-----|-----|-----|
| Gemini 2.5 Pro | 5 | 250,000 | 100 |
| Gemini 2.5 Flash | 10 | 250,000 | 250 |
| Gemini 2.5 Flash-Lite | 15 | 250,000 | 1,000 |
| Gemini 2.0 Flash | 15 | 1,000,000 | 200 |

#### Tier 1 (Paid)
| Model | RPM | TPM | RPD |
|-------|-----|-----|-----|
| Gemini 2.5 Pro | 150 | 2,000,000 | 10,000 |
| Gemini 2.5 Flash | 1,000 | 1,000,000 | 10,000 |
| Gemini 2.5 Flash-Lite | 4,000 | 4,000,000 | No limit |

### Error Codes
- **400**: Bad Request - Invalid request parameters
- **401**: Unauthorized - Invalid API key
- **403**: Forbidden - Quota exceeded or region restricted
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error
- **503**: Service Unavailable

### SDKs
- **Python**: `pip install google-genai`
- **Node.js**: `npm install @google/genai`
- **Go**: `go get google.golang.org/genai`
- **Java**: Official Java client available

### Pricing (USD per 1M tokens)

#### Gemini 2.5 Pro
| Tier | Input (≤200k) | Input (>200k) | Output (≤200k) | Output (>200k) |
|------|---------------|---------------|----------------|----------------|
| Free | Free | Free | Free | Free |
| Paid | $1.25 | $2.50 | $10.00 | $15.00 |

#### Gemini 2.5 Flash
| Tier | Text/Image/Video Input | Audio Input | Output |
|------|------------------------|-------------|--------|
| Free | Free | Free | Free |
| Paid | $0.30 | $1.00 | $2.50 |

#### Gemini 2.5 Flash-Lite
| Tier | Text/Image/Video Input | Audio Input | Output |
|------|------------------------|-------------|--------|
| Free | Free | Free | Free |
| Paid | $0.10 | $0.30 | $0.40 |

#### Additional Services
- **Context Caching**: $0.075-$4.50 per 1M tokens/hour
- **Grounding with Google Search**: $35/1k requests (after free quota)
- **Imagen 4**: $0.04-$0.06 per image
- **Veo 3**: $0.50-$0.75 per second of video
- **Batch Mode**: 50% discount on all models

### Technical Specifications
- **Context Windows**: Up to 1M-2M tokens depending on model
- **Max Output**: Up to 65,536 tokens
- **Supported Formats**: Text, images, video, audio, PDFs
- **Multimodal**: Native support for vision and audio
- **Function Calling**: JSON schema-based tools
- **Streaming**: Server-Sent Events
- **Caching**: Context caching for repeated prompts

### Code Examples

#### Multimodal Input
```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        {
            "role": "user",
            "parts": [
                {"text": "What's in this image?"},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image_data
                }}
            ]
        }
    ]
)
```

#### Streaming Response
```python
stream = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Tell me a story",
    stream=True
)

for chunk in stream:
    print(chunk.text, end="")
```

---

## xAI (Grok)

### API Endpoints
**Base URL**: `https://api.x.ai/v1`

#### Core Endpoints
- **Chat Completions**: `POST /chat/completions`
- **Messages (Anthropic-compatible)**: `POST /messages`
- **Image Generation**: `POST /images/generations`
- **Deferred Chat**: `POST /chat/completions/deferred`
- **Get Deferred**: `GET /completions/deferred/{completion_id}`
- **Models**: `GET /models`, `GET /models/{model_id}`
- **Language Models**: `GET /language-models`, `GET /language-models/{model_id}`

#### Management API
- **API Keys**: `POST /api-key`, `GET /api-key`, `DELETE /api-key/{key_id}`

### Authentication
```bash
Authorization: Bearer YOUR_XAI_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Chat Completions Example
```bash
curl "https://api.x.ai/v1/chat/completions" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 101*3?"}
    ]
  }'
```

#### Response Format
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1752854522,
  "model": "grok-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "101 multiplied by 3 is 303."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 32,
    "completion_tokens": 9,
    "total_tokens": 41
  }
}
```

#### Image Generation Example
```bash
curl "https://cdn.pixabay.com/photo/2022/11/17/09/09/cat-in-tree-7597653_1280.jpg" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat in a tree",
    "model": "grok-2-image",
    "response_format": "url",
    "n": 2
  }'
```

### Rate Limits
- Rate limits vary by model and subscription tier
- Specific limits available via `/v1/language-models` endpoint
- Enterprise customers get higher limits

### Error Codes
- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Invalid API key
- **403**: Forbidden - Insufficient permissions
- **429**: Rate limit exceeded
- **500**: Internal server error

### SDKs
- Compatible with OpenAI SDKs by changing base URL
- Official SDKs in development

### Pricing
- Pricing per model available via `/v1/language-models` endpoint
- Costs quoted in USD cents per 100M tokens
- Text input/output and image processing have different rates
- Contact sales for enterprise pricing

### Technical Specifications
- **Context Windows**: Varies by model (typically 128K+ tokens)
- **Supported Formats**: Text, images
- **Function Calling**: JSON schema-based tools
- **Streaming**: Server-Sent Events support
- **Deferred Processing**: Async completion support

### Code Examples

#### Python with OpenAI SDK
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-xai-api-key",
    base_url="https://api.x.ai/v1"
)

response = client.chat.completions.create(
    model="grok-4",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)
```

#### Function Calling
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]

response = client.chat.completions.create(
    model="grok-4",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools
)
```

---

## Groq

### API Endpoints
**Base URL**: `https://api.groq.com/openai/v1`

#### Core Endpoints
- **Chat Completions**: `POST /chat/completions`
- **Audio Transcription**: `POST /audio/transcriptions`
- **Audio Translation**: `POST /audio/translations`
- **Models**: `GET /models`, `GET /models/{model_id}`
- **Batches**: `POST /batches`, `GET /batches/{batch_id}`, `POST /batches/{batch_id}/cancel`
- **Files**: `POST /files`, `GET /files`, `GET /files/{file_id}`, `DELETE /files/{file_id}`

### Authentication
```bash
Authorization: Bearer YOUR_GROQ_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Chat Completions Example
```bash
curl "https://api.groq.com/openai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [
      {"role": "user", "content": "Explain the importance of fast language models"}
    ]
  }'
```

#### Response Format
```json
{
  "id": "chatcmpl-f51b2cd2-bef7-417e-964e-a08f0b513c22",
  "object": "chat.completion",
  "created": 1730241104,
  "model": "llama3-8b-8192",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Fast language models have gained significant attention..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "queue_time": 0.037493756,
    "prompt_tokens": 18,
    "completion_tokens": 556,
    "total_tokens": 574
  }
}
```

#### Audio Transcription Example
```bash
curl "https://api.groq.com/openai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@./sample_audio.m4a" \
  -F model="whisper-large-v3"
```

### Rate Limits
- Varies by model and subscription tier
- Free tier available with lower limits
- Batch API offers 50% cost reduction for async processing

### Error Codes
- **400**: Bad Request - Invalid request format
- **401**: Unauthorized - Invalid API key
- **429**: Rate limit exceeded
- **500**: Internal server error

### SDKs
- Compatible with OpenAI SDKs
- Official Python and JavaScript clients available

### Pricing (USD per 1M tokens)

#### Language Models (Examples)
| Model | Input | Output |
|-------|-------|--------|
| Llama 3.1 8B Instant | $0.05 | $0.08 |
| Llama 4 Scout 17B×16E | $0.11 | $0.34 |
| Kimi K2 1T | $1.00 | $3.00 |

#### Audio Models
| Model | Price |
|-------|-------|
| Whisper Large v3 Turbo | $0.04/hour |
| Distil-Whisper | $0.02/hour |

#### Text-to-Speech
| Model | Price |
|-------|-------|
| PlayAI Dialog v1.0 | $50/1M characters |

### Technical Specifications
- **Context Windows**: Up to 128K tokens (varies by model)
- **Supported Formats**: Text, audio
- **Streaming**: Server-Sent Events
- **Batch Processing**: Async job processing
- **Ultra-fast inference**: Optimized for speed

### Code Examples

#### Python Example
```python
from groq import Groq

client = Groq(api_key="your-groq-api-key")

chat_completion = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Explain quantum physics"}
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)
```

#### Streaming Response
```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Tell me a story"}],
    model="llama-3.3-70b-versatile",
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

---

## Anthropic Claude

### API Endpoints
**Base URL**: `https://api.anthropic.com/v1`

#### Core Endpoints
- **Messages**: `POST /messages`
- **Messages Streaming**: `POST /messages` (with `stream: true`)
- **Models**: Information available through console

### Authentication
```bash
x-api-key: YOUR_ANTHROPIC_API_KEY
Content-Type: application/json
anthropic-version: 2023-06-01
```

### Request/Response Formats

#### Messages Example
```bash
curl "https://api.anthropic.com/v1/messages" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, Claude"}
    ]
  }'
```

#### Python Example
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude"}
    ]
)
print(message.content)
```

### Rate Limits
- Tier-based system based on usage and payment history
- Higher tiers unlock increased rate limits
- Enterprise customers get dedicated capacity

### Error Codes
- **400**: Bad Request - Invalid request
- **401**: Unauthorized - Invalid API key
- **403**: Forbidden - Permission denied
- **429**: Rate limit exceeded
- **500**: Internal server error

### SDKs
- **Python**: `pip install anthropic`
- **TypeScript**: `npm install @anthropic-ai/sdk`

### Pricing (USD per 1M tokens)

#### Claude Models
| Model | Input | Output | Cached Input | Cached Read |
|-------|-------|--------|--------------|-------------|
| Claude Opus 4 | $15.00 | $75.00 | $18.75 | $1.50 |
| Claude Sonnet 4 | $3.00 | $15.00 | $3.75 | $0.30 |
| Claude Haiku 3.5 | $0.80 | $4.00 | $1.00 | $0.08 |

#### Additional Tools
- **Web Search**: $10/1k searches
- **Code Execution**: $0.05/hour (first 50 hours free daily)

### Technical Specifications
- **Context Windows**: Up to 200K tokens
- **Max Output**: Up to 4,096 tokens
- **Supported Formats**: Text, images, documents
- **Vision**: Image analysis capabilities
- **Tool Use**: Function calling support
- **Streaming**: Server-Sent Events

### Code Examples

#### Streaming Response
```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

#### Vision Example
```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image_data
                    }
                },
                {"type": "text", "text": "What's in this image?"}
            ]
        }
    ]
)
```

---

## Perplexity AI

### API Endpoints
**Base URL**: `https://api.perplexity.ai`

#### Core Endpoints
- **Chat Completions**: `POST /chat/completions`

### Authentication
```bash
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Chat Completions Example
```bash
curl "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [
      {"role": "user", "content": "What is Retrieval-Augmented Generation (RAG)?"}
    ],
    "temperature": 0.5,
    "max_tokens": 500
  }'
```

#### Python Example
```python
import requests

url = "https://api.perplexity.ai/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "sonar-pro",
    "messages": [
        {"role": "system", "content": "Be precise."},
        {"role": "user", "content": "How many moons does Mars have?"}
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

#### Response Format
```json
{
  "id": "unique-request-id",
  "model": "sonar-pro",
  "created": 1234567890,
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  },
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response with citations and sources"
      },
      "finish_reason": "stop"
    }
  ],
  "citations": ["https://source1.com", "https://source2.com"]
}
```

### Rate Limits
- Model-specific rate limits
- Different tiers available
- Check API Portal for current limits

### Error Codes
- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Invalid API key
- **429**: Rate limit exceeded
- **500**: Internal server error

### SDKs
- Compatible with OpenAI SDK format
- Community-maintained clients available

### Pricing
- Varies by model (sonar, sonar-pro, sonar-reasoning, etc.)
- Token-based pricing
- Contact for enterprise pricing

### Technical Specifications
- **Real-time Search**: Web-grounded responses
- **Citations**: Automatic source attribution
- **Streaming**: Partial response streaming
- **Domain Filtering**: Search specific domains
- **Structured Outputs**: JSON schema support

### Code Examples

#### Streaming Response
```python
payload = {
    "model": "sonar-pro",
    "messages": [{"role": "user", "content": "Latest AI news"}],
    "stream": True
}

response = requests.post(url, headers=headers, json=payload, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

#### Domain-Specific Search
```python
payload = {
    "model": "sonar-pro",
    "messages": [{"role": "user", "content": "Recent research on quantum computing"}],
    "search_domain_filter": ["arxiv.org", "nature.com"]
}
```

---

## Moonshot AI

### API Endpoints
**Base URL**: `https://api.moonshot.ai/v1`

#### Core Endpoints
- **Chat Completions**: `POST /chat/completions`
- **Models**: `GET /models`
- **Files**: `POST /files`, `GET /files`, `DELETE /files/{file_id}`
- **Context Caching**: `POST /cache/contexts`

### Authentication
```bash
Authorization: Bearer YOUR_MOONSHOT_API_KEY
Content-Type: application/json
```

### Request/Response Formats

#### Chat Completions Example
```python
from openai import OpenAI

client = OpenAI(
    api_key="$MOONSHOT_API_KEY",
    base_url="https://api.moonshot.ai/v1",
)

completion = client.chat.completions.create(
    model="kimi-k2-0711-preview",
    messages=[
        {"role": "system", "content": "You are Kimi, an AI assistant provided by Moonshot AI."},
        {"role": "user", "content": "Hello, my name is Li Lei. What is 1+1?"}
    ],
    temperature=0.6,
)
print(completion.choices[0].message.content)
```

#### cURL Example
```bash
curl "https://api.moonshot.ai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  -d '{
    "model": "kimi-k2-0711-preview",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

#### Response Format
```json
{
  "id": "cmpl-04ea926191a14749b7f2c7a48a68abc6",
  "object": "chat.completion",
  "created": 1698999496,
  "model": "kimi-k2-0711-preview",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello, Li Lei! 1+1 equals 2."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 19,
    "completion_tokens": 21,
    "total_tokens": 40
  }
}
```

### Rate Limits
- Model-specific limits
- Context window limits up to 128K tokens
- File upload and processing limits

### Error Codes
- **400**: content_filter - High-risk content rejected
- **400**: invalid_request_error - Invalid request format
- **401**: invalid_authentication_error - API key invalid
- **429**: rate_limit_reached_error - Rate limit exceeded
- **500**: server_error - Internal server error

### SDKs
- **OpenAI SDK Compatible**: Use existing OpenAI SDKs
- **LangChain**: `langchain-community.llms.moonshot.Moonshot`
- **Continue.dev**: Built-in provider support

### Pricing

#### Tool Calling
| Tool | Price |
|------|-------|
| Web Search | $0.005 per call |

#### Token Pricing
- Base model pricing varies by model
- Additional charges for search results tokens
- Context caching available for cost optimization

### Technical Specifications
- **Context Windows**: Up to 128K tokens (K2 series)
- **Supported Formats**: Text, images, documents
- **Function Calling**: JSON schema-based tools
- **Web Search**: Built-in `$web_search` tool
- **Vision**: Multimodal support in vision models
- **Streaming**: Server-Sent Events support
- **File Q&A**: Document upload and analysis

### Code Examples

#### Multi-turn Conversation
```python
def chat(query, history):
    history.append({"role": "user", "content": query})
    completion = client.chat.completions.create(
        model="kimi-k2-0711-preview",
        messages=history,
        temperature=0.6,
    )
    result = completion.choices[0].message.content
    history.append({"role": "assistant", "content": result})
    return result
```

#### Vision Model Example
```python
response = client.chat.completions.create(
    model="moonshot-v1-8k-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                {"type": "text", "text": "Describe this image"}
            ]
        }
    ]
)
```

#### Web Search Tool
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "$web_search",
            "description": "Search the web for current information"
        }
    }
]

response = client.chat.completions.create(
    model="kimi-k2-0711-preview",
    messages=[{"role": "user", "content": "What's the latest news about AI?"}],
    tools=tools
)
```

---

## Qwen (Alibaba)

### API Endpoints

#### OpenAI-Compatible
**Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Chat Completions**: `POST /chat/completions`

#### DashScope Native
**Base URL**: `https://dashscope.aliyuncs.com/api/v1`
- **Text Generation**: `POST /services/aigc/text-generation/generation`

### Authentication

#### OpenAI-Compatible
```bash
Authorization: Bearer YOUR_DASHSCOPE_API_KEY
Content-Type: application/json
```

#### DashScope Native
```bash
Authorization: Bearer YOUR_DASHSCOPE_API_KEY
X-DashScope-SSE: enable  # for streaming
```

### Request/Response Formats

#### OpenAI-Compatible Example
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"}
    ]
)
print(completion.model_dump_json())
```

#### cURL Example
```bash
curl "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "你是谁？"}
    ]
  }'
```

#### DashScope Native Example
```python
import dashscope

response = dashscope.Generation.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"}
    ],
    result_format='message'
)
print(response)
```

#### Response Format
```json
{
  "id": "chatcmpl-6ada9ed2-7f33-9de2-8bb0-78bd4035025a",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "我是阿里云开发的超大规模语言模型，我叫通义千问。"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 3019,
    "completion_tokens": 104,
    "total_tokens": 3123
  }
}
```

### Rate Limits
- Model-specific QPS limits
- Token quotas per model
- Free quotas available after enabling DashScope

### Error Codes
- **400**: data_inspection_failed - Content filtering triggered
- **429**: Rate limit exceeded
- **500**: Internal server error

### SDKs
- **Python**: `pip install dashscope` or use OpenAI SDK
- **Java**: Official Java SDK available
- **Node.js**: Use OpenAI SDK with custom base URL

### Pricing (CNY per 1K tokens)

#### Qwen3-Coder Series
| Model | Context | Input | Output |
|-------|---------|-------|--------|
| Qwen3-Coder-Plus | 1M tokens | ¥0.004-¥0.01 | ¥0.016-¥0.1 |
| Qwen-Coder-Plus | 131K tokens | ¥0.0035 | ¥0.007 |
| Qwen-Coder-Turbo | 131K tokens | ¥0.002 | ¥0.006 |

#### Other Models
- **qwen2.5-coder-32b-instruct**: ¥0.002 input, ¥0.006 output
- **qwen2.5-coder-7b-instruct**: ¥0.001 input, ¥0.002 output

### Technical Specifications
- **Context Windows**: Up to 1M tokens (varies by model)
- **Supported Formats**: Text, images, video, audio
- **Multimodal**: Vision and audio capabilities
- **Function Calling**: Tool use support
- **Streaming**: Server-Sent Events
- **Thinking Mode**: Available on Qwen3 models

### Code Examples

#### Multimodal Input (Image)
```bash
curl "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-vl-plus",
    "messages": [{
      "role": "user",
      "content": [
        {"type":"image_url","image_url":{"url":"https://i.pinimg.com/736x/48/58/79/4858795ff3a17f19440dfd6318633bee.jpg"}},
        {"type":"text","text":"这是什么？"}
      ]
    }]
  }'
```

#### Streaming Response
```python
stream = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a story"}
    ],
    stream=True,
    stream_options={"include_usage": True}
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

#### Tool Calling Example
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          }
        }
      }
    }
  ]
}
```

#### Qwen3 Thinking Mode
```python
completion = client.chat.completions.create(
    model="qwen3-plus",
    messages=[{"role": "user", "content": "Solve this math problem step by step"}],
    extra_body={"enable_thinking": True}
)
```

---

## Summary Comparison

| Provider | Base URL | Auth Method | Key Features | Pricing Range |
|----------|----------|-------------|--------------|---------------|
| **OpenAI** | `api.openai.com/v1` | Bearer Token | GPT-4.1, o3, Realtime API, Vision, Tools | $0.10-$8.00/1M tokens |
| **Google Gemini** | `generativelanguage.googleapis.com/v1beta` | API Key Header | Multimodal, 1M+ context, Free tier | Free-$15.00/1M tokens |
| **xAI (Grok)** | `api.x.ai/v1` | Bearer Token | Grok models, Image generation | Variable pricing |
| **Groq** | `api.groq.com/openai/v1` | Bearer Token | Ultra-fast inference, Llama models | $0.05-$3.00/1M tokens |
| **Anthropic Claude** | `api.anthropic.com/v1` | API Key Header | Claude 3.5, 200K context, Safety focus | $0.80-$75.00/1M tokens |
| **Perplexity AI** | `api.perplexity.ai` | Bearer Token | Real-time search, Citations | Variable pricing |
| **Moonshot AI** | `api.moonshot.ai/v1` | Bearer Token | Kimi models, 128K context, Web search | $0.005/search call |
| **Qwen** | `dashscope.aliyuncs.com` | Bearer Token | Multimodal, Thinking mode, Free quotas | ¥0.001-¥0.1/1K tokens |

---

## Best Practices

### General Guidelines
1. **API Key Security**: Store keys in environment variables, never in code
2. **Rate Limiting**: Implement exponential backoff for retry logic
3. **Error Handling**: Always handle HTTP errors and API-specific error codes
4. **Cost Optimization**: Use appropriate models for tasks, implement caching
5. **Monitoring**: Track usage, costs, and performance metrics

### Code Example: Universal Error Handling
```python
import time
import random
from typing import Any, Dict

def api_call_with_retry(api_func, max_retries=3, base_delay=1):
    """Universal retry logic for API calls"""
    for attempt in range(max_retries):
        try:
            return api_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
    
    return None
```

### Environment Setup Example
```bash
# .env file
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
XAI_API_KEY=xai-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
MOONSHOT_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
```

---

*Last updated: July 24, 2025*  
*Sources: Official API documentation from each provider*