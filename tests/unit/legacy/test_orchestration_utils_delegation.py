import importlib
from types import SimpleNamespace

import autoresearch.orchestration.orchestration_utils as ou


def test_get_agent_delegates(monkeypatch):
    def dummy(agent_id, factory):
        return "ok"

    monkeypatch.setattr("autoresearch.orchestration.execution._get_agent", dummy)
    mod = importlib.reload(ou)
    assert mod.OrchestrationUtils.get_agent("A", SimpleNamespace(get=lambda x: x)) == "ok"


def test_capture_token_usage_delegates(monkeypatch):
    def dummy(agent_name, metrics, config):
        return "ctx"

    monkeypatch.setattr(
        "autoresearch.orchestration.token_utils._capture_token_usage", dummy
    )
    mod = importlib.reload(ou)
    assert mod.OrchestrationUtils.capture_token_usage("A", 1, 2) == "ctx"
