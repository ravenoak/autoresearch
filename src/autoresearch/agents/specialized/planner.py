"""
PlannerAgent for structuring complex research tasks.

This agent is responsible for breaking down complex research queries into
structured plans, identifying key questions to answer, and organizing the
research process to ensure comprehensive coverage of the topic.
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


class PlannerAgent(Agent):
    """Structures complex research tasks into organized plans."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Planner"

    def execute(
        self, state: QueryState, config: ConfigModel
    ) -> Dict[str, Any]:
        """Create a structured research plan for the query."""
        log.info(f"PlannerAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Generate a research plan using the prompt template
        prompt = self.generate_prompt("planner.research_plan", query=state.query)
        research_plan = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(research_plan, "research_plan")
        return self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.PLANNING,
            },
            results={"research_plan": research_plan}
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Best executed at the beginning of the research process."""
        # The Planner is most useful at the beginning of the process
        # or when there are no existing claims
        is_beginning = state.cycle == 0 or len(state.claims) == 0
        return super().can_execute(state, config) and is_beginning