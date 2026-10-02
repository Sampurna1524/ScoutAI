import threading
from typing import Any, Dict, List, Optional
from uuid import uuid4

from models.event import Event
from models.job import Job
from models.verification_request import VerificationRequest


class ScoutSession:

    def __init__(self):

        self.session_id = str(uuid4())

        self.browser = None
        self.context = None
        self.pages: Dict[int, Any] = {}
        self.next_tab_index = 0

        self.jobs: List[Job] = []

        self.pending_verifications: List[VerificationRequest] = []

        self.events: List[Event] = []

        self.status = "created"

        self.query = ""
        self.filters: Dict[str, Any] = {}
        self.candidate_profile: Optional[Dict[str, Any]] = None
        self.error = ""

        self.agent_finished = False
        self.lock = threading.Lock()
        self.wake = threading.Event()

    def snapshot(self) -> dict:
        with self.lock:
            unresolved = [
                t for t in self.pending_verifications
                if t.status in ("pending", "accepted")
            ]
            return {
                "session_id": self.session_id,
                "query": self.query,
                "filters": self.filters,
                "candidate_profile": self.candidate_profile,
                "status": self.status,
                "error": self.error,
                "agent_finished": self.agent_finished,
                "waiting_on_user": bool(unresolved),
                "jobs": [job.model_dump() for job in self.jobs],
                "tasks": [task.model_dump() for task in self.pending_verifications],
                "events": [event.model_dump() for event in self.events],
            }

    def unresolved_tasks(self) -> List[VerificationRequest]:
        with self.lock:
            return [
                t for t in self.pending_verifications
                if t.status in ("pending", "accepted")
            ]

    def append_event(self, event_type: str, message: str, data: Optional[dict] = None):
        with self.lock:
            self.events.append(
                Event(type=event_type, message=message, data=data or {})
            )
