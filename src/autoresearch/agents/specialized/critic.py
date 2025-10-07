"""
CriticAgent for evaluating the quality of research.

This agent is responsible for critically evaluating research findings,
identifying strengths and weaknesses, and providing constructive feedback
to improve the quality of the research.
"""

from typing import Any, Dict

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...orchestration.reasoning_payloads import FrozenReasoningStep
from ...logging_utils import get_logger

log = get_logger(__name__)


class CriticAgent(Agent):
    """Evaluates the quality of research and provides constructive feedback."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Critic"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Evaluate the quality of research findings and provide feedback."""
        log.info(f"CriticAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Find research findings or other claims to evaluate
        claims_to_evaluate: list[dict[str, Any]] = []
        for claim_step in state.claims:
            payload = (
                claim_step.to_dict()
                if isinstance(claim_step, FrozenReasoningStep)
                else dict(claim_step)
            )
            # Include research findings and thesis/synthesis claims
            claim_type = payload.get("type", "")
            if claim_type in ["research_findings", "thesis", "synthesis"]:
                claims_to_evaluate.append(payload)

        if not claims_to_evaluate:
            # If no specific claims to evaluate, use all claims
            claims_to_evaluate = [
                (
                    claim_step.to_dict()
                    if isinstance(claim_step, FrozenReasoningStep)
                    else dict(claim_step)
                )
                for claim_step in state.claims
            ]

        # Extract content from claims
        claims_text = "\n\n".join(
            [
                f"Claim ({claim.get('type', 'unknown')}): {claim.get('content', 'No content')}"
                for claim in claims_to_evaluate
            ]
        )

        # Generate critique using the prompt template
        prompt = self.generate_prompt(
            "critic.evaluation", query=state.query, claims=claims_text
        )
        critique = adapter.generate(prompt, model=model)

        # Create and return the result
        critique_claim = self.create_claim(critique, "critique")
        result = self.create_result(
            claims=[critique_claim],
            metadata={
                "phase": DialoguePhase.CRITIQUE,
                "evaluated_claims": [c.get("id") for c in claims_to_evaluate],
            },
            results={"critique": critique},
        )

        if getattr(config, "enable_agent_messages", False):
            if state.coalitions:
                for c, m in state.coalitions.items():
                    if self.name in m:
                        self.broadcast(
                            state,
                            f"Critique ready in cycle {state.cycle}",
                            coalition=c,
                        )
            else:
                self.send_message(state, "Critique ready")

        if getattr(config, "enable_feedback", False):
            targets = {c.get("agent") for c in claims_to_evaluate if c.get("agent")}
            for tgt in targets:
                if tgt:
                    self.send_feedback(state, tgt, critique)

        return result

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute when there are claims to evaluate."""
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims
