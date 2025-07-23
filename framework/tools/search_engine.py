from framework.helpers.duckduckgo_search import search_async as duckduckgo_search
from framework.helpers.errors import handle_error
from framework.helpers.searxng import search as searxng_search
from framework.helpers.tool import Response, Tool

SEARCH_ENGINE_RESULTS = 10


class SearchEngine(Tool):
    async def execute(self, query="", **kwargs):

        # Try SearXNG first, fallback to DuckDuckGo if it fails
        search_result = await self.searxng_search_with_fallback(query)

        await self.agent.handle_intervention(
            search_result
        )  # wait for intervention and handle it, if paused

        return Response(message=search_result, break_loop=False)

    async def searxng_search_with_fallback(self, question):
        """Try SearXNG first, fallback to DuckDuckGo if SearXNG fails"""
        try:
            # Attempt SearXNG search first
            results = await searxng_search(question)

            # Check if SearXNG returned an error
            if isinstance(results, dict) and 'error' in results:
                print(f"SearXNG failed: {results['error']}, falling back to DuckDuckGo")
                results = await duckduckgo_search(question, max_results=SEARCH_ENGINE_RESULTS)
                return self.format_result_search(results, "DuckDuckGo (fallback)")

            return self.format_result_search(results, "SearXNG")

        except Exception as e:
            print(f"SearXNG error: {str(e)}, falling back to DuckDuckGo")
            # Fallback to DuckDuckGo if SearXNG fails
            results = await duckduckgo_search(question, max_results=SEARCH_ENGINE_RESULTS)
            return self.format_result_search(results, "DuckDuckGo (fallback)")

    async def duckduckgo_search(self, question):
        """Direct DuckDuckGo search method (kept for compatibility)"""
        results = await duckduckgo_search(question, max_results=SEARCH_ENGINE_RESULTS)
        return self.format_result_search(results, "DuckDuckGo")

    def format_result_search(self, result, source):
        if isinstance(result, Exception):
            handle_error(result)
            return f"{source} search failed: {str(result)}"

        if isinstance(result, dict) and 'error' in result:
            return f"{source} search failed: {result['error']}"

        # Handle both SearXNG and DuckDuckGo result formats
        results_list = result.get("results", []) if isinstance(result, dict) else result

        outputs = []
        for item in results_list:
            if isinstance(item, dict):
                # DuckDuckGo format or properly formatted SearXNG
                title = item.get('title', '')
                url = item.get('url', item.get('href', ''))
                content = item.get('content', item.get('body', ''))
            else:
                # Raw SearXNG format (if any)
                title = getattr(item, 'title', str(item))
                url = getattr(item, 'url', '')
                content = getattr(item, 'content', '')

            outputs.append(f"{title}\n{url}\n{content}")

        return "\n\n".join(outputs[:SEARCH_ENGINE_RESULTS]).strip()
