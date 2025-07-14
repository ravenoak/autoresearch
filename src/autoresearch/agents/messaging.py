from __future__ import annotations

"""Utilities for inter-agent messaging."""

from typing import Any, Dict, List
import time
from pydantic import BaseModel, Field

from ..orchestration.state import QueryState


class AgentMessage(BaseModel):
    """Representation of a message exchanged between agents."""

    sender: str = Field(..., alias="from")
    recipient: str | None = Field(None, alias="to")
    coalition: str | None = None
    type: str = "message"
    content: str
    cycle: int = 0
    timestamp: float = Field(default_factory=time.time)

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


class MessageBus:
    """Simple message bus storing messages in :class:`QueryState`."""

    @staticmethod
    def send(state: QueryState, message: AgentMessage) -> None:
        """Add a message to the state's message list."""

        state.add_message(message.model_dump(by_alias=True))

    @staticmethod
    def broadcast(state: QueryState, message: AgentMessage, coalition: str) -> None:
        """Broadcast a message to all members of a coalition."""

        members = state.coalitions.get(coalition, [])
        for member in members:
            msg = message.model_copy(update={"recipient": member, "coalition": coalition})
            MessageBus.send(state, msg)

    @staticmethod
    def inbox(state: QueryState, agent_name: str) -> List[Dict[str, Any]]:
        """Retrieve new messages for ``agent_name``."""

        delivered = state.metadata.setdefault("_delivered", {}).setdefault(agent_name, 0)
        messages = state.get_messages(recipient=agent_name)
        new = messages[delivered:]
        state.metadata["_delivered"][agent_name] = delivered + len(new)
        return new
