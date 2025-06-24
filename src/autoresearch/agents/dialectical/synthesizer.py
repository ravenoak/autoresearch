"""SynthesizerAgent creates the thesis and final synthesis."""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


class SynthesizerAgent(Agent):
    """Creates initial thesis and final synthesis."""

    role: AgentRole = AgentRole.SYNTHESIZER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Synthesize claims and sources into coherent thesis or synthesis."""
        log.info(f"SynthesizerAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)
        mode = config.reasoning_mode
        is_first_cycle = state.cycle == 0

        if mode == ReasoningMode.DIRECT:
            # Direct reasoning mode: Answer the query directly
            prompt = self.generate_prompt("synthesizer.direct", query=state.query)
            answer = adapter.generate(prompt, model=model)

            claim = self.create_claim(answer, "synthesis")
            return self.create_result(
                claims=[claim],
                metadata={"phase": DialoguePhase.SYNTHESIS},
                results={"final_answer": answer, "synthesis": answer},
            )

        elif is_first_cycle:
            # First cycle: Generate a thesis
            prompt = self.generate_prompt("synthesizer.thesis", query=state.query)
            thesis_text = adapter.generate(prompt, model=model)

            claim = self.create_claim(thesis_text, "thesis")
            return self.create_result(
                claims=[claim],
                metadata={"phase": DialoguePhase.THESIS},
                results={"thesis": thesis_text},
            )

        else:
            # Later cycles: Synthesize from claims
            claims_text = "\n".join(c.get("content", "") for c in state.claims)
            prompt = self.generate_prompt("synthesizer.synthesis", claims=claims_text)
            synthesis_text = adapter.generate(prompt, model=model)

            claim = self.create_claim(synthesis_text, "synthesis")
            return self.create_result(
                claims=[claim],
                metadata={"phase": DialoguePhase.SYNTHESIS},
                results={"final_answer": synthesis_text, "synthesis": synthesis_text},
            )
