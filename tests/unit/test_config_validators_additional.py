from pathlib import Path

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.errors import ConfigError
from autoresearch.orchestration import ReasoningMode
from typing import Any

SPEC_PATH = Path(__file__).resolve().parents[2] / "docs/algorithms/config_utils.md"


def test_config_spec_exists() -> None:
    """Configuration specification document must exist."""
    assert SPEC_PATH.is_file()


@pytest.mark.parametrize(
    "value, expected",
    [(ReasoningMode.DIRECT, ReasoningMode.DIRECT), ("direct", ReasoningMode.DIRECT)],
)
def test_reasoning_mode_valid(value: Any, expected: Any) -> None:
    cfg = ConfigModel.model_validate({"reasoning_mode": value})
    assert cfg.reasoning_mode == expected


def test_reasoning_mode_invalid() -> None:
    with pytest.raises(ConfigError):
        ConfigModel.model_validate({"reasoning_mode": "invalid"})


@pytest.mark.parametrize("budget", [None, 10])
def test_token_budget_valid(budget: Any) -> None:
    cfg = ConfigModel(token_budget=budget)
    assert cfg.token_budget == budget


@pytest.mark.parametrize("budget", [0, -5])
def test_token_budget_invalid(budget: Any) -> None:
    with pytest.raises(ConfigError):
        ConfigModel(token_budget=budget)


@pytest.mark.parametrize(
    "policy",
    ["LRU", "score", "hybrid", "priority", "adaptive"],
)
def test_eviction_policy_valid(policy: Any) -> None:
    cfg = ConfigModel(graph_eviction_policy=policy)
    assert cfg.graph_eviction_policy == policy


def test_eviction_policy_invalid() -> None:
    with pytest.raises(ConfigError):
        ConfigModel(graph_eviction_policy="bad")
