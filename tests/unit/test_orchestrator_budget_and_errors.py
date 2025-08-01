import pytest
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, TimeoutError, NotFoundError, AgentError


def test_adaptive_budget_scales_with_loops():
    cfg = ConfigModel(token_budget=100, loops=3)
    Orchestrator._apply_adaptive_token_budget(cfg, "one two")
    assert cfg.token_budget <= 100
    assert cfg.token_budget >= len("one two".split())


@pytest.mark.parametrize(
    "exc,expected",
    [
        (TimeoutError("t"), "transient"),
        (NotFoundError("x", resource_type="a", resource_id="b"), "recoverable"),
        (AgentError("fatal"), "critical"),
    ],
)
def test_error_categorization(exc, expected):
    assert Orchestrator._categorize_error(exc) == expected
