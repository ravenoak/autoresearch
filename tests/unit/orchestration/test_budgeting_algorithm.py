from types import SimpleNamespace

from autoresearch.orchestration.budgeting import _apply_adaptive_token_budget


def test_budget_scaled_by_loops_and_limits() -> None:
    config = SimpleNamespace(token_budget=300, loops=3, adaptive_max_factor=20)
    _apply_adaptive_token_budget(config, "one two three four")
    assert config.token_budget == 80


def test_budget_minimum_buffer_applied() -> None:
    config = SimpleNamespace(token_budget=1, loops=1, adaptive_min_buffer=10)
    _apply_adaptive_token_budget(config, "a b c d e")
    assert config.token_budget == 15


def test_budget_unchanged_within_bounds() -> None:
    config = SimpleNamespace(token_budget=50, loops=1)
    _apply_adaptive_token_budget(config, "a b c d e")
    assert config.token_budget == 50
