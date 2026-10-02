from typing import List, Optional
from pydantic import BaseModel, Field


class Job(BaseModel):

    title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    experience: str = ""
    experience_years: Optional[float] = None
    experience_months: Optional[int] = None
    employment_type: str = ""
    work_mode: str = ""
    posted_date: str = ""
    skills: List[str] = Field(default_factory=list)

    description: str = ""
    apply_url: str = ""

    # Tailored candidate match fields
    match_score: Optional[int] = None
    match_summary: Optional[str] = ""
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)

    source: str = ""
    status: str = ""
    error: str = ""

    # Auto-application tracking fields
    apply_type: Optional[str] = ""  # "easy_apply", "ats", "external"
    application_status: Optional[str] = "unapplied"  # "unapplied", "applying", "review_ready", "applied", "failed"
    applied_at: Optional[str] = ""
    application_notes: Optional[str] = ""