from __future__ import annotations

from pydantic import BaseModel, Field
import time
from typing import Optional
from enum import Enum


class MessageProtocol(str, Enum):
    """Communication protocol for agent messages."""

    DIRECT = "direct"
    BROADCAST = "broadcast"


class AgentMessage(BaseModel):
    """Structured message exchanged between agents."""

    sender: str = Field(..., alias="from")
    recipient: Optional[str] = Field(None, alias="to")
    coalition: Optional[str] = None
    type: str = "message"
    protocol: MessageProtocol = MessageProtocol.DIRECT
    content: str
    cycle: int
    timestamp: float = Field(default_factory=lambda: time.time())

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

    def to_dict(self) -> dict:
        """Return message as plain dictionary."""
        return self.model_dump(by_alias=True)
