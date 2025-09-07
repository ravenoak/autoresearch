import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.budgeting import _apply_adaptive_token_budget


@pytest.mark.requires_llm
def test_budget_scaled_by_loops_and_capped() -> None:
    cfg = ConfigModel(token_budget=100, loops=3, adaptive_max_factor=5, adaptive_min_buffer=2)
    _apply_adaptive_token_budget(cfg, "one two three four five")
    assert cfg.token_budget == 25


@pytest.mark.requires_llm
def test_budget_increased_when_too_low() -> None:
    cfg = ConfigModel(token_budget=5, loops=1, adaptive_min_buffer=2)
    _apply_adaptive_token_budget(cfg, "one two three four five six seven")
    assert cfg.token_budget == 9


@pytest.mark.requires_llm
def test_budget_unchanged_when_within_bounds() -> None:
    cfg = ConfigModel(token_budget=30, loops=1, adaptive_max_factor=10, adaptive_min_buffer=5)
    _apply_adaptive_token_budget(cfg, "one two three")
    assert cfg.token_budget == 30


@pytest.mark.requires_llm
def test_budget_noop_when_missing() -> None:
    cfg = ConfigModel()
    _apply_adaptive_token_budget(cfg, "hello world")
    assert cfg.token_budget is None
