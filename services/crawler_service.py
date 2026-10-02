class CrawlerService:

    @staticmethod
    def get_page_text(page, url: str):
        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=12000
            )
            page.wait_for_timeout(800)
            return page.locator("body").inner_text()
        except Exception as e:
            print(f"[CrawlerService] Page navigation notice ({url[:60]}...): {e}")
            return ""

    @staticmethod
    def current_url(page) -> str:
        try:
            return page.url
        except Exception:
            return ""
