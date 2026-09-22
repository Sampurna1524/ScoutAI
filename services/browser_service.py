import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus, urlparse, parse_qs

from playwright.sync_api import sync_playwright
from ddgs import DDGS

from models.search_result import SearchResult

_SYSTEM_CHANNELS = ("chrome", "msedge")
_CHROME_PROFILE_DIR = Path(__file__).resolve().parent.parent / ".scout_chrome_profile"

EXCLUDED_SITES = (
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
    "tiktok.com",
    "youtube.com",
    "reddit.com",
    "quora.com",
    "wikipedia.org",
)


class BrowserService:

    @staticmethod
    def get_profile_dir() -> Path:
        _CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        return _CHROME_PROFILE_DIR

    @staticmethod
    def launch(playwright, headless: bool = False):
        last_error = None
        for channel in _SYSTEM_CHANNELS:
            try:
                return playwright.chromium.launch(
                    headless=headless,
                    channel=channel,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
            except Exception as e:
                last_error = e
        try:
            return playwright.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
        except Exception as e:
            raise RuntimeError(
                "Could not launch Chrome, Edge, or Playwright Chromium. "
                "Install Chrome/Edge, or run: python -m playwright install chromium"
            ) from (last_error or e)

    @staticmethod
    def launch_persistent(playwright, headless: bool = False):
        profile_dir = BrowserService.get_profile_dir()
        last_error = None
        for channel in _SYSTEM_CHANNELS:
            try:
                return playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    channel=channel,
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
            except Exception as e:
                last_error = e

        try:
            return playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
        except Exception as e:
            print(f"[Warn] Persistent launch failed ({e}), falling back to standard launch.")
            browser = BrowserService.launch(playwright, headless=headless)
            return browser.new_context()

    @staticmethod
    def build_multi_queries(base_query: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        filters = filters or {}
        role = filters.get("role", "").strip() or base_query
        company = filters.get("company", "").strip()
        location = filters.get("location", "").strip()
        skills = filters.get("skills", "").strip()
        work_mode = filters.get("work_mode", "").strip()
        exp_years = filters.get("experience_years")

        # Clean role of punctuation like slashes or parentheses for search
        role_clean = role.replace("/", " ").replace("-", " ")
        loc_str = location if location else ""
        mode_str = work_mode if work_mode and work_mode.lower() not in ("any", "all") else ""

        exp_str = ""
        if exp_years is not None:
            if exp_years == 0:
                exp_str = "fresher entry level"
            elif exp_years == 1:
                exp_str = "1 year experience"
            else:
                exp_str = f"{int(exp_years)} years experience"

        queries = []

        if company:
            queries.append(f"{company} {role_clean} jobs {loc_str}".strip())
            queries.append(f"{company} {role_clean} careers site:greenhouse.io OR site:lever.co OR site:ashbyhq.com OR site:myworkdayjobs.com".strip())
            queries.append(f"{company} {role_clean} site:linkedin.com/jobs OR site:naukri.com OR site:foundit.in OR site:indeed.com {loc_str}".strip())
        else:
            # 1. Primary comprehensive job search
            queries.append(f"{role_clean} {exp_str} jobs {mode_str} {loc_str}".strip())

            # 2. Leading job platforms (LinkedIn, Naukri, Foundit)
            queries.append(f"{role_clean} {exp_str} site:linkedin.com/jobs OR site:naukri.com OR site:foundit.in {loc_str}".strip())

            # 3. Aggregators & Tech Portals (Indeed, Glassdoor, Wellfound, Internshala, Hirist)
            queries.append(f"{role_clean} {exp_str} site:indeed.com OR site:glassdoor.com OR site:wellfound.com OR site:internshala.com {loc_str}".strip())

            # 4. Direct ATS Boards (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable)
            queries.append(f"{role_clean} site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:myworkdayjobs.com OR site:apply.workable.com {loc_str}".strip())

            # 5. Skills focused
            if skills:
                skill_sample = " ".join(skills.split(",")[:2])
                queries.append(f"{role_clean} {skill_sample} hiring {loc_str}".strip())

            # 6. Direct company career openings
            queries.append(f"{role_clean} {exp_str} careers opening {mode_str} {loc_str}".strip())

        unique_queries = []
        for q in queries:
            q_clean = " ".join(q.split())
            if q_clean and q_clean not in unique_queries:
                unique_queries.append(q_clean)

        return unique_queries[:6]

    @staticmethod
    def search_multi_source(page, base_query: str, filters: Optional[Dict[str, Any]] = None, recency: Optional[str] = None) -> List[SearchResult]:
        queries = BrowserService.build_multi_queries(base_query, filters)
        print(f"[Multi-Engine Search] Executing {len(queries)} targeted queries across all sites...")

        all_results: List[SearchResult] = []
        seen_urls = set()

        # 1. High-speed multi-channel search via DDGS
        try:
            with DDGS() as ddgs:
                for idx, q in enumerate(queries, 1):
                    print(f" [Search Query {idx}/{len(queries)}] {q}")
                    try:
                        results = list(ddgs.text(q, max_results=35))
                        for r in results:
                            title = r.get("title", "").strip()
                            href = r.get("href", "").strip()
                            if not title or not href:
                                continue

                            # Skip social and non-job domains
                            netloc = urlparse(href).netloc.lower()
                            if any(bad in netloc for bad in EXCLUDED_SITES):
                                continue

                            norm_url = href.split("#")[0]
                            if norm_url not in seen_urls:
                                seen_urls.add(norm_url)
                                all_results.append(SearchResult(title=title, url=norm_url))
                    except Exception as e:
                        print(f"[Search Engine Notice] Query '{q}' notice: {e}")

                    if len(all_results) >= 80:
                        break
        except Exception as e:
            print(f"[DDGS Engine Warning] {e}")

        # 2. If fewer results were discovered, also query Google on page
        if len(all_results) < 20 and page is not None:
            print("[Search Engine] Running supplementary browser search...")
            for q in queries[:3]:
                res = BrowserService.search_google_on_page(page, q, recency=recency)
                for item in res:
                    norm_url = item.url.split("#")[0]
                    if norm_url not in seen_urls:
                        seen_urls.add(norm_url)
                        all_results.append(item)
                if len(all_results) >= 80:
                    break

        print(f"[Multi-Engine Search] Discovered {len(all_results)} total distinct candidate job links.")
        return all_results

    @staticmethod
    def search_google_on_page(page, query: str, recency: Optional[str] = None) -> List[SearchResult]:
        search_results: List[SearchResult] = []
        seen_urls = set()

        tbs_param = ""
        if recency:
            r = recency.lower().strip()
            if r in ("24h", "1d", "day", "past_24h", "today"):
                tbs_param = "&tbs=qdr:d"
            elif r in ("3d", "3days", "past_3d"):
                tbs_param = "&tbs=qdr:w"
            elif r in ("week", "7d", "1w", "past_week"):
                tbs_param = "&tbs=qdr:w"
            elif r in ("month", "30d", "1m", "past_month"):
                tbs_param = "&tbs=qdr:m"
            elif r in ("year", "1y", "past_year"):
                tbs_param = "&tbs=qdr:y"

        search_url = f"https://www.google.com/search?q={quote_plus(query)}{tbs_param}&num=30&hl=en"

        try:
            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            try:
                for _ in range(2):
                    page.evaluate("window.scrollBy(0, 1500);")
                    page.wait_for_timeout(400)
            except Exception:
                pass
        except Exception as e:
            print(f"[Google Search] Navigation warning: {e}")

        try:
            h3_elements = page.locator("h3").all()
        except Exception:
            h3_elements = []

        for h3 in h3_elements:
            if len(search_results) >= 30:
                break
            try:
                title = h3.inner_text().strip()
                if not title:
                    continue

                anc = h3.locator("xpath=ancestor::a[1]").first
                href = anc.get_attribute("href")
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue

                if href.startswith("/url?") or href.startswith("https://www.google.com/url?"):
                    qs = parse_qs(urlparse(href).query)
                    dest = qs.get("q", [""])[0] or qs.get("url", [""])[0]
                elif href.startswith("/goto?url="):
                    dest = f"https://www.google.com{href}"
                elif href.startswith("http://") or href.startswith("https://"):
                    dest = href
                else:
                    dest = f"https://www.google.com{href}"

                netloc = urlparse(dest).netloc.lower()
                if "google.com" in netloc and "/goto?" not in dest:
                    continue
                if any(bad in netloc for bad in EXCLUDED_SITES):
                    continue

                if dest in seen_urls:
                    continue

                seen_urls.add(dest)
                search_results.append(SearchResult(title=title, url=dest))
            except Exception:
                continue

        return search_results

    @staticmethod
    def search_google(query: str, recency: Optional[str] = None, page=None) -> List[SearchResult]:
        if page is not None:
            return BrowserService.search_google_on_page(page, query, recency=recency)

        with sync_playwright() as p:
            context = BrowserService.launch_persistent(p, headless=False)
            page = context.pages[0] if context.pages else context.new_page()
            results = BrowserService.search_google_on_page(page, query, recency=recency)
            context.close()
            return results
