"""Coverage for adaptive token budgeting."""

from __future__ import annotations

from tests.helpers.modules import ensure_stub_module
from tests.typing_helpers import make_config_model

ensure_stub_module(
    "pydantic_settings",
    {
        "BaseSettings": object,
        "CliApp": object,
        "SettingsConfigDict": dict,
    },
)

from autoresearch.orchestration.budgeting import _apply_adaptive_token_budget  # noqa: E402


def test_budget_none_leaves_value() -> None:
    """No token budget leaves config unchanged."""
    cfg = make_config_model(token_budget=None)
    _apply_adaptive_token_budget(cfg, "one two")
    assert cfg.token_budget is None


def test_budget_adjusts_for_loops() -> None:
    """Loops reduce available budget."""
    cfg = make_config_model(token_budget=50, loops=2)
    _apply_adaptive_token_budget(cfg, "alpha beta")
    assert cfg.token_budget == 25


def test_budget_caps_maximum() -> None:
    """Budget above cap reduces to query-based max."""
    cfg = make_config_model(token_budget=500)
    query = " ".join(["q"] * 10)
    _apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget == 200


def test_budget_raises_minimum() -> None:
    """Budget below query tokens adds buffer."""
    cfg = make_config_model(token_budget=5)
    query = " ".join(["q"] * 10)
    _apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget == 20


def test_budget_stays_within_range() -> None:
    """Budget within bounds remains unchanged."""
    cfg = make_config_model(token_budget=50, loops=1)
    query = " ".join(["q"] * 5)
    _apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget == 50
