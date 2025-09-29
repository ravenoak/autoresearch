from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
import time
from typing import Any, Optional
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

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """Return message as plain dictionary."""
        return self.model_dump(by_alias=True)
