"""
ContrarianAgent for challenging existing thesis with alternative viewpoints.
"""
from typing import Dict, Any
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...llm import get_llm_adapter

log = get_logger(__name__)


class ContrarianAgent(Agent):
    """Challenges thesis with alternative viewpoints."""
    role: AgentRole = AgentRole.CONTRARIAN

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Generate counterpoints to existing claims."""
        log.info(f"ContrarianAgent executing (cycle {state.cycle})")

        adapter = get_llm_adapter(config.llm_backend)
        model_cfg = config.agent_config.get("Contrarian")
        model = model_cfg.model if model_cfg and model_cfg.model else config.default_model

        thesis = next((c for c in state.claims if c.get("type") == "thesis"), None)
        thesis_text = thesis.get("content") if thesis else state.query
        prompt = f"Provide an antithesis to the following thesis:\n{thesis_text}"
        antithesis = adapter.generate(prompt, model=model)

        return {
            "claims": [
                {
                    "id": str(uuid4()),
                    "type": "antithesis",
                    "content": antithesis,
                }
            ],
            "metadata": {"phase": DialoguePhase.ANTITHESIS},
            "results": {"antithesis": antithesis},
        }

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute if there's at least one thesis claim."""
        has_thesis = any(claim.get("type") == "thesis" for claim in state.claims)
        return super().can_execute(state, config) and has_thesis
