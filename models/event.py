from pydantic import BaseModel


class Event(BaseModel):

    type: str

    message: str

    data: dict = {}