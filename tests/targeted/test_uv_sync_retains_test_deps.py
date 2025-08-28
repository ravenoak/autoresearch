"""Regression test ensuring essential test dependencies survive `uv sync`."""

from importlib import import_module


def test_uv_sync_retains_test_dependencies() -> None:
    """Verify `uv sync` keeps packages required for the test suite."""
    for module in ("pytest_bdd", "freezegun", "hypothesis"):
        import_module(module)
