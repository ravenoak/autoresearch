from typing import Any
from unittest.mock import MagicMock

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration import token_utils
import autoresearch.llm as llm


def test_capture_token_usage_counts(
    monkeypatch: pytest.MonkeyPatch, flexible_llm_adapter: Any
) -> None:
    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "flexible"
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: flexible_llm_adapter)

    with token_utils._capture_token_usage("agent", metrics, mock_config) as (
        _counter,
        adapter,
    ):
        adapter.generate("hello world")

    counts: dict[str, int] = metrics.token_counts["agent"]
    assert counts["in"] == 2
    assert counts["out"] > 0


def test_execute_with_adapter_injection_methods() -> None:
    class AgentWithParam:
        def __init__(self) -> None:
            self.used: Any | None = None

        def execute(self, state: QueryState, config: ConfigModel, *, adapter: Any = None):
            self.used = adapter
            return {"ok": True}

    class AgentWithSetter:
        def __init__(self) -> None:
            self.adapter = "orig"

        def set_adapter(self, adapter: Any) -> None:
            self.adapter = adapter

        def get_adapter(self) -> Any:
            return self.adapter

        def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
            return {"adapter": self.adapter}

    state = QueryState(query="q")
    cfg = ConfigModel.model_construct()
    adapter = object()

    agent1 = AgentWithParam()
    result1 = token_utils._execute_with_adapter(agent1, state, cfg, adapter)
    assert result1 == {"ok": True}
    assert agent1.used is adapter

    agent2 = AgentWithSetter()
    result2 = token_utils._execute_with_adapter(agent2, state, cfg, adapter)
    assert result2["adapter"] is adapter
    # original adapter restored after execution
    assert agent2.adapter == "orig"
