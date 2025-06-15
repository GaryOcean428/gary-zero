# from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

# def search(query: str, results = 5, region = "wt-wt", time="y") -> str:
#     # Create an instance with custom parameters
#     api = DuckDuckGoSearchAPIWrapper(
#         region=region,  # Set the region for search results
#         safesearch="off",  # Set safesearch level (options: strict, moderate, off)
#         time=time,  # Set time range (options: d, w, m, y)
#         max_results=results  # Set maximum number of results to return
#     )
#     # Perform a search
#     result = api.run(query)
#     return result

from duckduckgo_search import DDGS


def search(query: str, results=5, region="wt-wt", time="y") -> list[str]:

    with DDGS() as ddgs:
        src = ddgs.text(
            query,
            region=region,  # Specify region
            safesearch="off",  # SafeSearch setting
            timelimit=time,  # Time limit (y = past year)
        )
        results = []
        if src:
            for r in src:
                results.append(str(r))
        return results
