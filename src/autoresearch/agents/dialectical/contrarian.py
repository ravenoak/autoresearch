"""ContrarianAgent challenges the thesis with alternative viewpoints."""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


class ContrarianAgent(Agent):
    """Challenges thesis with alternative viewpoints."""

    role: AgentRole = AgentRole.CONTRARIAN

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Generate counterpoints to existing claims."""
        log.info(f"ContrarianAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Find the thesis to challenge
        thesis = next(
            (c for c in state.claims if c.get("type") == "thesis"),
            None,
        )
        thesis_text = thesis.get("content") if thesis else state.query

        # Generate an antithesis using the prompt template
        prompt = self.generate_prompt("contrarian.antithesis", thesis=thesis_text)
        antithesis = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(antithesis, "antithesis")
        return self.create_result(
            claims=[claim],
            metadata={"phase": DialoguePhase.ANTITHESIS},
            results={"antithesis": antithesis},
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute in dialectical mode when there's a thesis."""
        if config.reasoning_mode != ReasoningMode.DIALECTICAL:
            return False
        has_thesis = any(claim.get("type") == "thesis" for claim in state.claims)
        return super().can_execute(state, config) and has_thesis
