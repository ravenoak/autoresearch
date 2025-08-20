"""Unit tests for :mod:`autoresearch.config_utils`."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoresearch.config_utils import apply_preset, validate_config
from autoresearch.errors import ConfigError


def test_apply_preset_returns_configuration() -> None:
    """Return configuration dictionary for a known preset."""
    cfg = apply_preset("Default")
    assert cfg is not None
    assert cfg["loops"] == 2
    assert cfg["reasoning_mode"] == "dialectical"


def test_apply_preset_unknown_name() -> None:
    """Return ``None`` when preset name is unrecognised."""
    assert apply_preset("non-existent") is None


def test_validate_config_success() -> None:
    """Validation succeeds when the loader does not raise errors."""
    loader = MagicMock()
    loader.load_config.return_value = {}

    ok, errors = validate_config(loader)

    assert ok is True
    assert errors == []


def test_validate_config_failure() -> None:
    """Return ``False`` and an error message when validation fails."""
    loader = MagicMock()
    loader.load_config.side_effect = ConfigError("broken")

    ok, errors = validate_config(loader)

    assert ok is False
    assert errors == ["broken"]
