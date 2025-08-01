# OpenAI Models Comprehensive Documentation

*Research compiled from official OpenAI platform documentation (platform.openai.com) and OpenAI pricing pages (openai.com/api/pricing)*

## Table of Contents
1. [GPT Models](#gpt-models)
2. [Reasoning Models (o-series)](#reasoning-models-o-series)
3. [Image Generation Models](#image-generation-models)
4. [Audio Models](#audio-models)
5. [Embedding Models](#embedding-models)
6. [Moderation Models](#moderation-models)
7. [Pricing Summary](#pricing-summary)
8. [API Endpoints Reference](#api-endpoints-reference)

---

## GPT Models

### GPT-4.1 Series (Latest Generation)

#### GPT-4.1
- **Purpose**: High-intelligence text model for everyday tasks
- **Context Window**: 200,000 tokens
- **Maximum Output**: 100,000 tokens
- **Modalities**: Text input → Text output
- **Knowledge Cutoff**: June 1, 2024
- **Features**:
  - Streaming: Supported
  - Function calling: Supported
  - Structured outputs: Supported
  - Fine-tuning: Supported
- **Pricing** (per 1M tokens):
  - Input: $2.00
  - Cached Input: $0.50
  - Output: $8.00
- **Fine-tuning Pricing** (per 1M tokens):
  - Input: $3.00
  - Cached: $0.75
  - Output: $12.00
  - Training: $25.00

#### GPT-4.1 mini
- **Purpose**: Smaller, faster, cost-efficient variant
- **Context Window**: 200,000 tokens
- **Maximum Output**: 100,000 tokens
- **Modalities**: Text input → Text output
- **Knowledge Cutoff**: June 1, 2024
- **Features**: Same as GPT-4.1
- **Pricing** (per 1M tokens):
  - Input: $0.40
  - Cached Input: $0.10
  - Output: $1.60
- **Fine-tuning Pricing** (per 1M tokens):
  - Input: $0.80
  - Cached: $0.20
  - Output: $3.20
  - Training: $5.00

#### GPT-4.1 nano
- **Purpose**: Ultra-lightweight variant for high-volume applications
- **Context Window**: 200,000 tokens
- **Maximum Output**: 100,000 tokens
- **Modalities**: Text input → Text output
- **Knowledge Cutoff**: June 1, 2024
- **Features**: Same as GPT-4.1
- **Pricing** (per 1M tokens):
  - Input: $0.10
  - Cached Input: $0.025
  - Output: $0.40
- **Fine-tuning Pricing** (per 1M tokens):
  - Input: $0.20
  - Cached: $0.05
  - Output: $0.80
  - Training: $1.50

### GPT-4o Series (Multimodal)

#### GPT-4o ("Omni")
- **Purpose**: Flagship multimodal model
- **Context Window**: 128,000 tokens
- **Maximum Output**: 4,096 tokens
- **Modalities**: Text + Image input → Text output
- **Knowledge Cutoff**: April 2024
- **Features**:
  - Streaming: Supported
  - Function calling: Supported
  - Structured outputs: Supported
  - Fine-tuning: Supported
  - Vision capabilities: Supported
- **Pricing** (per 1M tokens):
  - Input: $2.50
  - Cached Input: $1.25
  - Output: $5.00
- **Realtime API Pricing** (per 1M tokens):
  - Text Input: $5.00
  - Text Output: $20.00
  - Audio Input: $40.00
  - Audio Output: $80.00
  - Cached Input: $2.50

#### GPT-4o mini
- **Purpose**: Smaller, cost-effective multimodal model
- **Context Window**: 128,000 tokens
- **Maximum Output**: 16,384 tokens
- **Modalities**: Text + Image input → Text output
- **Knowledge Cutoff**: October 2023
- **Features**: Same as GPT-4o
- **Pricing** (per 1M tokens):
  - Input: $0.15
  - Cached Input: $0.075
  - Output: $0.60
- **Realtime API Pricing** (per 1M tokens):
  - Text Input: $0.60
  - Text Output: $2.40
  - Audio Input: $10.00
  - Audio Output: $20.00
  - Cached Input: $0.30

#### GPT-4o Realtime
- **Purpose**: Low-latency voice-interactive applications
- **Features**:
  - Sub-100ms end-to-end latency
  - WebRTC/WebSocket support
  - Streaming audio + text inputs
  - Real-time response generation
- **Use Cases**: Live captioning, voice agents, interactive applications

### GPT-4 (Previous Generation) do not use

#### GPT-4
- **Purpose**: High-intelligence text model for chat completions
- **Context Window**: 8,192 tokens
- **Maximum Output**: 8,192 tokens
- **Modalities**: Text input → Text output
- **Features**:
  - Streaming: Supported
  - Function calling: Not supported
  - Structured outputs: Not supported
  - Fine-tuning: Supported
- **Pricing** (per 1M tokens):
  - Input: $30.00
  - Output: $60.00
- **Rate Limits** (varies by tier):
  - Tier 1: 500 RPM, 10,000 TPM
  - Tier 5: 10,000 RPM, 1,000,000 TPM

### GPT-3.5 Series do not use

#### GPT-3.5 Turbo
- **Purpose**: Lower-cost chat-optimized model
- **Context Window**: 16,385 tokens
- **Maximum Output**: 4,096 tokens
- **Knowledge Cutoff**: September 1, 2021
- **Modalities**: Text input → Text output
- **Features**:
  - Streaming: Not supported
  - Function calling: Not supported
  - Structured outputs: Not supported
  - Fine-tuning: Supported
- **Pricing** (per 1M tokens):
  - Input: $0.50
  - Output: $1.50
- **Available Snapshots**:
  - gpt-3.5-turbo
  - gpt-3.5-turbo-0125

---

## Reasoning Models (o-series)

### OpenAI o3
- **Purpose**: Most powerful reasoning model for complex, multi-step tasks
- **Context Window**: 200,000 tokens
- **Maximum Output**: 100,000 tokens
- **Knowledge Cutoff**: June 1, 2024
- **Modalities**: Text + Image input → Text output
- **Features**:
  - Streaming: Supported
  - Function calling: Supported
  - Structured outputs: Supported
  - Fine-tuning: Not supported
  - Advanced reasoning capabilities
- **Pricing** (per 1M tokens):
  - Input: $2.00
  - Cached Input: $0.50
  - Output: $8.00
- **Performance**: Highest reasoning capability, slowest speed
- **Rate Limits**:
  - Tier 1: 500 RPM, 30,000 TPM
  - Tier 5: 10,000 RPM, 30,000,000 TPM

### OpenAI o4-mini
- **Purpose**: Faster, cost-efficient reasoning model
- **Context Window**: 128,000 tokens
- **Maximum Output**: 65,536 tokens
- **Knowledge Cutoff**: October 1, 2023
- **Modalities**: Text input → Text output
- **Features**:
  - Streaming: Supported
  - Function calling: Supported
  - Structured outputs: Supported
  - Fine-tuning: Supported (reinforcement learning)
- **Pricing** (per 1M tokens):
  - Input: $1.10
  - Cached Input: $0.275
  - Output: $4.40
- **Fine-tuning**: $100/hour for reinforcement learning

### o1-mini (Legacy Reasoning)
- **Purpose**: Lightweight reasoning model (consider upgrading to o3-mini)
- **Context Window**: 128,000 tokens
- **Maximum Output**: 65,536 tokens
- **Knowledge Cutoff**: October 1, 2023
- **Modalities**: Text input → Text output
- **Features**:
  - Reasoning tokens: Supported
  - Function calling: Not supported
  - Structured outputs: Not supported
  - Fine-tuning: Not supported
- **Pricing** (per 1M tokens):
  - Input: $1.10
  - Cached Input: $0.55
  - Output: $4.40
- **Available Snapshots**:
  - o1-mini (latest)
  - o1-mini-2024-09-12 (deprecated)

### o1-preview (Legacy Reasoning)
- **Purpose**: Preview snapshot of full o1 reasoning model
- **Context Window**: 200,000 tokens
- **Maximum Output**: 100,000 tokens
- **Knowledge Cutoff**: October 1, 2023
- **Modalities**: Text + Image input → Text output
- **Features**:
  - Chain-of-thought reasoning
  - Streaming: Supported
  - Function calling: Supported
  - Structured outputs: Supported
- **Pricing** (per 1M tokens):
  - Input: $15.00
  - Cached Input: $7.50
  - Output: $60.00
- **Available Snapshots**:
  - o1-preview
  - o1-preview-2024-09-12

---

## Image Generation Models

### GPT Image 1
- **Purpose**: State-of-the-art natively multimodal image generation
- **Modalities**: Text + Image input → Image output
- **Features**:
  - Highest quality image generation
  - Inpainting support
  - Multiple resolution options
- **Pricing**:
  - **Text tokens** (per 1M tokens):
    - Input: $5.00
    - Cached: $1.25
  - **Image tokens** (per 1M tokens):
    - Input: $10.00
    - Cached: $2.50
    - Output: $40.00
  - **Per image generation**:
    - Low quality (1024×1024): $0.011
    - Medium quality (1024×1024): $0.042
    - High quality (1024×1024): $0.167
- **Performance**: Highest quality, slowest speed
- **Rate Limits**:
  - Tier 1: 100,000 TPM, 5 IPM (images per minute)
  - Tier 5: 8,000,000 TPM, 250 IPM

### DALL·E 3
- **Purpose**: Advanced text-to-image generation
- **Features**:
  - More advanced visual reasoning than DALL·E 2
  - Better text rendering within images
  - Improved alignment with user intent
  - Fewer hallucinated details
- **API Endpoint**: `POST https://api.openai.com/v1/images/generations`
- **Parameters**:
  - `prompt` (required): Text description
  - `n` (optional, default=1): Number of images
  - `size` (optional, default="1024x1024"): Image dimensions
  - `response_format` (optional, default="url"): "url" or "b64_json"
  - `user` (optional): End-user identifier

### DALL·E 2
- **Purpose**: General-purpose image generation
- **Features**:
  - High-fidelity samples
  - Coherent composition
  - Broad creative and commercial use
- **API**: Same endpoint and parameters as DALL·E 3
- **Model Selection**: Use `model="dall-e"` in API calls

**Sample Code Example**:

```python
import openai
openai.api_key = "YOUR_API_KEY"

response = openai.Image.create(
    model="dall-e-3",
    prompt="A photorealistic red fox sitting in a snowy forest",
    n=2,
    size="512x512",
    response_format="url"
)
print(response["data"])
```

---

## Audio Models

### Speech-to-Text (Whisper)

#### Whisper-1
- **Purpose**: General-purpose speech recognition
- **Capabilities**:
  - Automatic speech recognition (ASR)
  - Speech translation (multilingual → English)
  - Language identification
- **Input**: Audio (various formats)
- **Output**: Text (UTF-8) with optional timestamps
- **Pricing**: $0.006 per 1M tokens (based on output text length)
- **API Endpoints**:
  - `v1/audio/transcriptions` (ASR/transcription)
  - `v1/audio/translations` (speech-to-English translation)
- **Rate Limits**:
  - Free tier: 3 RPM, 200 RPD
  - Tier 1: 500 RPM
  - Tier 5: 10,000 RPM
- **Available Snapshots**: whisper-1

**Sample Code Example**:

```bash
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F file="@my_audio.wav" \
  -F model="whisper-1"
```

### Text-to-Speech (TTS)

#### GPT-4o mini TTS
- **Purpose**: Balanced speed and naturalness in compact model
- **Use Cases**: Lightweight, real-time applications
- **Features**: Resource-efficient, good quality

#### TTS-1
- **Purpose**: Low latency, real-time streaming
- **Use Cases**: Live interactions, chatbots, voice assistants
- **Features**: Optimized for speed, good naturalness

#### TTS-1 HD
- **Purpose**: Maximum audio quality and expressiveness
- **Use Cases**: Pre-recorded content, audiobooks, high-fidelity requirements
- **Features**: Richer prosody, lifelike intonation

**API Usage**: Specify model name (e.g., `model="tts-1-hd"`) in audio/speech endpoint calls.

---

## Embedding Models

### Overview
Embeddings are numerical vector representations of text that enable semantic similarity computation, clustering, recommendation systems, anomaly detection, and classification tasks.

### text-embedding-3-large
- **Purpose**: High-capacity model for richer semantic encodings
- **Use Cases**: Tasks demanding higher accuracy in similarity judgments
- **Performance**: Best semantic precision
- **Pricing**: $0.00013 per 1K tokens

### text-embedding-3-small
- **Purpose**: Smallest, fastest, most affordable option
- **Use Cases**: Large-scale applications where cost and latency are critical
- **Performance**: Good balance of speed and accuracy
- **Pricing**: $0.00002 per 1K tokens (5× cheaper than ada-002)

### text-embedding-ada-002
- **Purpose**: Prior-generation workhorse embedding model
- **Use Cases**: Balance between performance and cost
- **Status**: Largely superseded by 3-series models
- **Compatibility**: Same dimensionality as newer models

### Common Use Cases
- **Semantic Search**: Compare query embeddings against document corpus
- **Clustering**: Group similar texts or visualize semantic landscapes
- **Recommendations**: Suggest items based on content similarity
- **Anomaly Detection**: Spot outliers using embedding distances
- **Classification**: Use embeddings as input features for ML models

**Sample Code Example**:

```python
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Your text to embed here"
)
vectors = response.data[0].embedding
```

---

## Moderation Models

### Overview
All moderation models are provided **free of charge** for detecting policy-violating or harmful content. They return confidence scores for seven content categories:
- hate
- hate/threatening
- self-harm
- sexual
- sexual/minors
- violence
- violence/graphic

### text-moderation-stable
- **Purpose**: Frozen stable snapshot for consistent long-term usage
- **Input**: Text only
- **Use Case**: Production deployments requiring consistent behavior over time

### text-moderation-latest
- **Purpose**: Most recent text-only moderation model
- **Input**: Text only
- **Use Case**: When you want the latest improvements in detection

### omni-moderation-latest
- **Purpose**: Most capable moderation model
- **Input**: Images + Text
- **Features**:
  - Same seven category classifications
  - Can scan images for policy violations
  - Snapshots available for version consistency

**Sample Code Example**:

```bash
curl https://api.openai.com/v1/moderations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"text-moderation-latest","input":"<YOUR_TEXT_HERE>"}'
```

**Response Format**:

```json
{
  "id": "...",
  "model": "text-moderation-latest",
  "results": [
    {
      "categories": {
        "hate": false,
        "sexual": true,
        ...
      },
      "category_scores": {
        "hate": 0.01,
        "sexual": 0.85,
        ...
      },
      "flagged": true
    }
  ]
}
```

---

## Pricing Summary

### Current Models (2025) - Per 1M Tokens

| Model | Input | Cached Input | Output | Notes |
|-------|-------|--------------|--------|-------|
| **GPT-4.1** | $2.00 | $0.50 | $8.00 | Latest generation |
| **GPT-4.1 mini** | $0.40 | $0.10 | $1.60 | Cost-efficient |
| **GPT-4.1 nano** | $0.10 | $0.025 | $0.40 | Ultra-lightweight |
| **OpenAI o3** | $2.00 | $0.50 | $8.00 | Most powerful reasoning |
| **OpenAI o4-mini** | $1.10 | $0.275 | $4.40 | Efficient reasoning |
| **GPT-4o** | $2.50 | $1.25 | $5.00 | Multimodal flagship |
| **GPT-4o mini** | $0.15 | $0.075 | $0.60 | Multimodal efficient |
| **o1-mini** | $1.10 | $0.55 | $4.40 | Legacy reasoning |
| **o1-preview** | $15.00 | $7.50 | $60.00 | Legacy reasoning |
| **GPT-4** | $30.00 | - | $60.00 | Previous generation |
| **GPT-3.5 Turbo** | $0.50 | - | $1.50 | Legacy chat model |

### Specialized Pricing

#### Realtime API (Text)
- **GPT-4o**: Input $5.00, Output $20.00, Cached $2.50
- **GPT-4o mini**: Input $0.60, Output $2.40, Cached $0.30

#### Realtime API (Audio)
- **GPT-4o**: Input $40.00, Output $80.00, Cached $2.50
- **GPT-4o mini**: Input $10.00, Output $20.00, Cached $0.30

#### Image Generation (GPT-image-1)
- **Text prompts**: Input $5.00, Cached $1.25
- **Image tokens**: Input $10.00, Cached $2.50, Output $40.00
- **Per image**: Low $0.011, Medium $0.042, High $0.167

#### Embeddings (Per 1K Tokens)
- **text-embedding-3-small**: $0.00002
- **text-embedding-3-large**: $0.00013

#### Audio
- **Whisper-1**: $0.006 per 1M tokens

#### Built-in Tools
- **Code Interpreter**: $0.03 per call
- **File Search Storage**: $0.10 per GB per day (first 1GB free)
- **File Search calls**: $2.50 per 1K calls
- **Web Search**: $25 per 1K calls (GPT-4o/4.1), $10 per 1K calls (o3/o4-mini)

### Batch API Discount
- **50% off** input/output rates for all models when using Batch API

---

## API Endpoints Reference

### Core Endpoints
- **Chat Completions**: `v1/chat/completions`
- **Completions (Legacy)**: `v1/completions`
- **Embeddings**: `v1/embeddings`
- **Fine-tuning**: `v1/fine-tuning`
- **Batch**: `v1/batch`
- **Responses**: `v1/responses`
- **Assistants**: `v1/assistants`
- **Realtime**: `v1/realtime`

### Image Endpoints
- **Image Generation**: `v1/images/generations`
- **Image Edit**: `v1/images/edits`

### Audio Endpoints
- **Speech Generation**: `v1/audio/speech`
- **Transcriptions**: `v1/audio/transcriptions`
- **Translations**: `v1/audio/translations`

### Moderation Endpoint
- **Moderation**: `v1/moderations`

### Rate Limits by Tier

| Tier | RPM | TPM | Batch Queue | Notes |
|------|-----|-----|-------------|-------|
| **Free** | 3 | 200 | - | Limited access |
| **Tier 1** | 500-3,500 | 10K-200K | 100K | Entry level |
| **Tier 2** | 5,000 | 450K-2M | 200K | Moderate usage |
| **Tier 3** | 5,000 | 800K-4M | 5M-40M | High usage |
| **Tier 4** | 10,000 | 2M-10M | 30M-1B | Enterprise |
| **Tier 5** | 10,000-30,000 | 1M-150M | 150M-15B | Maximum |

*RPM = Requests Per Minute, TPM = Tokens Per Minute*

### Best Practices

#### Model Selection
- **GPT-4.1 series**: Latest generation for everyday tasks
- **o3/o4-mini**: Complex reasoning and STEM tasks
- **GPT-4o series**: Multimodal applications (text + images)
- **Realtime models**: Low-latency voice interactions
- **Embedding models**: Choose 3-small for cost, 3-large for accuracy

#### Cost Optimization
- Use cached inputs when possible (50% discount)
- Consider Batch API for non-real-time tasks (50% discount)
- Choose appropriate model size for your use case
- Implement proper rate limiting and error handling

#### Fine-tuning
- Supported on: GPT-4.1 series, GPT-4o series, GPT-3.5 Turbo
- Vision fine-tuning available for image understanding tasks
- Reinforcement learning fine-tuning available for o4-mini

---

*This documentation is based on official OpenAI platform documentation as of July 2025. For the most current information, always refer to [platform.openai.com/docs/models](https://platform.openai.com/docs/models) and [openai.com/api/pricing](https://openai.com/api/pricing).*
