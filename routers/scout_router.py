from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from agents.job_agent import JobAgent
from services import session_store
from services.verification_service import VerificationService

router = APIRouter(prefix="/scout", tags=["Scout"])


class StartSearchBody(BaseModel):
    query: Optional[str] = ""
    role: Optional[str] = ""
    company: Optional[str] = ""
    company_url: Optional[str] = ""
    experience_years: Optional[float] = None
    experience_months: Optional[int] = None
    experience_level: Optional[str] = ""
    location: Optional[str] = ""
    work_mode: Optional[str] = ""
    employment_type: Optional[str] = ""
    skills: Optional[str] = ""
    salary_min: Optional[str] = ""
    posted_within: Optional[str] = ""  # e.g. "24h", "3d", "week", "month"
    notification_email: Optional[str] = None
    send_email: Optional[bool] = True
    auto_apply_mode: Optional[str] = "off"  # "off", "review", "auto"
    auto_apply_top_n: Optional[int] = 5
    min_match_score: Optional[int] = 70
    candidate_profile: Optional[Dict[str, Any]] = None


class SingleJobApplyBody(BaseModel):
    job_url: str
    mode: Optional[str] = "review"  # "review" or "auto"


class TestEmailBody(BaseModel):
    email: str


class ProfileTextBody(BaseModel):
    text: str


class TaskActionBody(BaseModel):
    action: str


def build_search_query(body: StartSearchBody) -> str:
    if body.query and body.query.strip():
        return body.query.strip()

    parts = []
    
    # 1. Role / keywords
    if body.role and body.role.strip():
        parts.append(body.role.strip())
    else:
        parts.append("job openings")

    # 2. Target Company / Company URL
    if body.company and body.company.strip():
        parts.append(body.company.strip())
    elif body.company_url and body.company_url.strip():
        from services.company_career_service import CompanyCareerService
        info = CompanyCareerService.extract_company_info(body.company_url)
        c_name = info.get("company_name", "")
        if c_name:
            parts.append(c_name)

    # 3. Experience requirements
    if body.experience_years is not None:
        y = body.experience_years
        if y == 0:
            parts.append("fresher")
        elif y == 1:
            parts.append("1 year experience")
        else:
            y_str = f"{int(y)}" if isinstance(y, (int, float)) and float(y).is_integer() else f"{y}"
            parts.append(f"{y_str} years experience")
    elif body.experience_level and body.experience_level.strip() and body.experience_level.strip().lower() not in ("any", "all"):
        parts.append(body.experience_level.strip())

    # 4. Skills
    if body.skills and body.skills.strip():
        parts.append(body.skills.strip())

    # 5. Work Mode & Employment Type
    if body.work_mode and body.work_mode.strip() and body.work_mode.strip().lower() not in ("any", "all"):
        parts.append(body.work_mode.strip())

    # 6. Location
    if body.location and body.location.strip():
        parts.append(f"in {body.location.strip()}")

    return " ".join(parts).strip()


@router.post("/profile/upload")
async def upload_profile(
    file: Optional[Any] = None,
):
    from services.profile_service import ProfileService
    from fastapi import UploadFile, File

    raw_text = ""
    # We will handle file upload or raw text
    raise HTTPException(status_code=400, detail="Use specific endpoint")


