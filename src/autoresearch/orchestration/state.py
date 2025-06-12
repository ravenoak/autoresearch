"""
State management for the dialectical reasoning process.
"""

from typing import List, Dict, Any
import time
from pydantic import BaseModel, Field

from ..models import QueryResponse


class QueryState(BaseModel):
    """State object passed between agents during dialectical cycles."""

    query: str
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
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
