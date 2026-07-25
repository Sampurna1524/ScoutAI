from services.browser_service import BrowserService


class JobAgent:

    def search_jobs(self, query):

        return BrowserService.search_duckduckgo(query)