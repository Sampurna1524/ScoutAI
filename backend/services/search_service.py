from services.browser_service import BrowserService


class SearchService:

    @staticmethod
    def search(query: str, max_results: int = 10):
        results = BrowserService.search_google(query)
        formatted = [{"title": r.title, "href": r.url} for r in results[:max_results]]
        return formatted