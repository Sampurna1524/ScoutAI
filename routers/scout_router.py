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
    experience_years: Optional[float] = None
    experience_months: Optional[int] = None
    experience_level: Optional[str] = ""
    location: Optional[str] = ""
    work_mode: Optional[str] = ""
    employment_type: Optional[str] = ""
    skills: Optional[str] = ""
    salary_min: Optional[str] = ""
    posted_within: Optional[str] = ""  # e.g. "24h", "3d", "week", "month"
    candidate_profile: Optional[Dict[str, Any]] = None


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

    # 2. Target Company
    if body.company and body.company.strip():
        parts.append(body.company.strip())

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
