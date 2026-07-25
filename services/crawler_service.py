from playwright.sync_api import sync_playwright


class CrawlerService:

    @staticmethod
    def get_page_text(url: str):

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            page.goto(url, wait_until="networkidle")

            text = page.locator("body").inner_text()

            browser.close()

            return text