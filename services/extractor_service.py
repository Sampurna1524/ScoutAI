import re
from typing import Optional, List
from urllib.parse import urlparse

from models.job import Job
from models.scout_session import ScoutSession
from services.llm.llm_service import LLMService


COMMON_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django", "Flask",
    "PyTorch", "TensorFlow", "LangChain", "OpenAI", "LlamaIndex", "HuggingFace", "Scikit-Learn",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "CI/CD", "Git", "Linux", "REST", "GraphQL", "Java", "C++", "Go",
    "Rust", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Engineering"
]


class ExtractorService:

    @staticmethod
    def extract_job(
        page_text: str,
        url: str,
        session: Optional[ScoutSession] = None,
        fallback_title: str = "",
    ) -> Job:
        try:
            job = LLMService.extract_job(page_text, session=session)
        except Exception as e:
            print(f"[ExtractorService] LLM extraction fallback used ({e})")
            job = ExtractorService._heuristic_extract(page_text, url, fallback_title)

        if not (job.title or "").strip() and fallback_title:
            job.title = fallback_title

        # Prefer job-body text over the full page chrome when possible.
        cleaned = page_text.strip()
        for marker in ("Skip to main content", "Start of main content"):
            idx = cleaned.find(marker)
            if idx != -1:
                cleaned = cleaned[idx + len(marker):].strip()
                break

        if not job.description:
            job.description = cleaned[:2000]
        job.apply_url = url
        job.source = urlparse(url).netloc
        job.status = "success"
        job.error = ""

        return job

    @staticmethod
    def _heuristic_extract(page_text: str, url: str, fallback_title: str) -> Job:
        # Clean title
        title = fallback_title.strip()
        for suffix in (" - LinkedIn", " | LinkedIn", " - Indeed", " - Glassdoor", " | Greenhouse", " - Lever", " | Workday", " jobs in India", " jobs"):
            if title.lower().endswith(suffix.lower()):
                title = title[:-len(suffix)].strip()

        # Deduce company
        company = ""
        host = urlparse(url).netloc.lower()
        if "greenhouse.io" in host:
            parts = urlparse(url).path.strip("/").split("/")
            if parts: company = parts[0].capitalize()
        elif "lever.co" in host:
            parts = urlparse(url).path.strip("/").split("/")
            if parts: company = parts[0].capitalize()
        elif "ashbyhq.com" in host:
            parts = urlparse(url).path.strip("/").split("/")
            if parts: company = parts[0].capitalize()
        elif " - " in title:
            bits = title.split(" - ")
            if len(bits) >= 2:
                company = bits[-1].strip()
                title = " - ".join(bits[:-1]).strip()

        # Experience extraction
        exp_years = None
        exp_match = re.search(r"(\d+)\+?\s*(?:-|to)?\s*(\d+)?\s*(?:years?|yrs?|yr)\s*(?:of\s+)?(?:experience|exp)?", page_text, re.I)
        if exp_match:
            try:
                exp_years = float(exp_match.group(1))
            except Exception:
                pass

        # Work mode
        work_mode = None
        if re.search(r"\b(remote|work from home|wfh)\b", page_text, re.I):
            work_mode = "Remote"
        elif re.search(r"\bhybrid\b", page_text, re.I):
            work_mode = "Hybrid"
        elif re.search(r"\bon-?site\b", page_text, re.I):
            work_mode = "On-site"

        # Skills
        found_skills = []
        for s in COMMON_SKILLS:
            if re.search(rf"\b{re.escape(s)}\b", page_text, re.I):
                found_skills.append(s)

        return Job(
            title=title or "Job Opportunity",
            company=company,
            experience_years=exp_years,
            work_mode=work_mode,
            skills=found_skills[:8],
            description=page_text.strip()[:1500]
        )
