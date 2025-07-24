import asyncio

from duckduckgo_search import DDGS


def search(query: str, results=5, region="wt-wt", time="y") -> list[str]:
    """Synchronous DuckDuckGo search - for backward compatibility"""
    with DDGS() as ddgs:
        src = ddgs.text(
            query,
            region=region,  # Specify region
            safesearch="off",  # SafeSearch setting
            timelimit=time,  # Time limit (y = past year)
            max_results=results,
        )
        results = []
        if src:
            for r in src:
                results.append(str(r))
        return results


async def search_async(query: str, max_results=10) -> dict:
    """Async DuckDuckGo search compatible with SearXNG interface"""
    try:
        # Run the synchronous DDGS search in executor to make it async
        loop = asyncio.get_event_loop()

        def _sync_search():
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        query,
                        safesearch="off",
                        max_results=max_results,
                    )
                )

        results = await loop.run_in_executor(None, _sync_search)

        # Format results to match SearXNG format expected by search_engine.py
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "content": result.get("body", ""),
                }
            )

        return {"results": formatted_results}

    except Exception as e:
        return {"results": [], "error": str(e)}
