import itertools

import pytest

from autoresearch.agents import AgentRegistry, AgentFactory
from autoresearch.agents.feedback import FeedbackEvent
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager
from autoresearch.storage_typing import JSONDict


# Register a coalition to exercise coalition handling
AgentRegistry.create_coalition("ReviewTeam", ["Contrarian", "FactChecker"])

ALL_PAIRS = list(itertools.combinations(AgentRegistry.list_available(), 2))
COALITIONS = AgentRegistry.list_coalitions()


def make_agent(name: str, order: list[str]):
    class DummyAgent:
        def __init__(self, name: str, llm_adapter=None) -> None:
            self.name = name

        def can_execute(
            self,
            state: QueryState,
            config: ConfigModel,
        ) -> bool:  # noqa: D401
            _ = state, config
            return True

        def execute(
            self,
            state: QueryState,
            config: ConfigModel,
            **kwargs: object,
        ) -> JSONDict:  # noqa: D401
            _ = config, kwargs
            state.update(
                {
                    "claims": [
                        {"id": self.name, "type": "fact", "content": self.name}
                    ],
                    "results": {self.name: "ok"},
                }
            )
            if self.name == "Contrarian" and "FactChecker" in order:
                state.add_feedback_event(
                    FeedbackEvent(
                        source="Contrarian",
                        target="FactChecker",
                        content="check",
                        cycle=state.cycle,
                    )
                )
            if self.name == "FactChecker":
                _ = state.get_feedback_events(recipient="FactChecker")
            if self.name == "Synthesizer" or self.name == order[-1]:
                state.results["final_answer"] = f"Answer from {self.name}"
            payload: JSONDict = {"results": {self.name: "ok"}}
            return payload

    return DummyAgent(name)


@pytest.mark.parametrize("agents", ALL_PAIRS)
def test_all_agent_pairs(
    monkeypatch: pytest.MonkeyPatch,
    agents: tuple[str, str],
) -> None:
    order: list[str] = list(agents)

    def _persist_claim(_: JSONDict, partial_update: bool = False) -> None:
        _ = partial_update
        return None

    monkeypatch.setattr(StorageManager, "persist_claim", _persist_claim)
    monkeypatch.setattr(
        AgentFactory, "get", lambda name, llm_adapter=None: make_agent(name, order)
    )

    loader = ConfigLoader.new_for_tests()
    cfg = loader.config
    cfg.agents = order
    cfg.loops = 1
    cfg.enable_feedback = True

    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert response.answer


@pytest.mark.parametrize("coalition", COALITIONS)
def test_registered_coalitions(
    monkeypatch: pytest.MonkeyPatch,
    coalition: str,
) -> None:
    members = AgentRegistry.get_coalition(coalition)
    order = ["Synthesizer"] + members

    def _persist_claim(_: JSONDict, partial_update: bool = False) -> None:
        _ = partial_update
        return None

    monkeypatch.setattr(StorageManager, "persist_claim", _persist_claim)
    monkeypatch.setattr(
        AgentFactory, "get", lambda name, llm_adapter=None: make_agent(name, order)
    )

    loader = ConfigLoader.new_for_tests()
    cfg = loader.config
    cfg.agents = ["Synthesizer", coalition]
    cfg.coalitions = {coalition: members}
    cfg.loops = 1
    cfg.enable_feedback = True

    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert response.answer
