"""FactChecker agent verifies claims against external sources."""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search

log = get_logger(__name__)


class FactChecker(Agent):
    """Verifies claims against external knowledge sources."""

    role: AgentRole = AgentRole.FACT_CHECKER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Check existing claims for factual accuracy."""
        log.info(f"FactChecker executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Retrieve external references
        max_results = getattr(
            config, "max_results_per_query", 5
        )  # Default to 5 if not specified
        raw_sources = Search.external_lookup(state.query, max_results=max_results)
        sources = []
        for s in raw_sources:
            s = dict(s)
            s["checked_claims"] = [c["id"] for c in state.claims]
            s["agent"] = self.name
            sources.append(s)

        # Generate verification using the prompt template
        claims_text = "\n".join(c.get("content", "") for c in state.claims)
        prompt = self.generate_prompt("fact_checker.verification", claims=claims_text)
        verification = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(verification, "verification")
        return self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.VERIFICATION,
                "source_count": len(sources),
            },
            results={"verification": verification},
            sources=sources,
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute in dialectical mode if there are claims."""
        if config.reasoning_mode != ReasoningMode.DIALECTICAL:
            return False
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims
