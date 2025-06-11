"""
SynthesizerAgent responsible for thesis creation and final synthesis.
"""
from typing import Dict, Any
from uuid import uuid4

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...synthesis import build_answer, build_rationale
from ...llm import get_llm_adapter

log = get_logger(__name__)


class SynthesizerAgent(Agent):
    """Creates initial thesis and final synthesis."""
    role: AgentRole = AgentRole.SYNTHESIZER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Synthesize claims and sources into coherent thesis or synthesis."""
        log.info(f"SynthesizerAgent executing (cycle {state.cycle})")

        adapter = get_llm_adapter(config.llm_backend)
        model_cfg = config.agent_config.get("Synthesizer")
        model = model_cfg.model if model_cfg and model_cfg.model else config.default_model

        mode = config.reasoning_mode
        is_first_cycle = state.cycle == 0

        if mode == ReasoningMode.DIRECT:
            prompt = f"Answer the query directly: {state.query}"
            answer = adapter.generate(prompt, model=model)
            result = {
                "claims": [
                    {
                        "id": str(uuid4()),
                        "type": "synthesis",
                        "content": answer,
                    }
                ],
                "metadata": {"phase": DialoguePhase.SYNTHESIS},
                "results": {"final_answer": answer, "synthesis": answer},
            }
        elif is_first_cycle:
            prompt = f"Provide a thesis for the query: {state.query}"
            thesis_text = adapter.generate(prompt, model=model)
            result = {
                "claims": [
                    {
                        "id": str(uuid4()),
                        "type": "thesis",
                        "content": thesis_text,
                    }
                ],
                "metadata": {"phase": DialoguePhase.THESIS},
                "results": {"thesis": thesis_text},
            }
        else:
            prompt = (
                "Synthesize an answer from the following claims:\n" +
                "\n".join(c.get("content", "") for c in state.claims)
            )
            synthesis_text = adapter.generate(prompt, model=model)
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
                    "final_answer": synthesis_text,
                    "synthesis": synthesis_text,
                },
            }

        return result
