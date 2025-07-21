"""
SearchXNG tool for Gary Zero agent.
Provides web search capabilities using Railway-hosted SearchXNG service.
"""

import os
import aiohttp
from framework.helpers.tool import Response, Tool
from framework.helpers.print_style import PrintStyle


class SearchXng(Tool):
    """Search tool using Railway-hosted SearchXNG service."""
    
    def __init__(self, agent, name: str, method: str | None, args: dict[str, str], message: str, **kwargs):
        super().__init__(agent, name, method, args, message, **kwargs)
        
        # Get SearchXNG URL with proper fallback handling
        self.searxng_url = os.getenv('SEARXNG_URL', '')
        
        # Check if URL contains unresolved Railway reference variables
        if not self.searxng_url or '${{' in self.searxng_url:
            # Try Railway internal domain as fallback
            if os.getenv('RAILWAY_ENVIRONMENT'):
                self.searxng_url = 'http://searchxng.railway.internal:8080'
                PrintStyle(font_color="#FFA500").print(
                    f"⚠️  Using fallback SearchXNG URL: {self.searxng_url}"
                )
            else:
                # Local development fallback
                self.searxng_url = 'http://localhost:55510'
        
        # Log the URL being used
        PrintStyle(font_color="#85C1E9").print(f"🔍 SearchXNG URL: {self.searxng_url}")
    
    async def execute(self, **kwargs):
        """Perform search using SearchXNG."""
        
        query = self.args.get("query", "")
        category = self.args.get("category", "general")
        
        if not query:
            return Response(message="Error: Search query is required", break_loop=False)
        
        try:
            PrintStyle(font_color="#85C1E9").print(f"🔍 Searching with SearchXNG: {query}")
            
            results = await self._search_searchxng(query, category)
            
            if isinstance(results, dict) and 'error' in results:
                error_msg = f"❌ SearchXNG search failed: {results['error']}"
                PrintStyle.error(error_msg)
                
                # Suggest fallback to DuckDuckGo if SearchXNG fails
                if 'connection' in results['error'].lower():
                    error_msg += "\n💡 Hint: SearchXNG may not be accessible. Consider using DuckDuckGo as fallback."
                
                return Response(message=error_msg, break_loop=False)
            
            formatted_results = self._format_search_results(results, "SearchXNG")
            
            await self.agent.handle_intervention(formatted_results)
            
            return Response(message=formatted_results, break_loop=False)
            
        except Exception as e:
            error_msg = f"❌ SearchXNG tool error: {str(e)}"
            PrintStyle.error(error_msg)
            return Response(message=error_msg, break_loop=False)
    
    async def _search_searchxng(self, query: str, category: str = "general"):
        """Perform search using SearchXNG API."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'category': category,
                    'format': 'json'
                }
                
                search_url = f"{self.searxng_url}/search"
                
                async with session.get(search_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    else:
                        return {"error": f"SearchXNG returned status {response.status}"}
                        
        except aiohttp.ClientError as e:
            return {"error": f"SearchXNG connection failed: {str(e)}"}
        except Exception as e:
            return {"error": f"SearchXNG request error: {str(e)}"}
    
    def _format_search_results(self, results, source):
        """Format search results for display."""
        if isinstance(results, dict) and 'error' in results:
            return f"{source} search failed: {results['error']}"
        
        if not results:
            return f"No results found using {source}"
        
        formatted = f"🔍 Search results from {source}:\n\n"
        
        for i, result in enumerate(results[:10], 1):  # Limit to top 10 results
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('content', 'No description')
            
            # Truncate content if too long
            if len(content) > 200:
                content = content[:197] + "..."
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   URL: {url}\n"
            formatted += f"   {content}\n\n"
        
        return formatted

    def get_log_object(self):
        return self.agent.context.log.log(
            type="searchxng",
            heading=f"{self.agent.agent_name}: Using SearchXNG search",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message)
