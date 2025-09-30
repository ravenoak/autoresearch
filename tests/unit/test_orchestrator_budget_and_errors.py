import pytest
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import TimeoutError, NotFoundError, AgentError
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from typing import Any


def test_adaptive_budget_scales_with_loops() -> None:
    cfg = ConfigModel(token_budget=100, loops=3)
    OrchestrationUtils.apply_adaptive_token_budget(cfg, "one two")
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
def test_error_categorization(exc: Any, expected: Any) -> None:
    assert OrchestrationUtils.categorize_error(exc) == expected
