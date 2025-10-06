# mypy: ignore-errors
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

from autoresearch import streamlit_ui

pytestmark = pytest.mark.requires_ui


class Session(dict[str, Any]):
    def __getattr__(self, item: str) -> Any:
        return self[item]

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def test_apply_accessibility_settings_no_high_contrast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, ...]] = []

    def record_markdown(*args: Any, **_kwargs: Any) -> None:
        calls.append(args)

    fake_st = types.SimpleNamespace(
        markdown=record_markdown,
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.apply_accessibility_settings()
    assert len(calls) == 1


def test_apply_theme_settings_light(monkeypatch: pytest.MonkeyPatch) -> None:
    m = MagicMock()
    fake_st = types.SimpleNamespace(markdown=m, session_state={"dark_mode": False})
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.apply_theme_settings()
    assert m.called and "background-color:#fff" in m.call_args[0][0]


class _DummyContext:
    def __init__(self) -> None:
        self.entered = False

    def __enter__(self) -> "_DummyContext":
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        return None


def test_display_guided_tour_dismiss(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _DummyContext()
    calls: dict[str, int] = {"modal": 0}

    def track_modal(*_args: Any, **_kwargs: Any) -> _DummyContext:
        calls["modal"] += 1
        return ctx

    def noop_markdown(*_args: Any, **_kwargs: Any) -> None:
        return None

    def always_true_button(*_args: Any, **_kwargs: Any) -> bool:
        return True

    fake_st = types.SimpleNamespace(
        markdown=noop_markdown,
        modal=track_modal,
        button=always_true_button,
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.display_guided_tour()
    assert fake_st.session_state.show_tour is False
    assert calls["modal"] == 1 and ctx.entered


def test_display_help_sidebar_dismiss(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _DummyContext()

    def expand_sidebar(*_args: Any, **_kwargs: Any) -> _DummyContext:
        return ctx

    sidebar = types.SimpleNamespace(expander=expand_sidebar)

    def noop_markdown(*_args: Any, **_kwargs: Any) -> None:
        return None

    def always_true_button(*_args: Any, **_kwargs: Any) -> bool:
        return True

    fake_st = types.SimpleNamespace(
        markdown=noop_markdown,
        sidebar=sidebar,
        button=always_true_button,
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.display_help_sidebar()
    assert fake_st.session_state.first_visit is False
    assert ctx.entered
