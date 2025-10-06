"""Tests for configure_logging_from_env helper."""

import logging
import pytest

from autoresearch import logging_utils


def test_configure_logging_from_env(monkeypatch):
    captured = {}

    def fake_configure_logging(*, level: int) -> None:
        captured["level"] = level

    monkeypatch.setenv("AUTORESEARCH_LOG_LEVEL", "DEBUG")
    monkeypatch.setattr(logging_utils, "configure_logging", fake_configure_logging)

    logging_utils.configure_logging_from_env()

    assert captured["level"] == logging.DEBUG


def test_configure_logging_from_env_invalid(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_LOG_LEVEL", "INVALID")

    with pytest.raises(ValueError):
        logging_utils.configure_logging_from_env()
