"""
FactChecker agent for verifying claims against external sources.
"""
from typing import Dict, Any
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search
from ...llm import get_llm_adapter

log = get_logger(__name__)


class FactChecker(Agent):
    """Verifies claims against external knowledge sources."""
    role: AgentRole = AgentRole.FACT_CHECKER

    def execute(
        self, state: QueryState, config: ConfigModel
    ) -> Dict[str, Any]:
        """Check existing claims for factual accuracy."""
        log.info(f"FactChecker executing (cycle {state.cycle})")

        adapter = get_llm_adapter(config.llm_backend)
        model_cfg = config.agent_config.get("FactChecker")
        model = (
            model_cfg.model
            if model_cfg and model_cfg.model
            else config.default_model
        )

        # Retrieve external references
        raw_sources = Search.external_lookup(
            state.query, max_results=config.max_results_per_query
        )
        sources = []
        for s in raw_sources:
            s = dict(s)
            s["checked_claims"] = [c["id"] for c in state.claims]
            s["agent"] = self.name
            sources.append(s)

        prompt = (
            "Verify the following claims:\n" +
            "\n".join(c.get("content", "") for c in state.claims)
        )
        verification = adapter.generate(prompt, model=model)

        return {
            "claims": [
                {
                    "id": str(uuid4()),
                    "type": "verification",
                    "content": verification,
                }
            ],
            "sources": sources,
            "metadata": {
                "phase": DialoguePhase.VERIFICATION,
                "source_count": len(sources),
            },
            "results": {"verification": verification},
        }

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute in dialectical mode if there are claims."""
        if config.reasoning_mode != ReasoningMode.DIALECTICAL:
            return False
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims
