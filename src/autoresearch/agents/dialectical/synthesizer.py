"""
SynthesizerAgent responsible for thesis creation and final synthesis.
"""
from typing import Dict, Any
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...synthesis import build_answer, build_rationale

log = get_logger(__name__)


class SynthesizerAgent(Agent):
    """Creates initial thesis and final synthesis."""
    role = AgentRole.SYNTHESIZER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Synthesize claims and sources into coherent thesis or synthesis."""
        log.info(f"SynthesizerAgent executing (cycle {state.cycle})")

        # Implementation would call LLM with appropriate prompts
        # based on whether this is first cycle (thesis) or later (synthesis)

        is_first_cycle = state.cycle == 0

        if is_first_cycle:
            # Generate initial thesis
            result = {
                "claims": [
                    {
                        "id": str(uuid4()),
                        "type": "thesis",
                        "content": f"Initial thesis for: {state.query}"
                    }
                ],
                "metadata": {"phase": DialoguePhase.THESIS},
                "results": {"thesis": f"Initial thesis for: {state.query}"}
            }
        else:
            # Generate synthesis from existing claims and evidence
            synthesis_text = build_rationale(state.claims)
            result = {
                "claims": [
                    {
                        "id": str(uuid4()),
                        "type": "synthesis",
                        "content": synthesis_text,
                    }
                ],
                "metadata": {"phase": DialoguePhase.SYNTHESIS},
                "results": {
                    "final_answer": build_answer(state.query, state.claims),
                    "synthesis": synthesis_text,
                },
            }

        return result
