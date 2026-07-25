from playwright.sync_api import sync_playwright
from models.search_result import SearchResult


class BrowserService:

    @staticmethod
    def search_duckduckgo(query: str):

        search_results = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            page.goto("https://duckduckgo.com")

            page.locator("input[name='q']").fill(query)

            page.keyboard.press("Enter")

            page.wait_for_selector(
                "a[data-testid='result-title-a']",
                timeout=15000
            )

            results = page.locator("a[data-testid='result-title-a']")

            for i in range(results.count()):

                title = results.nth(i).inner_text()

                url = results.nth(i).get_attribute("href")

                search_results.append(
                    SearchResult(
                        title=title,
                        url=url
                    )
                )

            browser.close()

        return search_results