@router.post("/profile/parse-file")
async def parse_profile_file(
    file: UploadFile = None,
):
    from services.profile_service import ProfileService
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    contents = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        text = ProfileService.extract_text_from_pdf(contents)
    else:
        try:
            text = contents.decode("utf-8")
        except UnicodeDecodeError:
            text = contents.decode("latin-1", errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from uploaded file")

    profile = ProfileService.parse_profile_text(text)
    return profile.model_dump()


@router.post("/profile/parse-text")
def parse_profile_text_endpoint(body: ProfileTextBody):
    from services.profile_service import ProfileService
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    profile = ProfileService.parse_profile_text(body.text)
    return profile.model_dump()


@router.post("/start")
def start_search(body: StartSearchBody):
    query = build_search_query(body)
    if not query:
        raise HTTPException(status_code=400, detail="Search query or filter criteria is required")
    
    filters = body.model_dump(exclude={"query", "candidate_profile"}, exclude_none=True)
    session = JobAgent.start_search(query, filters=filters, candidate_profile=body.candidate_profile)
    return session.snapshot()


@router.get("/{session_id}")
def get_session(session_id: str):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.snapshot()


@router.post("/{session_id}/tasks/{task_id}")
def update_task(session_id: str, task_id: str, body: TaskActionBody):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    action = body.action.strip().lower()
    if action not in ("accept", "decline", "complete"):
        raise HTTPException(status_code=400, detail="action must be accept, decline, or complete")

    status_map = {
        "accept": "accepted",
        "decline": "declined",
        "complete": "completed",
    }
    try:
        VerificationService.set_status(session, task_id, status_map[action])
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return session.snapshot()


@router.post("/test-email")
def test_email(body: TestEmailBody):
    from services.notification_service import NotificationService
    from models.job import Job

    sample_job = Job(
        title="AI/ML Engineer (Test Notification)",
        company="ScoutAI Demo Corp",
        location="Remote",
        experience_years=0,
        match_score=95,
        match_summary="Sample match summary for email verification.",
        matched_skills=["Python", "FastAPI", "PyTorch"],
        missing_skills=["Kubernetes"],
        apply_url="https://github.com",
        description="This is a test notification confirming your email dispatch is working perfectly."
    )

    success = NotificationService.send_top_matches(
        recipient=body.email.strip(),
        query="AI/ML Developer (Test)",
        jobs=[sample_job],
        total_discovered=1,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test email. Please check SMTP credentials.")
    return {"status": "success", "message": f"Test email sent to {body.email}"}


@router.post("/{session_id}/apply-job")
def apply_job_endpoint(session_id: str, body: SingleJobApplyBody):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    job = JobAgent.apply_to_single_job(session_id, body.job_url, mode=body.mode or "review")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in session")

    return {"status": "started", "job": job.model_dump(), "mode": body.mode}


class GeneratePitchBody(BaseModel):
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    description: Optional[str] = ""
    matched_skills: Optional[list] = []
    missing_skills: Optional[list] = []
    candidate_profile: Optional[Dict[str, Any]] = None
    tone: Optional[str] = "confident"


class InterviewPrepBody(BaseModel):
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    skills: Optional[list] = []
    missing_skills: Optional[list] = []
    candidate_profile: Optional[Dict[str, Any]] = None


@router.post("/generate-pitch")
def generate_pitch_endpoint(body: GeneratePitchBody):
    from services.ai_tailor_service import AiTailorService
    from models.job import Job
    from services.profile_service import CandidateProfile

    job = Job(
        title=body.job_title or "",
        company=body.company or "",
        description=body.description or "",
        matched_skills=body.matched_skills or [],
        missing_skills=body.missing_skills or [],
    )
    cand = CandidateProfile(**body.candidate_profile) if body.candidate_profile else None
    result = AiTailorService.generate_pitch_and_cover_letter(job, candidate=cand, tone=body.tone or "confident")
    return result


@router.post("/interview-prep")
def interview_prep_endpoint(body: InterviewPrepBody):
    from services.ai_tailor_service import AiTailorService
    from models.job import Job
    from services.profile_service import CandidateProfile

    job = Job(
        title=body.job_title or "",
        company=body.company or "",
        skills=body.skills or [],
        missing_skills=body.missing_skills or [],
    )
    cand = CandidateProfile(**body.candidate_profile) if body.candidate_profile else None
    questions = AiTailorService.generate_interview_prep(job, candidate=cand)
    return {"questions": questions}


@router.get("/{session_id}/market-insights")
def market_insights_endpoint(session_id: str):
    from services.ai_tailor_service import AiTailorService
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    insights = AiTailorService.compute_market_insights(session.jobs)
    return insights


@router.get("/{session_id}/export")
def export_session_endpoint(session_id: str, format: str = "csv"):
    import csv
    import io
    from fastapi.responses import Response

    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if format.lower() == "json":
        return session.snapshot()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title", "Company", "Location", "Work Mode", "Experience", "Match Score", "Matched Skills", "Missing Skills", "Apply URL", "Source", "Application Status"])

    for j in session.jobs:
        writer.writerow([
            j.title,
            j.company,
            j.location,
            j.work_mode,
            j.experience or (f"{j.experience_years} yrs" if j.experience_years is not None else ""),
            f"{j.match_score}%" if j.match_score is not None else "",
            ", ".join(j.matched_skills),
            ", ".join(j.missing_skills),
            j.apply_url,
            j.source,
            j.application_status
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scout_hunt_{session_id[:8]}.csv"}
    )

