from duckduckgo_search import DDGS


class SearchService:

    @staticmethod
    def search(query: str, max_results: int = 5):
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            print(results)
            return results