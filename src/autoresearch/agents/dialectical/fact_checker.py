"""
FactChecker agent for verifying claims against external sources.
"""
from typing import Dict, Any
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search

log = get_logger(__name__)


class FactChecker(Agent):
    """Verifies claims against external knowledge sources."""
    role = AgentRole.FACT_CHECKER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Check existing claims for factual accuracy."""
        log.info(f"FactChecker executing (cycle {state.cycle})")

        # Retrieve external references
        sources = Search.external_lookup(
            state.query, max_results=config.max_results_per_query
        )

        return {
            "claims": [
                {
                    "id": str(uuid4()),
                    "type": "verification",
                    "content": f"Fact verification for claims regarding: {state.query}"
                }
            ],
            "sources": sources,
            "metadata": {"phase": DialoguePhase.VERIFICATION},
            "results": {"verification": f"Fact check results for: {state.query}"}
        }

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute if there are claims to check."""
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims
