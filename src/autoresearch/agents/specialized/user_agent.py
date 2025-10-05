"""
UserAgent for representing user preferences and requirements.

This agent is responsible for representing the user's perspective,
preferences, and requirements in the dialogue, ensuring that the
research and analysis remain aligned with the user's needs.
"""

from typing import Dict, Any, List

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


class UserAgent(Agent):
    """Represents the user's perspective, preferences, and requirements."""

    role: AgentRole = AgentRole.USER
    name: str = "User"

    # User preferences that can be configured
    preferences: Dict[str, Any] = {
        "detail_level": "balanced",  # "concise", "balanced", or "detailed"
        "perspective": "neutral",    # "neutral", "critical", or "optimistic"
        "format_preference": "structured",  # "structured", "narrative", or "bullet_points"
        "expertise_level": "intermediate",  # "beginner", "intermediate", or "expert"
        "focus_areas": [],  # List of specific areas to focus on
        "excluded_areas": [],  # List of areas to exclude
    }

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Represent the user's perspective and provide feedback on the current state."""
        log.info(f"UserAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Load user preferences from config if available
        self._load_preferences(config)

        # Extract recent claims and results to evaluate
        recent_claims = self._get_recent_claims(state)
        current_results = self._extract_current_results(state)

        # Format the claims and results for the prompt
        claims_text = self._format_claims(recent_claims)
        results_text = self._format_results(current_results)

        # Generate user feedback using the prompt template
        prompt = self.generate_prompt(
            "user.feedback",
            query=state.query,
            claims=claims_text,
            results=results_text,
            preferences=self._format_preferences(),
            cycle=state.cycle
        )

        feedback = adapter.generate(prompt, model=model)

        # Generate user requirements and expectations
        requirements_prompt = self.generate_prompt(
            "user.requirements",
            query=state.query,
            feedback=feedback,
            preferences=self._format_preferences(),
            cycle=state.cycle
        )

        requirements = adapter.generate(requirements_prompt, model=model)

        # Create and return the result
        feedback_claim = self.create_claim(feedback, "user_feedback")
        requirements_claim = self.create_claim(requirements, "user_requirements")

        result = self.create_result(
            claims=[feedback_claim, requirements_claim],
            metadata={
                "phase": DialoguePhase.FEEDBACK,
                "user_preferences": self.preferences,
                "evaluated_claims": [c.get("id") for c in recent_claims],
            },
            results={
                "user_feedback": feedback,
                "user_requirements": requirements,
                "user_preferences": self.preferences
            },
        )

        if getattr(config, "enable_agent_messages", False):
            if state.coalitions:
                for c, m in state.coalitions.items():
                    if self.name in m:
                        self.broadcast(
                            state,
                            f"User feedback available in cycle {state.cycle}",
                            coalition=c,
                        )
            else:
                self.send_message(state, "User feedback available")

        if getattr(config, "enable_feedback", False):
            targets = {c.get("agent") for c in recent_claims if c.get("agent")}
            for tgt in targets:
                if tgt:
                    self.send_feedback(state, tgt, feedback)

        return result

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute when there are claims to evaluate and after initial research."""
        # Need at least some claims to provide feedback on
        has_claims = len(state.claims) > 0

        # Preferably execute after at least one cycle of research/analysis
        is_appropriate_cycle = state.cycle >= 1

        return super().can_execute(state, config) and has_claims and is_appropriate_cycle

    def _load_preferences(self, config: ConfigModel) -> None:
        """Load user preferences from config if available."""
        if hasattr(config, "user_preferences") and isinstance(config.user_preferences, dict):
            # Update preferences with values from config
            for key, value in config.user_preferences.items():
                if key in self.preferences:
                    self.preferences[key] = value

            log.info(f"Loaded user preferences from config: {self.preferences}")

    def _get_recent_claims(self, state: QueryState) -> List[Dict[str, Any]]:
        """Get the most recent claims from the state, up to a limit."""
        # Get the most recent 5 claims, or all if fewer than 5
        max_claims = 5
        selected = state.claims[-max_claims:] if len(state.claims) > max_claims else state.claims
        return [dict(claim) for claim in selected]

    def _extract_current_results(self, state: QueryState) -> Dict[str, Any]:
        """Extract current results from the state."""
        # Collect all results from the state
        all_results: Dict[str, Any] = {}

        # Combine results from all agents
        for agent_result in state.results.values():
            if isinstance(agent_result, dict):
                all_results.update(agent_result)

        return all_results

    def _format_claims(self, claims: List[Dict[str, Any]]) -> str:
        """Format claims for inclusion in the prompt."""
        formatted_claims = []

        for i, claim in enumerate(claims, 1):
            agent = claim.get("agent", "Unknown Agent")
            content = claim.get("content", "No content")
            claim_type = claim.get("type", "statement")

            formatted_claims.append(f"Claim {i} ({agent}, {claim_type}):\n{content}")

        if not formatted_claims:
            return "No claims available yet."

        return "\n\n".join(formatted_claims)

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format results for inclusion in the prompt."""
        formatted_results = []

        # Filter out metadata and focus on actual results
        result_keys_to_include = [
            "answer", "synthesis", "critique", "analysis",
            "recommendations", "domain_analysis", "research_findings"
        ]

        for key in result_keys_to_include:
            if key in results and results[key]:
                formatted_results.append(f"{key.replace('_', ' ').title()}:\n{results[key]}")

        if not formatted_results:
            return "No results available yet."

        return "\n\n".join(formatted_results)

    def _format_preferences(self) -> str:
        """Format user preferences for inclusion in the prompt."""
        formatted_prefs = ["User Preferences:"]

        for key, value in self.preferences.items():
            # Format the key for better readability
            readable_key = key.replace("_", " ").title()

            # Format list values
            if isinstance(value, list):
                if value:
                    value_str = ", ".join(value)
                else:
                    value_str = "None specified"
            else:
                value_str = str(value)

            formatted_prefs.append(f"- {readable_key}: {value_str}")

        return "\n".join(formatted_prefs)
