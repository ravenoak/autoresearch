"""
State management for the dialectical reasoning process.
"""

from typing import List, Dict, Any, Optional

from ..agents.feedback import FeedbackEvent
from ..agents.messages import MessageProtocol
import time
from pydantic import BaseModel, Field

from ..models import QueryResponse


class QueryState(BaseModel):
    """State object passed between agents during dialectical cycles."""

    query: str
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_events: List[FeedbackEvent] = Field(default_factory=list)
    coalitions: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cycle: int = 0
    primus_index: int = 0
    last_updated: float = Field(default_factory=time.time)
    error_count: int = 0

    def update(self, result: Dict[str, Any]) -> None:
        """Update state with agent result."""
        if "claims" in result:
            self.claims.extend(result["claims"])
        if "sources" in result:
            self.sources.extend(result["sources"])
        for k, v in result.get("metadata", {}).items():
            self.metadata[k] = v
        # Update results with agent-specific outputs
        self.results.update(result.get("results", {}))
        # Update timestamp
        self.last_updated = time.time()

    def add_error(self, error_info: Dict[str, Any]) -> None:
        """Track execution errors."""
        self.error_count += 1
        if "errors" not in self.metadata:
            self.metadata["errors"] = []
        self.metadata["errors"].append(error_info)

    def add_message(self, message: Dict[str, Any]) -> None:
        """Store a message exchanged between agents."""
        self.messages.append(message)

    def add_feedback_event(self, event: FeedbackEvent) -> None:
        """Store a feedback event exchanged between agents."""
        self.feedback_events.append(event)

    def get_feedback_events(self, *, recipient: Optional[str] = None) -> List[FeedbackEvent]:
        """Retrieve feedback events for a specific recipient."""
        events = self.feedback_events
        if recipient is not None:
            events = [e for e in events if e.target == recipient]
        return events

    # ------------------------------------------------------------------
    # Coalition management utilities
    # ------------------------------------------------------------------

    def add_coalition(self, name: str, members: List[str]) -> None:
        """Register a coalition of agents.

        Args:
            name: Name of the coalition
            members: Agent names that belong to the coalition
        """
        self.coalitions[name] = members

    def remove_coalition(self, name: str) -> None:
        """Remove a coalition if it exists."""
        self.coalitions.pop(name, None)

    def get_coalition_members(self, name: str) -> List[str]:
        """Return members of a coalition."""
        return self.coalitions.get(name, [])

    def get_messages(
        self,
        *,
        recipient: Optional[str] = None,
        coalition: Optional[str] = None,
        protocol: MessageProtocol | None = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve messages for a specific recipient or coalition."""
        messages = self.messages
        if recipient is not None:
            messages = [m for m in messages if m.get("to") in (None, recipient)]
        if coalition is not None:
            members = self.coalitions.get(coalition, [])
            messages = [m for m in messages if m.get("from") in members]
        if protocol is not None:
            messages = [m for m in messages if m.get("protocol") == protocol.value]
        return messages

    def synthesize(self) -> QueryResponse:
        """Create final response from state."""
        # Default implementation - can be overridden by SynthesizerAgent
        return QueryResponse(
            answer=self.results.get("final_answer", "No answer synthesized"),
            citations=self.sources,
            reasoning=self.claims,
            metrics=self.metadata,
        )

    def get_dialectical_structure(self) -> Dict[str, Any]:
        """Extract thesis, antithesis, verification, and synthesis claims."""
        structure: Dict[str, Any] = {
            "thesis": None,
            "antithesis": [],
            "verification": [],
            "synthesis": None,
        }

        # Extract claims by type
        for claim in self.claims:
            claim_type = claim.get("type")
            if claim_type == "thesis":
                structure["thesis"] = claim
            elif claim_type == "antithesis":
                structure["antithesis"].append(claim)
            elif claim_type == "verification":
                structure["verification"].append(claim)
            elif claim_type == "synthesis":
                structure["synthesis"] = claim

        return structure

    def prune_context(
        self,
        max_claims: int = 50,
        max_sources: int = 20,
        max_messages: int = 50,
        max_feedback: int = 50,
    ) -> None:
        """Prune stored context to keep the state manageable.

        This method removes the oldest claims and sources when their count
        exceeds the provided limits. A summary of the number of items pruned
        is stored under ``metadata['pruned']``.

        Args:
            max_claims: Maximum number of claims to keep.
            max_sources: Maximum number of sources to keep.
        """

        pruned = {"claims": 0, "sources": 0, "messages": 0, "feedback": 0}

        if len(self.claims) > max_claims:
            excess = len(self.claims) - max_claims
            del self.claims[0:excess]
            pruned["claims"] = excess

        if len(self.sources) > max_sources:
            excess = len(self.sources) - max_sources
            del self.sources[0:excess]
            pruned["sources"] = excess

        if len(self.messages) > max_messages:
            excess = len(self.messages) - max_messages
            del self.messages[0:excess]
            pruned["messages"] = excess

        if len(self.feedback_events) > max_feedback:
            excess = len(self.feedback_events) - max_feedback
            del self.feedback_events[0:excess]
            pruned["feedback"] = excess

        if any(pruned.values()):
            self.metadata.setdefault("pruned", []).append(pruned)
