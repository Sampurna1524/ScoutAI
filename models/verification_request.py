from uuid import uuid4

from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    site: str
    url: str
    reason: str
    tab_index: int
    title: str = ""
    # pending = waiting for the user to accept or decline
    # accepted = user is completing login/verification in the browser
    # declined = user skipped this site
    # completed = user finished; agent may extract from the tab
    status: str = "pending"
    extracted: bool = False
    brought_to_front: bool = False
