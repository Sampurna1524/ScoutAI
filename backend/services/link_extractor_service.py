import re
from typing import List
from urllib.parse import urljoin, urlparse


class LinkExtractorService:

    # Patterns that indicate a single job posting detail page.
    DETAIL_PATTERNS = [
        # ATS Platforms
        re.compile(r"boards\.greenhouse\.io/[^/]+/jobs/\d+", re.I),
        re.compile(r"boards\.greenhouse\.io/[^/]+/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"job-boards\.greenhouse\.io/[^/]+/jobs/\d+", re.I),
        re.compile(r"jobs\.lever\.co/[^/]+/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"jobs\.ashbyhq\.com/[^/]+/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"myworkdayjobs\.com/.+/job/", re.I),
        re.compile(r"myworkdaysite\.com/.+/job/", re.I),
        re.compile(r"jobs\.smartrecruiters\.com/[^/]+/[^/]+", re.I),
        re.compile(r"apply\.workable\.com/[^/]+/j/[^/]+", re.I),
        re.compile(r"bamboohr\.com/careers/\d+", re.I),
        re.compile(r"bamboohr\.com/jobs/view\.php\?id=\d+", re.I),
        re.compile(r"jobs\.jobvite\.com/[^/]+/job/[^/]+", re.I),
        re.compile(r"jobs\.icims\.com/jobs/\d+", re.I),
        re.compile(r"taleo\.net/careersection/.+/jobdetail\.ftl", re.I),
        re.compile(r"recruitee\.com/o/[^/]+", re.I),
        re.compile(r"breezy\.hr/p/[^/]+", re.I),
        re.compile(r"rippling-ats\.com/[^/]+/jobs/[^/]+", re.I),
        re.compile(r"freshteam\.com/jobs/[^/]+", re.I),
        re.compile(r"instahyre\.com/job-\d+", re.I),
        re.compile(r"cutshort\.io/job/[^/]+", re.I),
        
        # Major Job Boards Individual Postings
        re.compile(r"linkedin\.com/jobs/view/\d+", re.I),
        re.compile(r"/jobs/view/\d+", re.I),
        re.compile(r"/jobs/view/", re.I),
        re.compile(r"/viewjob\?", re.I),
        re.compile(r"/rc/clk\?", re.I),
        re.compile(r"[?&]jk=[a-f0-9]+", re.I),
        re.compile(r"/job-listings-", re.I),
        re.compile(r"/job-listing/", re.I),
        re.compile(r"wellfound\.com/jobs/\d+", re.I),
        re.compile(r"wellfound\.com/company/[^/]+/jobs/\d+", re.I),
        re.compile(r"ziprecruiter\.com/jobs/[^/]+/[^/]+", re.I),
        re.compile(r"glassdoor\.[^/]+/partner/jobListing\.htm", re.I),
        re.compile(r"glassdoor\.[^/]+/Job/[^/]+-JV_", re.I),
        re.compile(r"foundit\.in/job/[^/]+", re.I),
        re.compile(r"naukri\.com/job-listings-[^/]+", re.I),

        # Company Direct Career Paths & Enterprise ATS (Phenom, Workday, Eightfold, Taleo)
        re.compile(r"/careers?/[^/]+/job/[^/]+", re.I),
        re.compile(r"/careers?/[^/]+/\d+", re.I),
        re.compile(r"/careers?/[^/]+/position/[^/]+", re.I),
        re.compile(r"/careers?/[^/]+/opening/[^/]+", re.I),
        re.compile(r"/careers?/[^/]+/open-roles/[^/]+", re.I),
        re.compile(r"/careers?/[0-9a-zA-Z_-]+-\d+", re.I),
        re.compile(r"/careers?/[0-9a-zA-Z_-]+/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/career-areas?/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"-opportunities-[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/career\?gh_jid=\d+", re.I),
        re.compile(r"/jobs/\d{4,}", re.I),
        re.compile(r"/job/R-\d+", re.I),
        re.compile(r"/job/REQ-\d+", re.I),
        re.compile(r"/job/JR\d+", re.I),
        re.compile(r"/job/\d+", re.I),
        re.compile(r"/job/[0-9a-zA-Z_-]+/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/job/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/jobs/[0-9a-zA-Z_-]+-\d+", re.I),
        re.compile(r"/position/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/positions/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/opening/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/openings/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/role/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"/roles/[0-9a-zA-Z_-]+", re.I),
        re.compile(r"eightfold\.ai/careers/job/\d+", re.I),
        re.compile(r"[?&](?:job_id|gh_jid|jid|req_id|requisition_id)=\d+", re.I),
        re.compile(r"/apply/[0-9a-zA-Z_-]+", re.I),
    ]

    EXCLUDED_DOMAINS = (
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
        "linkedin.com",
        "indeed.com",
        "wellfound.com",
        "ziprecruiter.com",
        "glassdoor.com",
        "naukri.com",
        "foundit.in",
    )

    LISTING_HINTS = (
        "/jobs?",
        "/jobs/",
        "/search?",
        "/find-jobs",
        "jobs.html",
        "/vacancies",
        "/careers/search",
        "/jobsearch",
        "q-",
        "/l-",
        "linkedin.com/jobs/search",
        "indeed.com/jobs",
        "indeed.com/q-",
        "-jobs",
    )

    @staticmethod
    def get_apex_domain(host: str) -> str:
        parts = host.lower().lstrip("www.").split(".")
        if len(parts) >= 2:
            if parts[-2] in ("co", "com", "org", "gov", "net", "edu") and len(parts) >= 3:
                return ".".join(parts[-3:])
            return ".".join(parts[-2:])
        return host.lower()

    @staticmethod
    def is_detail_url(url: str) -> bool:
        if not url:
            return False
        # If url explicitly ends with -jobs or is a search listing, it is not a detail page
        if re.search(r"[-/]jobs(?:-[a-z0-9]+)*-jobs/?(?:\?.*)?$", url, re.I):
            return False
        return any(pattern.search(url) for pattern in LinkExtractorService.DETAIL_PATTERNS)

    @staticmethod
    def is_listing_url(url: str) -> bool:
        if not url:
            return False
        if LinkExtractorService.is_detail_url(url):
            return False
        lower = url.lower()
        path = urlparse(lower).path
        query = urlparse(lower).query
        joined = f"{path}?{query}"
        return any(hint in joined or hint in lower for hint in LinkExtractorService.LISTING_HINTS)

    @staticmethod
    def extract_job_links(page, base_url: str, limit: int = 10) -> List[str]:
        job_links: List[str] = []
        seen = set()
        base_host = urlparse(base_url).netloc.lower()
        base_apex = LinkExtractorService.get_apex_domain(base_host)

        try:
            anchors = page.locator("a[href]").all()
        except Exception:
            anchors = []

        for anchor in anchors:
            if len(job_links) >= limit:
                break
            try:
                href = anchor.get_attribute("href")
                if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                    continue

                url = urljoin(base_url, href).split("#")[0]
                if url in seen:
                    continue

                host = urlparse(url).netloc.lower()
                if any(ex in host for ex in LinkExtractorService.EXCLUDED_DOMAINS):
                    continue

                apex = LinkExtractorService.get_apex_domain(host)

                # Accept same apex domain or recognized ATS/job board domains
                is_same_domain = (apex == base_apex)
                is_recognized_ats = any(host.endswith(ats) or ats in host for ats in LinkExtractorService.ATS_DOMAINS)

                if not is_same_domain and not is_recognized_ats:
                    continue

                if not LinkExtractorService.is_detail_url(url):
                    continue

                seen.add(url)
                job_links.append(url)
            except Exception:
                continue

        return job_links

    @staticmethod
    def should_drill_into_jobs(url: str, job_links: List[str]) -> bool:
        if len(job_links) >= 1:
            if LinkExtractorService.is_listing_url(url):
                return True
            if not LinkExtractorService.is_detail_url(url):
                return True
            # Even on a detail page, if multiple distinct job links are found, drill into them
            if len(job_links) >= 2:
                return True
        return False

