import os
import time

from dotenv import load_dotenv
load_dotenv(verbose=True)

from typing import List
from firecrawl import FirecrawlApp
import asyncio

from src.tools.search.base import WebSearchEngine, SearchItem

def search(params):
    """
    Perform a Google search using the provided parameters.
    Returns a list of SearchItem objects.
    """
    app = FirecrawlApp(
        api_key=os.getenv("FIRECRAWL_API_KEY"),
    )

    response = app.search(
        query=params["q"],
        limit= params.get("num", 10),
        tbs= params.get("tbs", ""),
    )

    data = response.data

    results = []
    for item in data:
        title = item.get("title", "")
        url = item.get("url", "")
        description = item.get("description", "")
        results.append(SearchItem(title=title,
                                  url=url,
                                  description=description))

    return results

class FirecrawlSearchEngine(WebSearchEngine):
    async def perform_search(
        self,
        query: str,
        num_results: int = 10,
        filter_year: int = None,
        *args, **kwargs
    ) -> List[SearchItem]:
        """
        Google search engine.

        Returns results formatted according to SearchItem model.
        """
        params = {
            "q": query,
            "num": num_results,
        }
        if filter_year is not None:
            params["tbs"] = f"cdr:1,cd_min:01/01/{filter_year},cd_max:12/31/{filter_year}"

        results = search(params)

        return results


if __name__ == '__main__':
    # Example usage
    start_time = time.time()
    search_engine = FirecrawlSearchEngine()
    query = "OpenAI GPT-4"
    results = asyncio.run(search_engine.perform_search(query, num_results=5))

    for item in results:
        print(f"Title: {item.title}\nURL: {item.url}\nDescription: {item.description}\n")

    end_time = time.time()

    print(end_time - start_time, "seconds elapsed for search")