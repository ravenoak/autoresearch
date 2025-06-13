import pytest

from autoresearch.orchestration.orchestrator import (
    Orchestrator,
    OrchestrationError,
)
from autoresearch.config import ConfigModel


class FailingAgent:
    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        raise ValueError("boom")


class Cfg(ConfigModel):
    max_errors: int = 1


def test_orchestrator_raises_after_error(monkeypatch):
    cfg = Cfg(agents=["Fail"], loops=1)

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: FailingAgent(),
    )

    with pytest.raises(OrchestrationError):
        Orchestrator.run_query("q", cfg)
