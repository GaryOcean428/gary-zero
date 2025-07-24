from openai import OpenAI

import models


def perplexity_search(
    query: str,
    model_name="sonar-reasoning-pro",  # Updated to use modern Sonar Reasoning Pro instead of legacy sonar-large
    api_key=None,
    base_url="https://api.perplexity.ai",
):
    """Search using Perplexity's Sonar models.

    Args:
        query: The search query
        model_name: The model to use (default: sonar-reasoning-pro - modern model)
        api_key: Perplexity API key (optional, will use env var if not provided)
        base_url: Perplexity API base URL

    Returns:
        str: The search result content

    Note:
        Default model updated to 'sonar-reasoning-pro' (released Feb 2025)
        instead of legacy 'llama-3.1-sonar-large-128k-online' for better
        performance and modern capabilities.
    """
    api_key = api_key or models.get_api_key("perplexity")

    client = OpenAI(api_key=api_key, base_url=base_url)

    messages = [
        # It is recommended to use only single-turn conversations and avoid system prompts for the online LLMs (sonar-small-online and sonar-medium-online).
        # {
        #     "role": "system",
        #     "content": (
        #         "You are an artificial intelligence assistant and you need to "
        #         "engage in a helpful, detailed, polite conversation with a user."
        #     ),
        # },
        {
            "role": "user",
            "content": (query),
        },
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,  # type: ignore
    )
    result = response.choices[0].message.content  # only the text is returned
    return result
