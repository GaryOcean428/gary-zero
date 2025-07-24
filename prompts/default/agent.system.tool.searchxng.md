### searchxng

search the web using private SearchXNG service for current information
use for research, fact-checking, and finding latest information
enter search "query" in tool_args; optionally specify "category"
categories: "general", "news", "science", "tech", "social media", etc.
provides privacy-focused search results without tracking
usage:

1 general web search

~~~json
{
    "thoughts": [
        "Need to search for current information about...",
        "SearchXNG will provide privacy-focused results...",
    ],
    "tool_name": "searchxng",
    "tool_args": {
        "query": "latest AI developments 2024",
        "category": "general"
    }
}
~~~

2 news search

~~~json
{
    "thoughts": [
        "Looking for recent news about...",
    ],
    "tool_name": "searchxng",
    "tool_args": {
        "query": "quantum computing breakthrough",
        "category": "news"
    }
}
~~~
