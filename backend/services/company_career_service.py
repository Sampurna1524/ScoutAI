import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from models.search_result import SearchResult
from models.scout_session import ScoutSession
from services.link_extractor_service import LinkExtractorService

# Known ATS platforms and enterprise career portal domains
ATS_DOMAINS = (
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "smartrecruiters.com",
    "workable.com",
    "bamboohr.com",
    "jobvite.com",
    "icims.com",
    "taleo.net",
    "recruitee.com",
    "breezy.hr",
    "rippling-ats.com",
    "freshteam.com",
    "instahyre.com",
    "cutshort.io",
    "eightfold.ai",
    "successfactors.com",
    "phenompro.com",
)

CAREER_KEYWORDS = (
    "career",
    "careers",
    "jobs",
    "job",
    "browse jobs",
    "search jobs",
    "career areas",
    "job categories",
    "join us",
    "join our team",
    "work with us",
    "we're hiring",
    "open roles",
    "open positions",
    "openings",
    "opportunities",
    "employment",
    "work at",
)

# Mapping of role keywords to typical enterprise "Career Areas" dropdown items
CAREER_AREA_MAPPINGS = {
    "technology": ["technology", "it", "information technology", "engineering", "software", "digital", "data", "ai", "artificial intelligence", "tech"],
    "engineering": ["engineering", "manufacturing & quality / engineering", "technology", "r&d", "research and development", "software"],
    "ai": ["technology", "artificial intelligence", "data", "research and development", "engineering", "digital", "innovation"],
    "ml": ["technology", "artificial intelligence", "data", "research and development", "engineering"],
    "data": ["technology", "data", "analytics", "business intelligence", "digital", "information technology"],
    "research": ["research and development", "r&d", "science", "medical", "discovery", "technology"],
    "finance": ["finance", "accounting", "treasury", "audit", "business"],
    "business": ["business", "strategy", "operations", "commercial"],
    "medical": ["medical", "clinical", "health", "regulatory", "pharmacovigilance"],
    "legal": ["legal", "compliance", "regulatory", "ethics"],
    "hr": ["human resources", "people", "talent", "recruiting"],
    "marketing": ["marketing", "sales", "sales/marketing", "commercial", "brand"],
    "sales": ["sales", "sales/marketing", "commercial", "business development"],
    "manufacturing": ["manufacturing & quality", "manufacturing", "quality", "operations", "supply chain"],
}


