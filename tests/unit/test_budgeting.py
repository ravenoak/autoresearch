from autoresearch.orchestration.budgeting import _apply_adaptive_token_budget
from tests.helpers import make_config_model


def test_apply_adaptive_token_budget_paths() -> None:
    cfg = make_config_model(
        token_budget=100,
        loops=2,
        adaptive_max_factor=10,
        adaptive_min_buffer=5,
    )
    _apply_adaptive_token_budget(cfg, "one two three four five")
    assert cfg.token_budget == 50  # reduced due to loops then limited by max factor

    cfg2 = make_config_model(
        token_budget=1,
        loops=1,
        adaptive_max_factor=20,
        adaptive_min_buffer=10,
    )
    _apply_adaptive_token_budget(cfg2, "two words")
    assert cfg2.token_budget == 12  # increased due to query longer than budget

    cfg3 = make_config_model(token_budget=None)
    _apply_adaptive_token_budget(cfg3, "any")
    assert getattr(cfg3, "token_budget", None) is None
