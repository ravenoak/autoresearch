"""
ModeratorAgent for managing complex dialogues.

This agent is responsible for facilitating discussions between other agents,
ensuring productive dialogue, resolving conflicts, and guiding the conversation
towards a constructive resolution.
"""

from typing import Dict, Any, List

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


class ModeratorAgent(Agent):
    """Facilitates discussions between agents and guides complex dialogues."""

    role: AgentRole = AgentRole.MODERATOR
    name: str = "Moderator"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Moderate the dialogue between agents and guide the conversation."""
        log.info(f"ModeratorAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Extract recent claims from different agents to analyze the dialogue
        recent_claims = self._get_recent_claims(state)

        # Identify any conflicts or disagreements between agents
        conflicts = self._identify_conflicts(recent_claims)

        # Extract the dialogue history as a formatted conversation
        dialogue_history = self._format_dialogue_history(recent_claims)

        # Generate moderation using the prompt template
        prompt = self.generate_prompt(
            "moderator.dialogue",
            query=state.query,
            dialogue_history=dialogue_history,
            conflicts=conflicts,
            cycle=state.cycle
        )

        if getattr(config, "enable_feedback", False):
            fb = self.format_feedback(state)
            if fb:
                prompt += f"\n\nPeer feedback:\n{fb}\n"

        moderation = adapter.generate(prompt, model=model)

        # Create guidance for next steps in the dialogue
        guidance_prompt = self.generate_prompt(
            "moderator.guidance",
            query=state.query,
            dialogue_history=dialogue_history,
            moderation=moderation,
            cycle=state.cycle
        )

        if getattr(config, "enable_feedback", False):
            fb = self.format_feedback(state)
            if fb:
                guidance_prompt += f"\n\nPeer feedback:\n{fb}\n"

        guidance = adapter.generate(guidance_prompt, model=model)

        # Create and return the result
        moderation_claim = self.create_claim(moderation, "moderation")
        guidance_claim = self.create_claim(guidance, "guidance")

        result = self.create_result(
            claims=[moderation_claim, guidance_claim],
            metadata={
                "phase": DialoguePhase.MODERATION,
                "analyzed_claims": [c.get("id") for c in recent_claims],
                "conflicts_identified": len(conflicts) > 0,
            },
            results={
                "moderation": moderation,
                "guidance": guidance,
                "conflicts": conflicts
            },
        )

        if getattr(config, "enable_agent_messages", False):
            if state.coalitions:
                for c, m in state.coalitions.items():
                    if self.name in m:
                        self.broadcast(
                            state,
                            f"Moderation guidance ready in cycle {state.cycle}",
                            coalition=c,
                        )
            else:
                self.send_message(state, "Moderation guidance ready")

        return result

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute when there are multiple claims from different agents."""
        # Need at least 3 claims to have a meaningful dialogue to moderate
        has_sufficient_claims = len(state.claims) >= 3

        # Check if we have claims from at least 2 different agents
        agent_set = set()
        for claim in state.claims:
            if "agent" in claim:
                agent_set.add(claim["agent"])

        has_multiple_agents = len(agent_set) >= 2

        return (
            super().can_execute(state, config)
            and has_sufficient_claims
            and has_multiple_agents
        )

    def _get_recent_claims(self, state: QueryState) -> List[Dict[str, Any]]:
        """Get the most recent claims from the state, up to a limit."""
        # Get the most recent 10 claims, or all if fewer than 10
        max_claims = 10
        return state.claims[-max_claims:] if len(state.claims) > max_claims else state.claims

    def _identify_conflicts(self, claims: List[Dict[str, Any]]) -> List[str]:
        """Identify potential conflicts or disagreements between claims."""
        conflicts = []

        # Simple heuristic: look for claims with contradictory language
        contradiction_markers = [
            "however", "but", "contrary", "disagree", "incorrect",
            "false", "misleading", "inaccurate", "dispute"
        ]

        for claim in claims:
            content = claim.get("content", "").lower()
            for marker in contradiction_markers:
                if marker in content:
                    conflicts.append(
                        f"Potential conflict in claim from {claim.get('agent', 'unknown agent')}: "
                        f"'{content[:100]}...'"
                    )
                    break

        return conflicts

    def _format_dialogue_history(self, claims: List[Dict[str, Any]]) -> str:
        """Format the claims as a dialogue history."""
        dialogue = []

        for claim in claims:
            agent = claim.get("agent", "Unknown Agent")
            content = claim.get("content", "No content")
            claim_type = claim.get("type", "statement")

            dialogue.append(f"{agent} ({claim_type}): {content}")

        return "\n\n".join(dialogue)