class CompanyCareerService:

    @staticmethod
    def normalize_company_url(url: str) -> str:
        """Ensures the company URL has a valid scheme and is cleanly formatted."""
        if not url:
            return ""
        cleaned = url.strip()
        if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
            cleaned = "https://" + cleaned
        return cleaned.rstrip("/")

    @staticmethod
    def extract_company_info(url: str) -> Dict[str, str]:
        """
        Extracts company name, domain, and apex domain from a URL.
        e.g., https://boards.greenhouse.io/anthropic -> name: Anthropic, domain: boards.greenhouse.io
              https://openai.com -> name: OpenAI, domain: openai.com
              https://www.lilly.com/ -> name: Lilly, domain: lilly.com
              https://stripe.com/careers -> name: Stripe, domain: stripe.com
        """
        norm_url = CompanyCareerService.normalize_company_url(url)
        parsed = urlparse(norm_url)
        netloc = parsed.netloc.lower()
        path = parsed.path.strip("/").split("/")

        # Check for ATS subpaths where company name is in path
        if any(ats in netloc for ats in ("greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com", "apply.workable.com", "rippling-ats.com")):
            if path and path[0]:
                company_name = path[0].replace("-", " ").replace("_", " ").title()
                return {
                    "company_name": company_name,
                    "domain": netloc,
                    "apex_domain": LinkExtractorService.get_apex_domain(netloc),
                    "url": norm_url,
                }

        # Check for subdomain like company.bamboohr.com or company.myworkdayjobs.com
        if any(ats in netloc for ats in ("myworkdayjobs.com", "bamboohr.com", "jobvite.com", "recruitee.com", "eightfold.ai")):
            sub = netloc.split(".")[0]
            if sub and sub != "www":
                return {
                    "company_name": sub.replace("-", " ").replace("_", " ").title(),
                    "domain": netloc,
                    "apex_domain": LinkExtractorService.get_apex_domain(netloc),
                    "url": norm_url,
                }

        # Extract name from domain: e.g. openai.com -> OpenAI, lilly.com -> Lilly
        apex = LinkExtractorService.get_apex_domain(netloc)
        base_name = apex.split(".")[0] if apex else netloc
        # Clean common prefixes like "careers", "jobs", "about"
        if base_name in ("careers", "jobs", "work", "join") and len(netloc.split(".")) > 2:
            base_name = netloc.split(".")[-2]

        special_casing = {
            "lilly": "Eli Lilly",
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google",
            "microsoft": "Microsoft",
            "meta": "Meta",
            "apple": "Apple",
            "amazon": "Amazon",
            "netflix": "Netflix",
            "uber": "Uber",
            "airbnb": "Airbnb",
            "stripe": "Stripe",
            "nvidia": "NVIDIA",
            "salesforce": "Salesforce",
            "linkedin": "LinkedIn",
            "github": "GitHub",
            "datadog": "Datadog",
            "snowflake": "Snowflake",
            "palantir": "Palantir",
            "scale": "Scale AI",
            "cohere": "Cohere",
            "mistral": "Mistral AI",
            "huggingface": "Hugging Face",
            "deepmind": "Google DeepMind",
        }

        company_name = special_casing.get(base_name.lower(), base_name.replace("-", " ").replace("_", " ").title())
        return {
            "company_name": company_name,
            "domain": netloc,
            "apex_domain": apex,
            "url": norm_url,
        }

    @staticmethod
    def is_likely_careers_url(url: str) -> bool:
        """Checks if a URL already points directly to a careers or jobs portal."""
        lower = url.lower()
        if any(ats in lower for ats in ATS_DOMAINS):
            return True
        path = urlparse(lower).path
        for kw in ("careers", "career", "jobs", "job", "openings", "positions", "vacancies", "join-us", "work-with-us", "career-areas"):
            if f"/{kw}" in path or f"-{kw}" in path or f"{kw}/" in path or path.startswith(f"/{kw}"):
                return True
        netloc = urlparse(lower).netloc
        if netloc.startswith("careers.") or netloc.startswith("jobs."):
            return True
        return False

    @staticmethod
    def find_careers_url(page, company_url: str) -> str:
        """
        Locates the primary careers or jobs page on the company website.
        If the company_url is already a careers page, returns it.
        Otherwise, probes careers subdomains and inspects homepage navigation.
        """
        norm_url = CompanyCareerService.normalize_company_url(company_url)
        if CompanyCareerService.is_likely_careers_url(norm_url):
            return norm_url

        info = CompanyCareerService.extract_company_info(norm_url)
        apex = info.get("apex_domain", "")

        # 1. First probe standard dedicated career subdomains (e.g. careers.lilly.com, jobs.lilly.com)
        if apex:
            candidate_subdomains = [
                f"https://careers.{apex}",
                f"https://jobs.{apex}",
                f"https://{apex}/careers",
                f"https://{apex}/jobs",
                f"https://www.{apex}/careers",
            ]
            for c_sub in candidate_subdomains:
                try:
                    res = page.goto(c_sub, wait_until="domcontentloaded", timeout=6000)
                    if res and res.status in (200, 301, 302, 304, 307, 308):
                        final_u = page.url
                        print(f"[Company Careers] Discovered active careers portal: {final_u}")
                        return final_u
                except Exception:
                    continue

        # 2. Inspect homepage anchors for career links and Career Areas
        print(f"[Company Careers] Inspecting homepage navigation for careers link: {norm_url}")
        try:
            page.goto(norm_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(800)

            anchors = page.locator("a[href]").all()
            candidate_links = []

            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                        continue
                    text = (a.inner_text() or "").strip().lower()
                    href_lower = href.lower()
                    full_url = urljoin(norm_url, href).split("#")[0]

                    # Check for direct ATS platform links
                    if any(ats in full_url.lower() for ats in ATS_DOMAINS):
                        print(f"[Company Careers] Discovered direct ATS link: {full_url}")
                        return full_url

                    # Check for career keywords in text or href
                    if any(kw in text for kw in CAREER_KEYWORDS) or any(f"/{kw}" in href_lower for kw in ("career", "careers", "jobs", "job", "career-areas", "openings", "positions")):
                        candidate_links.append(full_url)
                except Exception:
                    continue

            if candidate_links:
                for cl in candidate_links:
                    if "careers" in cl.lower() or "jobs" in cl.lower():
                        print(f"[Company Careers] Found primary careers page from navigation: {cl}")
                        return cl
                return candidate_links[0]

        except Exception as e:
            print(f"[Company Careers] Homepage inspection notice: {e}")

        # 3. Fallback
        if apex:
            return f"https://careers.{apex}"
        return f"{norm_url}/careers"

    @staticmethod
    def search_and_extract_company_jobs(
        page,
        careers_url: str,
        target_role: str,
        session: Optional[ScoutSession] = None,
        max_results: int = 40,
    ) -> List[SearchResult]:
        """
        Navigates to the company's careers portal.
        Handles:
        1. "Career Areas" / "Job Categories" dropdowns and navigation items (e.g. Technology, Engineering, R&D).
        2. "Browse Jobs" / "Search Jobs" links.
        3. In-page search bar inputs (types role, presses Enter).
        4. Extracts all matching job listing URLs.
        """
        discovered: List[SearchResult] = []
        seen_urls = set()

        print(f"[Company Careers] Navigating to careers portal: {careers_url}")
        if session:
            session.append_event(
                "company_portal_nav",
                f"Visiting company careers portal: {careers_url}",
                {"url": careers_url, "target_role": target_role},
            )

        try:
            page.goto(careers_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)

            # 1. Check for "Career Areas", "Job Categories", "Departments" dropdowns or menus
            role_lower = target_role.lower().strip()
            target_areas = set()
            for key, areas in CAREER_AREA_MAPPINGS.items():
                if key in role_lower:
                    target_areas.update(areas)
            if not target_areas:
                target_areas = {"technology", "engineering", "data", "r&d", "research and development", "software"}

            # Find and expand "Career Areas" / "Browse Jobs" navigation menus
            try:
                career_area_triggers = page.locator("button, a, span, div").filter(
                    has_text=re.compile(r"^(Career Areas|Job Categories|Browse Jobs|Explore Careers|Departments|Teams)", re.I)
                ).all()

                for trigger in career_area_triggers[:3]:
                    try:
                        if trigger.is_visible():
                            trigger.hover()
                            page.wait_for_timeout(300)
                            trigger.click(timeout=1000)
                            page.wait_for_timeout(500)
                    except Exception:
                        pass
            except Exception:
                pass

            # Scan anchors for matching Career Area links (e.g. Technology, Engineering, Research and Development)
            career_area_links = []
            try:
                anchors = page.locator("a[href]").all()
                for a in anchors:
                    try:
                        t = (a.inner_text() or "").strip().lower()
                        h = (a.get_attribute("href") or "").strip()
                        if not h or h.startswith("#"):
                            continue
                        # If link text matches target career areas
                        if any(area in t for area in target_areas) or "browse-jobs" in h.lower() or "search-results" in h.lower():
                            full = urljoin(page.url, h)
                            career_area_links.append(full)
                    except Exception:
                        continue
            except Exception:
                pass

            # 2. Try interactive search in search inputs
            if target_role and target_role.strip():
                role_query = target_role.strip()
                search_selectors = [
                    "input[type='search']",
                    "input[placeholder*='search' i]",
                    "input[placeholder*='job' i]",
                    "input[placeholder*='role' i]",
                    "input[placeholder*='title' i]",
                    "input[placeholder*='keyword' i]",
                    "input[placeholder*='position' i]",
                    "input[name*='keyword' i]",
                    "input[name*='search' i]",
                    "input[name*='query' i]",
                    "input[name*='q' i]",
                    "input[id*='search' i]",
                    "input[id*='job' i]",
                ]

                for sel in search_selectors:
                    try:
                        input_el = page.locator(sel).first
                        if input_el.is_visible():
                            print(f"[Company Careers] Found in-page search input ({sel}), typing '{role_query}'...")
                            if session:
                                session.append_event(
                                    "company_portal_search",
                                    f"Filtering careers page for '{role_query}'",
                                    {"selector": sel, "role": role_query},
                                )
                            input_el.click()
                            input_el.fill("")
                            input_el.type(role_query, delay=35)
                            input_el.press("Enter")
                            page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue

            # Scroll to trigger lazy loading
            try:
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000);")
                    page.wait_for_timeout(400)
            except Exception:
                pass

            # Extract job detail links from current page
            base_url = page.url or careers_url
            job_links = LinkExtractorService.extract_job_links(page, base_url, limit=max_results)

            role_tokens = [t.lower() for t in re.split(r"[\s,\-/]+", target_role) if len(t) > 2] if target_role else []

            all_anchors = page.locator("a[href]").all()
            for anchor in all_anchors:
                if len(discovered) >= max_results:
                    break
                try:
                    href = anchor.get_attribute("href")
                    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                        continue
                    url = urljoin(base_url, href).split("#")[0]
                    if url in seen_urls:
                        continue

                    title = (anchor.inner_text() or "").strip()
                    title = " ".join(title.split())

                    is_detail = LinkExtractorService.is_detail_url(url)
                    is_ats = any(ats in url.lower() for ats in ATS_DOMAINS)
                    matches_role = any(t in title.lower() or t in url.lower() for t in role_tokens) if role_tokens else True

                    if (is_detail or is_ats or matches_role) and len(title) >= 3:
                        if title.lower() in ("home", "about", "contact", "careers", "jobs", "search", "apply", "view all", "learn more", "read more", "who we are", "privacy", "terms"):
                            continue

                        seen_urls.add(url)
                        discovered.append(SearchResult(title=title or f"Position at {careers_url}", url=url))
                except Exception:
                    continue

            for jl in job_links:
                if jl not in seen_urls and len(discovered) < max_results:
                    seen_urls.add(jl)
                    discovered.append(SearchResult(title=f"Position at {careers_url}", url=jl))

            # 3. If few jobs found and Career Area links exist, visit top 2 matching Career Area pages
            if len(discovered) < 5 and career_area_links:
                print(f"[Company Careers] Drilling into matching Career Area pages: {career_area_links[:2]}")
                for ca_url in career_area_links[:2]:
                    if len(discovered) >= max_results:
                        break
                    try:
                        page.goto(ca_url, wait_until="domcontentloaded", timeout=12000)
                        page.wait_for_timeout(1000)
                        sub_links = LinkExtractorService.extract_job_links(page, ca_url, limit=15)
                        for sl in sub_links:
                            if sl not in seen_urls and len(discovered) < max_results:
                                seen_urls.add(sl)
                                discovered.append(SearchResult(title=f"Opportunity in {target_role}", url=sl))
                    except Exception:
                        continue

            print(f"[Company Careers] Discovered {len(discovered)} direct job listings on portal.")
            if session:
                session.append_event(
                    "company_portal_results",
                    f"Discovered {len(discovered)} job listings directly on company careers portal",
                    {"count": len(discovered), "careers_url": careers_url},
                )

        except Exception as e:
            print(f"[Company Careers] Error crawling careers portal: {e}")
            if session:
                session.append_event(
                    "company_portal_error",
                    f"Notice while reading careers portal: {e}",
                    {"url": careers_url},
                )

        return discovered
