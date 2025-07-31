from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError, NotFoundError, TimeoutError, OrchestrationError


def test_parse_config_direct():
    cfg = ConfigModel(reasoning_mode=ReasoningMode.DIRECT)
    params = Orchestrator._parse_config(cfg)
    assert params["agents"] == ["Synthesizer"]
    assert params["loops"] == 1


def test_rotate_list_wraps():
    assert Orchestrator._rotate_list([1, 2, 3], 4) == [2, 3, 1]


def test_adaptive_token_budget():
    cfg = ConfigModel(token_budget=1000, loops=4)
    Orchestrator._apply_adaptive_token_budget(cfg, "a b c")
    assert cfg.token_budget == 60


def test_categorize_error_cases():
    assert Orchestrator._categorize_error(TimeoutError()) == "transient"
    nf = NotFoundError("x", resource_type="a", resource_id="b")
    assert Orchestrator._categorize_error(nf) == "recoverable"
    assert Orchestrator._categorize_error(AgentError("configuration bad")) == "recoverable"
    assert Orchestrator._categorize_error(AgentError("boom")) == "critical"
    assert Orchestrator._categorize_error(OrchestrationError("oops")) == "critical"


def test_apply_recovery_strategy(monkeypatch):
    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy("A", "transient", Exception("e"), state)
    assert info["recovery_strategy"] == "retry_with_backoff"
    assert "fallback" in state.results
    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy("A", "recoverable", Exception("e"), state)
    assert info["recovery_strategy"] == "fallback_agent"
    assert "fallback" in state.results
    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy("A", "critical", Exception("e"), state)
    assert info["recovery_strategy"] == "fail_gracefully"
    assert "error" in state.results
