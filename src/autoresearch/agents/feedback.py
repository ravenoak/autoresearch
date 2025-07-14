from pydantic import BaseModel
from typing import Optional


class FeedbackEvent(BaseModel):
    """Represents feedback from one agent to another."""

    source: str
    target: str
    content: str
    cycle: int
    metadata: Optional[dict] = None
