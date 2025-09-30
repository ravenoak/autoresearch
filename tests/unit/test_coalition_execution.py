
from autoresearch.config.models import ConfigModel
from autoresearch.agents.registry import AgentFactory, AgentRegistry
import pytest
from pathlib import Path
from typing import Any


class DummyAgent:
    def __init__(self, name: str, record: list[str]) -> None:
        self.name = name
        self.record = record

    def can_execute(self, state, config) -> bool:
        return True

    def execute(self, state, config):
        self.record.append(self.name)
        return {}


def test_coalition_agents_run_together(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, orchestrator: Any) -> None:
    record: list[str] = []

    with AgentRegistry.temporary_state(), AgentFactory.temporary_state():
        def get_agent(name):
            return DummyAgent(name, record)

        AgentFactory.register("A", DummyAgent)
        AgentFactory.register("B", DummyAgent)

        cfg = ConfigModel.from_dict(
            {"loops": 1, "agents": ["team"], "coalitions": {"team": ["A", "B"]}}
        )

        monkeypatch.setattr(
            "autoresearch.orchestration.orchestrator.AgentFactory.get", get_agent
        )
        monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "rel.json"))
        monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", str(tmp_path / "qt.json"))

        orchestrator.run_query("q", cfg)

        assert set(record[:2]) == {"A", "B"}


def test_configmodel_from_dict_allows_coalitions() -> None:
    cfg = ConfigModel.from_dict(
        {"loops": 1, "agents": ["team"], "coalitions": {"team": ["A", "B"]}}
    )
    assert cfg.agents == ["team"]
    assert cfg.coalitions == {"team": ["A", "B"]}
