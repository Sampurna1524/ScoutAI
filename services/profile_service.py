import io
import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from models.job import Job
from services.llm.llm_service import LLMService


class CandidateProfile(BaseModel):
    name: str = ""
    headline: str = ""
    experience_years: Optional[float] = 0.0
    experience_months: Optional[int] = 0
    skills: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    location_preference: str = ""
    summary: str = ""


RESUME_PARSING_PROMPT = """
You are an expert technical recruiter and resume parsing AI.

Extract key professional details from the following resume / LinkedIn profile text and return ONLY a valid JSON object.

The JSON MUST contain exactly these fields:
{{
    "name": "",
    "headline": "",
    "experience_years": null,
    "experience_months": null,
    "skills": [],
    "target_roles": [],
    "location_preference": "",
    "summary": ""
}}

Rules:
- Return ONLY valid JSON without markdown wrapping or explanations.
- "name": Candidate's full name.
- "headline": Candidate's current or primary role title.
- "experience_years": Total years of work experience as a number (e.g., 3.5, 2, 0).
- "experience_months": Additional months if specified (0 to 11).
- "skills": Array of key technical skills, languages, tools, frameworks (e.g., ["Python", "PyTorch", "FastAPI", "Docker"]).
- "target_roles": Array of 1 to 3 job titles best suited for this candidate (e.g., ["Python AI Engineer", "Backend Developer"]).
- "location_preference": Current city or preferred location if stated.
- "summary": 1-2 sentence professional summary highlighting their strongest competencies.

Resume Content:
{resume_text}
"""


class ProfileService:

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            return "\n".join(text_parts).strip()
        except Exception as e:
            print(f"[ProfileService] PDF extraction failed: {e}")
            return ""

    @staticmethod
    def parse_profile_text(text: str) -> CandidateProfile:
        cleaned_text = text.strip()
        if not cleaned_text:
            return CandidateProfile()

        prompt = RESUME_PARSING_PROMPT.format(resume_text=cleaned_text[:10000])

        from services.llm.registry import get_provider_classes

        for provider_cls in get_provider_classes():
            try:
                provider = provider_cls()
                if getattr(provider, "name", "") == "Gemini":
                    from google.genai import types
                    response = provider.client.models.generate_content(
                        model=provider.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=CandidateProfile
                        )
                    )
                    if response.parsed:
                        return response.parsed
                    elif response.text:
                        data = json.loads(response.text)
                        return CandidateProfile(**data)
                elif getattr(provider, "name", "") == "Groq":
                    response = provider.client.chat.completions.create(
                        model=provider.model,
                        temperature=0.1,
                        response_format={"type": "json_object"},
                        messages=[{"role": "user", "content": prompt}]
                    )
                    content = response.choices[0].message.content
                    if content:
                        data = json.loads(content)
                        return CandidateProfile(**data)
            except Exception as e:
                print(f"[ProfileService] Provider {getattr(provider_cls, '__name__', '')} failed: {e}")
                continue

        return ProfileService._fallback_heuristic_parse(cleaned_text)

    @staticmethod
    def _fallback_heuristic_parse(text: str) -> CandidateProfile:
        profile = CandidateProfile()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            profile.name = lines[0][:40]
            if len(lines) > 1:
                profile.headline = lines[1][:60]

        # Extract years of experience
        exp_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs)", text, re.IGNORECASE)
        if exp_match:
            try:
                profile.experience_years = float(exp_match.group(1))
            except ValueError:
                pass

        # Common tech skills
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django",
            "Flask", "PyTorch", "TensorFlow", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "SQL", "PostgreSQL", "MongoDB", "Redis", "Git", "LangChain", "LLM", "C++", "Java",
            "Go", "Rust", "HTML", "CSS", "Tailwind", "Next.js", "GraphQL", "REST API"
        ]
        found_skills = []
        for kw in tech_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
                found_skills.append(kw)
        profile.skills = found_skills[:12]

        if profile.headline:
            profile.target_roles = [profile.headline]
        elif found_skills:
            profile.target_roles = [f"{found_skills[0]} Developer"]

        profile.summary = f"Candidate with {profile.experience_years or 0} yrs experience in {', '.join(found_skills[:4])}."
        return profile

    @staticmethod
    def evaluate_match(profile: CandidateProfile, job: Job) -> Job:
        if not profile or not (profile.skills or profile.target_roles or profile.experience_years):
            return job

        candidate_skills = {s.lower().strip() for s in profile.skills if s}
        job_skills = [s.strip() for s in job.skills if s]

        matched = []
        missing = []

        if job_skills:
            for js in job_skills:
                js_lower = js.lower()
                is_matched = any(
                    cs == js_lower or cs in js_lower or js_lower in cs
                    for cs in candidate_skills
                )
                if is_matched:
                    matched.append(js)
                else:
                    missing.append(js)
        else:
            # Check candidate skills against job description
            desc_lower = (job.description or "").lower()
            for cs in profile.skills:
                if re.search(rf"\b{re.escape(cs.lower())}\b", desc_lower):
                    matched.append(cs)

        # Calculate skill score (weight: 60%)
        if job_skills:
            skill_ratio = len(matched) / len(job_skills)
        else:
            skill_ratio = min(len(matched) / 3, 1.0) if matched else 0.5
        skill_score = skill_ratio * 60

        # Calculate experience score (weight: 25%)
        exp_score = 25
        if job.experience_years is not None and profile.experience_years is not None:
            if profile.experience_years >= job.experience_years:
                exp_score = 25
            elif profile.experience_years >= (job.experience_years * 0.7):
                exp_score = 18
            else:
                exp_score = 10

        # Calculate role relevance score (weight: 15%)
        role_score = 15
        job_title_lower = (job.title or "").lower()
        if profile.target_roles:
            role_match = any(
                tr.lower() in job_title_lower or job_title_lower in tr.lower()
                for tr in profile.target_roles
            )
            if not role_match:
                role_score = 8

        total_match = int(min(max(skill_score + exp_score + role_score, 20), 98))

        # Build human-readable match summary
        summary_bits = []
        if total_match >= 80:
            summary_bits.append(f"Strong fit ({total_match}% match).")
        elif total_match >= 60:
            summary_bits.append(f"Good potential ({total_match}% match).")
        else:
            summary_bits.append(f"Moderate fit ({total_match}% match).")

        if matched:
            summary_bits.append(f"Matches required skills: {', '.join(matched[:4])}.")
        if missing:
            summary_bits.append(f"Skills to acquire: {', '.join(missing[:3])}.")

        job.match_score = total_match
        job.match_summary = " ".join(summary_bits)
        job.matched_skills = matched
        job.missing_skills = missing

        return job
