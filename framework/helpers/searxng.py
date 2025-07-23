import os

import aiohttp

from framework.helpers import runtime

# Use Railway's internal service URL for SearXNG, fallback to localhost for development
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://localhost:55510')
URL = f"{SEARXNG_URL}/search"


async def search(query: str):
    return await runtime.call_development_function(_search, query=query)


async def _search(query: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(URL, data={"q": query, "format": "json"}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"SearXNG returned status {response.status}")
    except Exception as e:
        # Return error in the expected format for fallback handling
        return {"results": [], "error": f"SearXNG connection failed: {str(e)}"}
