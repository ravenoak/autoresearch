from typing import Any, Optional

from pydantic import BaseModel


class FeedbackEvent(BaseModel):
    """Represents feedback from one agent to another."""

    source: str
    target: str
    content: str
    cycle: int
    metadata: Optional[dict[str, Any]] = None
