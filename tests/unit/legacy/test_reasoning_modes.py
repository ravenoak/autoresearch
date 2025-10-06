# mypy: ignore-errors
from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import AgentExecutionResult
from tests.typing_helpers import AgentTestProtocol


class DummyAgent(AgentTestProtocol):
    def __init__(self, name: str, record: list[str]) -> None:
        self.name = name
        self.record = record

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(
        self, state: QueryState, config: ConfigModel, **_: object
    ) -> AgentExecutionResult:
        self.record.append(self.name)
        return {"claims": [], "results": {"final_answer": self.name}}


def _run(
    cfg: ConfigModel, orchestrator_factory: Callable[[], Orchestrator]
) -> list[str]:
    record: list[str] = []

    def get_agent(name: str, llm_adapter: object | None = None) -> AgentTestProtocol:
        return DummyAgent(name, record)

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        orchestrator_factory().run_query("q", cfg)

    return record


def test_direct_mode_executes_once(
    orchestrator_factory: Callable[[], Orchestrator]
) -> None:
    cfg = ConfigModel(loops=3, reasoning_mode=ReasoningMode.DIRECT)
    record: list[str] = _run(cfg, orchestrator_factory)
    assert record == ["Synthesizer"]


def test_chain_of_thought_mode_loops(
    orchestrator_factory: Callable[[], Orchestrator]
) -> None:
    cfg = ConfigModel(loops=2, reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT)
    record = _run(cfg, orchestrator_factory)
    assert record == ["Synthesizer", "Synthesizer"]


def test_chain_of_thought_records_steps(
    orchestrator_factory: Callable[[], Orchestrator]
) -> None:
    cfg = ConfigModel(loops=3, reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT)

    class DummySynth(AgentTestProtocol):
        def __init__(self) -> None:
            self.idx = 0

        def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
            return True

        def execute(
            self, state: QueryState, config: ConfigModel, **_: object
        ) -> AgentExecutionResult:
            self.idx += 1
            content = f"step-{self.idx}"
            return {
                "claims": [
                    {
                        "id": str(self.idx),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            }

    agent = DummySynth()
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        return_value=agent,
    ):
        resp = orchestrator_factory().run_query("q", cfg)

    steps = [c["content"] for c in resp.reasoning]
    assert steps == ["step-1", "step-2", "step-3"]
    assert resp.answer == "step-3"
