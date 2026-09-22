from typing import Dict, Optional

from models.scout_session import ScoutSession

_SESSIONS: Dict[str, ScoutSession] = {}


def save(session: ScoutSession) -> ScoutSession:
    _SESSIONS[session.session_id] = session
    return session


def get(session_id: str) -> Optional[ScoutSession]:
    return _SESSIONS.get(session_id)
