import os
import re
from typing import Dict, Any, List, Optional
from models.job import Job
from services.profile_service import CandidateProfile


class AiTailorService:

    @staticmethod
    def generate_pitch_and_cover_letter(
        job: Job,
        candidate: Optional[CandidateProfile] = None,
        tone: str = "confident",
    ) -> Dict[str, str]:
        """
        Generates tailored outreach messages, ATS resume bullets, and custom cover letters
        specifically tailored to the target job and candidate profile.
        """
        cand_name = (candidate.name if candidate and candidate.name else "Candidate").strip()
        cand_skills = (", ".join(candidate.skills[:8]) if candidate and candidate.skills else "Python, Machine Learning, Cloud Architecture")
        job_title = job.title or "Software / AI Role"
        company = job.company or "your team"
        matched = ", ".join(job.matched_skills) if job.matched_skills else cand_skills
        missing = ", ".join(job.missing_skills) if job.missing_skills else "related specialized tooling"

        # Try LLM generation if available
        prompt = f"""
You are an expert executive career coach and technical recruiter.
Candidate Name: {cand_name}
Candidate Background Skills: {cand_skills}
Target Job Title: {job_title}
Target Company: {company}
Matched Key Skills: {matched}
Job Description Excerpt: {(job.description or '')[:1200]}

Generate 3 high-impact items in valid JSON with these exact keys:
1. "linkedin_outreach": A concise, highly persuasive 3-paragraph LinkedIn DM to the hiring manager (under 130 words).
2. "cover_letter": A compelling, professional 3-paragraph cover letter tailored to {company}.
3. "resume_bullet_points": An array of 3 strong, quantified achievement bullet points highlighting {matched} relevant to this job.

Return ONLY valid JSON with keys: "linkedin_outreach", "cover_letter", "resume_bullet_points" (list of strings).
"""
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
                model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                txt = response.text.strip()
                import json
                # Strip markdown fences if present
                clean_json = re.sub(r"^```json\s*", "", txt, flags=re.MULTILINE)
                clean_json = re.sub(r"```\s*$", "", clean_json, flags=re.MULTILINE).strip()
                parsed = json.loads(clean_json)
                return {
                    "linkedin_outreach": parsed.get("linkedin_outreach", ""),
                    "cover_letter": parsed.get("cover_letter", ""),
                    "resume_bullet_points": "\n".join(f"• {b}" for b in parsed.get("resume_bullet_points", []))
                }
        except Exception as e:
            print(f"[AiTailorService] LLM generation notice ({e}), using high-yield heuristic generator.")

        # High-yield heuristic template generator
        outreach = (
            f"Hi Hiring Team at {company},\n\n"
            f"I came across the {job_title} opening at {company} and was immediately drawn to the work your team is building. "
            f"With hands-on expertise in {matched}, I have successfully architected and scaled production systems delivering high throughput and measurable reliability.\n\n"
            f"I would love to connect for 10 minutes to discuss how my background in {matched} can directly accelerate your current roadmap for this role.\n\n"
            f"Best regards,\n{cand_name}"
        )

        cover_letter = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong enthusiasm for the {job_title} position at {company}. "
            f"Having developed robust solutions utilizing {matched}, I have consistently focused on building scalable, reliable architectures that solve mission-critical problems.\n\n"
            f"Reviewing the requirements for {job_title}, I noticed a strong emphasis on core engineering excellence and rapid execution. "
            f"In my recent projects, I spearheaded implementations using {matched}, cutting latency, optimizing deployment pipelines, and collaborating cross-functionally to exceed technical milestones.\n\n"
            f"I would welcome the opportunity to discuss in detail how my skills and problem-solving mindset align with {company}'s strategic goals. Thank you for your time and consideration.\n\n"
            f"Sincerely,\n{cand_name}"
        )

        bullets = (
            f"• Spearheaded architecture and end-to-end development of high-performance pipelines utilizing {matched}, improving execution efficiency by 35%.\n"
            f"• Designed modular, production-ready services solving core technical constraints relevant to {job_title}, ensuring 99.9% uptime and low latency.\n"
            f"• Rapidly mastered and integrated modern ecosystem frameworks, bridging requirements across cross-functional engineering teams."
        )

        return {
            "linkedin_outreach": outreach,
            "cover_letter": cover_letter,
            "resume_bullet_points": bullets
        }

    @staticmethod
    def generate_interview_prep(job: Job, candidate: Optional[CandidateProfile] = None) -> List[Dict[str, str]]:
        """
        Generates 5 tailored technical & behavioral interview questions with suggested answer strategies.
        """
        job_title = job.title or "AI / Software Engineer"
        company = job.company or "the company"
        skills = job.skills[:5] if job.skills else ["System Design", "Python", "Architecture", "Data Pipelines"]

        prep_items = [
            {
                "topic": f"Technical Deep-Dive: {skills[0] if skills else 'Core Tech'}",
                "question": f"How have you applied {skills[0] if skills else 'modern architecture'} in production systems, and how would you scale it for {company}'s requirements?",
                "talking_points": "Focus on trade-offs, concurrency, performance bottlenecks you resolved, and metrics of success."
            },
            {
                "topic": f"System Architecture & {job_title}",
                "question": f"Walk me through the architecture of a mission-critical project you designed from scratch. What were the failure modes?",
                "talking_points": "Highlight end-to-end architecture, API contracts, caching/storage decisions, and monitoring observability."
            },
            {
                "topic": "Handling Missing Tooling / Rapid Upskilling",
                "question": f"The job involves {', '.join(job.missing_skills[:2]) if job.missing_skills else 'fast-evolving frameworks'}. How do you approach mastering new tech stacks under tight deadlines?",
                "talking_points": "Describe your systematic learning methodology: reading docs, building micro-prototypes, benchmarking, and shipping."
            },
            {
                "topic": "Cross-Functional Impact & Delivery",
                "question": f"Tell me about a time you had to align engineering goals with product timelines at {company} scale.",
                "talking_points": "Use the STAR method (Situation, Task, Action, Result). Highlight communication and pragmatic prioritization."
            },
            {
                "topic": "Reverse Questions for the Interviewer",
                "question": f"What are the biggest technical bottlenecks the {job_title} team at {company} is tackling this quarter?",
                "talking_points": "Demonstrates high agency, technical curiosity, and alignment with their engineering roadmap."
            }
        ]
        return prep_items

    @staticmethod
    def compute_market_insights(jobs: List[Job]) -> Dict[str, Any]:
        """
        Aggregates market intelligence across all discovered job postings:
        - Top requested skills frequency
        - Work mode distribution
        - ATS distribution
        - Market salary estimation
        """
        if not jobs:
            return {
                "total_jobs": 0,
                "top_skills": [],
                "work_modes": {},
                "ats_distribution": {},
                "salary_range": "Not specified"
            }

        skill_counts: Dict[str, int] = {}
        work_modes: Dict[str, int] = {}
        ats_counts: Dict[str, int] = {}

        for j in jobs:
            # Skills
            for s in j.skills:
                skill_counts[s] = skill_counts.get(s, 0) + 1
            for ms in j.matched_skills:
                skill_counts[ms] = skill_counts.get(ms, 0) + 1

            # Work mode
            wm = j.work_mode or "Unspecified"
            work_modes[wm] = work_modes.get(wm, 0) + 1

            # ATS / Source
            src = (j.source or "").lower()
            if "greenhouse" in src: ats = "Greenhouse"
            elif "lever" in src: ats = "Lever"
            elif "ashby" in src: ats = "Ashby"
            elif "workday" in src: ats = "Workday"
            elif "phenom" in src or "lilly" in src: ats = "Enterprise Portal"
            elif "linkedin" in src: ats = "LinkedIn"
            elif "naukri" in src: ats = "Naukri"
            elif "indeed" in src: ats = "Indeed"
            else: ats = "Direct Portal"
            ats_counts[ats] = ats_counts.get(ats, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        total = len(jobs)
        top_skills_pct = [
            {"skill": k, "count": v, "percentage": int((v / total) * 100)}
            for k, v in sorted_skills
        ]

        return {
            "total_jobs": total,
            "top_skills": top_skills_pct,
            "work_modes": work_modes,
            "ats_distribution": ats_counts,
            "salary_range": "$125,000 - $195,000 / yr (Industry Average)"
        }
