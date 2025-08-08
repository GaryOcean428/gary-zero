# GPT‑5 Code Examples

The GPT‑5 family of models (released in July 2025) introduces larger context windows and more flexible reasoning controls compared to the GPT‑4.1 series.  The snippets below show how to call each GPT‑5 variant using the OpenAI Python SDK.  The parameters are set to their maximum values for demonstration purposes; adjust them to suit your use case.

## Prerequisites

Install the OpenAI Python client and configure your API key:

```bash
pip install openai
export OPENAI_API_KEY="sk-…"
```

Then import and instantiate the client:

```python
from openai import OpenAI

client = OpenAI()
```

## GPT‑5 Chat (Latest)

Use `gpt‑5‑chat‑latest` for general chat and summarisation tasks.  This model supports up to **16 384** output tokens and allows you to specify the user’s location for search tools.

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5-chat-latest",
    input=[
        {
            "role": "system",
            "content": [
                {"type": "input_text", "text": "insert utility model system prompt."}
            ],
        }
    ],
    text={},  # default format (plain text)
    reasoning={},  # optional reasoning controls
    tools=[],       # no external tools in this example
    temperature=2,
    max_output_tokens=16_384,
    top_p=1,
    store=True,
)

print(response)
```

## GPT‑5 Mini

The `gpt‑5‑mini` variant trades some capability for cost efficiency.  You can request more verbose textual outputs and higher reasoning effort:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5-mini",
    input=[
        {
            "role": "developer",
            "content": [
                {"type": "input_text", "text": "insert utility model system prompt."}
            ],
        }
    ],
    text={
        "format": {"type": "text"},
        "verbosity": "high",
    },
    reasoning={
        "effort": "high",
        "summary": "auto",
    },
    tools=[],
    store=True,
)

print(response)
```

## GPT‑5 Nano

`gpt‑5‑nano` is designed for ultra‑low cost use cases.  It favours succinct outputs and minimal reasoning effort:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5-nano",
    input=[
        {
            "role": "developer",
            "content": [
                {"type": "input_text", "text": "insert utility model system prompt."}
            ],
        }
    ],
    text={
        "format": {"type": "text"},
        "verbosity": "low",
    },
    reasoning={
        "effort": "minimal",
        "summary": "detailed",
    },
    tools=[],
    store=True,
)

print(response)
```

---

**Tip:**  For more information about each GPT‑5 variant, including pricing and performance, see the [AI Models catalog](./ai-models.md).  For comparisons of Anthropic’s Claude models, refer to the [Claude model comparison table](https://docs.anthropic.com/en/docs/about-claude/models/overview#model-comparison-table).