"""Tests for Streamlit rerun helper compatibility."""

from __future__ import annotations

import types

from autoresearch import streamlit_app


class _DummyStreamlit(types.SimpleNamespace):
    """Minimal stub of the Streamlit module used for rerun tests."""


def test_trigger_rerun_falls_back_to_experimental(monkeypatch):
    """Ensure the helper uses the experimental rerun path when necessary."""

    calls: list[str] = []

    def _experimental() -> None:
        calls.append("experimental")

    fake_st = _DummyStreamlit(experimental_rerun=_experimental)
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app._trigger_rerun()

    assert calls == ["experimental"]


def test_trigger_rerun_prefers_stable_api(monkeypatch):
    """Ensure the helper calls the stable rerun API when both exist."""

    calls: list[str] = []

    def _stable() -> None:
        calls.append("stable")

    def _experimental() -> None:
        calls.append("experimental")

    fake_st = _DummyStreamlit(rerun=_stable, experimental_rerun=_experimental)
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app._trigger_rerun()

    assert calls == ["stable"]
