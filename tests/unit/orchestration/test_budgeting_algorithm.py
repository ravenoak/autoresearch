from __future__ import annotations

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.budgeting import _apply_adaptive_token_budget
from autoresearch.models import ReasoningMode
from tests.helpers import make_config_model


def _typed_config(
    *,
    token_budget: int | None = None,
    loops: int = 2,
    adaptive_max_factor: int = 20,
    adaptive_min_buffer: int = 10,
) -> ConfigModel:
    stub = make_config_model(
        token_budget=token_budget,
        loops=loops,
        adaptive_max_factor=adaptive_max_factor,
        adaptive_min_buffer=adaptive_min_buffer,
        reasoning_mode=ReasoningMode.DIRECT,
    )
    return ConfigModel.model_validate(stub.model_dump())


def test_budget_scaled_by_loops_and_limits() -> None:
    config = _typed_config(
        token_budget=300, loops=3, adaptive_max_factor=20
    )
    _apply_adaptive_token_budget(config, "one two three four")
    assert config.token_budget == 80


def test_budget_minimum_buffer_applied() -> None:
    config = _typed_config(
        token_budget=1, loops=1, adaptive_min_buffer=10
    )
    _apply_adaptive_token_budget(config, "a b c d e")
    assert config.token_budget == 15


def test_budget_unchanged_within_bounds() -> None:
    config = _typed_config(token_budget=50, loops=1)
    _apply_adaptive_token_budget(config, "a b c d e")
    assert config.token_budget == 50
