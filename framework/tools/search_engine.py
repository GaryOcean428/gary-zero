from framework.helpers.errors import handle_error
from framework.helpers.duckduckgo_search import search_async as duckduckgo_search
from framework.helpers.tool import Response, Tool

SEARCH_ENGINE_RESULTS = 10


class SearchEngine(Tool):
    async def execute(self, query="", **kwargs):

        search_result = await self.duckduckgo_search(query)

        await self.agent.handle_intervention(
            search_result
        )  # wait for intervention and handle it, if paused

        return Response(message=search_result, break_loop=False)

    async def duckduckgo_search(self, question):
        results = await duckduckgo_search(question, max_results=SEARCH_ENGINE_RESULTS)
        return self.format_result_search(results, "Search Engine")

    def format_result_search(self, result, source):
        if isinstance(result, Exception):
            handle_error(result)
            return f"{source} search failed: {str(result)}"

        if 'error' in result:
            return f"{source} search failed: {result['error']}"

        outputs = []
        for item in result["results"]:
            outputs.append(f"{item['title']}\n{item['url']}\n{item['content']}")

        return "\n\n".join(outputs[:SEARCH_ENGINE_RESULTS]).strip()
