import pytest
from autoresearch.config import ConfigModel
from autoresearch.orchestration import ReasoningMode
from autoresearch.errors import ConfigError


@pytest.mark.parametrize(
    "value, expected",
    [(ReasoningMode.DIRECT, ReasoningMode.DIRECT), ("direct", ReasoningMode.DIRECT)],
)
def test_reasoning_mode_valid(value, expected):
    cfg = ConfigModel(reasoning_mode=value)
    assert cfg.reasoning_mode == expected


def test_reasoning_mode_invalid():
    with pytest.raises(ConfigError):
        ConfigModel(reasoning_mode="invalid")


@pytest.mark.parametrize("budget", [None, 10])
def test_token_budget_valid(budget):
    cfg = ConfigModel(token_budget=budget)
    assert cfg.token_budget == budget


@pytest.mark.parametrize("budget", [0, -5])
def test_token_budget_invalid(budget):
    with pytest.raises(ConfigError):
        ConfigModel(token_budget=budget)


@pytest.mark.parametrize("policy", ["LRU", "score"])
def test_eviction_policy_valid(policy):
    cfg = ConfigModel(graph_eviction_policy=policy)
    assert cfg.graph_eviction_policy == policy


def test_eviction_policy_invalid():
    with pytest.raises(ConfigError):
        ConfigModel(graph_eviction_policy="bad")
