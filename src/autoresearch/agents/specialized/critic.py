"""
CriticAgent for evaluating the quality of research.

This agent is responsible for critically evaluating research findings,
identifying strengths and weaknesses, and providing constructive feedback
to improve the quality of the research.
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...llm.adapters import LLMAdapter

log = get_logger(__name__)


class CriticAgent(Agent):
    """Evaluates the quality of research and provides constructive feedback."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Critic"

    def execute(
        self, state: QueryState, config: ConfigModel
    ) -> Dict[str, Any]:
        """Evaluate the quality of research findings and provide feedback."""
        log.info(f"CriticAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Find research findings or other claims to evaluate
        claims_to_evaluate = []
        for claim in state.claims:
            # Include research findings and thesis/synthesis claims
            claim_type = claim.get("type", "")
            if claim_type in ["research_findings", "thesis", "synthesis"]:
                claims_to_evaluate.append(claim)

        if not claims_to_evaluate:
            # If no specific claims to evaluate, use all claims
            claims_to_evaluate = state.claims

        # Extract content from claims
        claims_text = "\n\n".join([
            f"Claim ({claim.get('type', 'unknown')}): {claim.get('content', 'No content')}"
            for claim in claims_to_evaluate
        ])

        # Generate critique using the prompt template
        prompt = self.generate_prompt("critic.evaluation", 
                                     query=state.query, 
                                     claims=claims_text)
        critique = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(critique, "critique")
        return self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.CRITIQUE,
                "evaluated_claims": [c.get("id") for c in claims_to_evaluate],
            },
            results={"critique": critique}
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute when there are claims to evaluate."""
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims