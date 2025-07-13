"""
SummarizerAgent for concise output generation.

This agent is responsible for distilling complex information into clear,
concise summaries that capture the essential points while maintaining
accuracy and context.
"""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


class SummarizerAgent(Agent):
    """Generates concise summaries of complex information."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Summarizer"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Generate a concise summary of the current state."""
        log.info(f"SummarizerAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Collect all relevant content to summarize
        content_to_summarize = []

        # Include all claims from the state
        for claim in state.claims:
            content_to_summarize.append(
                {
                    "type": claim.get("type", "unknown"),
                    "content": claim.get("content", "No content"),
                }
            )

        # Extract content from claims
        content_text = "\n\n".join(
            [
                f"Content ({item['type']}): {item['content']}"
                for item in content_to_summarize
            ]
        )

        # Generate summary using the prompt template
        prompt = self.generate_prompt(
            "summarizer.concise", query=state.query, content=content_text
        )
        summary = adapter.generate(prompt, model=model)

        # Create and return the result
        claim = self.create_claim(summary, "summary")
        result = self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.SUMMARY,
                "summarized_items": len(content_to_summarize),
            },
            results={"summary": summary},
        )

        if getattr(config, "enable_agent_messages", False):
            if state.coalitions:
                for c, m in state.coalitions.items():
                    if self.name in m:
                        self.broadcast(
                            state,
                            f"Summary ready in cycle {state.cycle}",
                            coalition=c,
                        )
            else:
                self.send_message(state, "Summary ready")

        return result

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute when there is content to summarize."""
        has_content = len(state.claims) > 0
        return super().can_execute(state, config) and has_content
