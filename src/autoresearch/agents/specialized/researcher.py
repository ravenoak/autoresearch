"""
ResearcherAgent focused on deep information gathering.

This agent is responsible for conducting in-depth research on a topic,
gathering information from multiple sources, and providing comprehensive
research results.
"""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search

log = get_logger(__name__)


class ResearcherAgent(Agent):
    """Conducts deep information gathering from multiple sources."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Researcher"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Conduct in-depth research on the query topic."""
        log.info(f"ResearcherAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Retrieve external references with more results than standard fact checking
        max_results = config.max_results_per_query * 2  # Double the standard results
        raw_sources = Search.external_lookup(state.query, max_results=max_results)
        sources = []
        for s in raw_sources:
            s = dict(s)
            s["agent"] = self.name
            sources.append(s)

        # Extract key information from sources
        sources_text = "\n\n".join(
            [
                f"Source {i + 1}: {s.get('title', 'Untitled')}\n{s.get('content', 'No content')}"
                for i, s in enumerate(sources)
            ]
        )

        # Generate research findings using the prompt template
        prompt = self.generate_prompt(
            "researcher.findings", query=state.query, sources=sources_text
        )
        research_findings = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(research_findings, "research_findings")
        return self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.RESEARCH,
                "source_count": len(sources),
            },
            results={"research_findings": research_findings},
            sources=sources,
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Determine if this agent should execute in the current state."""
        # The Researcher can execute in any reasoning mode
        return super().can_execute(state, config)
