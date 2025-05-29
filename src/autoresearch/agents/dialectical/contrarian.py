"""
ContrarianAgent for challenging existing thesis with alternative viewpoints.
"""
from typing import Dict, Any
from uuid import uuid4
import logging

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState

log = logging.getLogger(__name__)


class ContrarianAgent(Agent):
    """Challenges thesis with alternative viewpoints."""
    role = AgentRole.CONTRARIAN

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Generate counterpoints to existing claims."""
        log.info(f"ContrarianAgent executing (cycle {state.cycle})")

        # Implementation would analyze existing claims and generate counterpoints

        return {
            "claims": [
                {
                    "id": str(uuid4()),
                    "type": "antithesis",
                    "content": f"Counterpoint to existing claims for: {state.query}"
                }
            ],
            "metadata": {"phase": DialoguePhase.ANTITHESIS},
            "results": {"antithesis": f"Counterpoint for: {state.query}"}
        }

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute if there's at least one thesis claim."""
        has_thesis = any(claim.get("type") == "thesis" for claim in state.claims)
        return super().can_execute(state, config) and has_thesis
