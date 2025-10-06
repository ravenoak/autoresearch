# mypy: ignore-errors
import types
from typing import Any

import pytest

from autoresearch import streamlit_app, streamlit_ui  # noqa: E402

pytestmark = pytest.mark.requires_ui


def test_apply_accessibility(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Any, ...]] = []

    def record_markdown(*args: Any, **_kwargs: Any) -> None:
        calls.append(args)

    fake_st = types.SimpleNamespace(
        markdown=record_markdown,
        session_state={"high_contrast": True},
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_app.apply_accessibility_settings()
    assert len(calls) == 2


def test_display_query_input_has_accessibility(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, list[Any]] = {"markdown": [], "form_submit_button": []}

    class Dummy:
        def __enter__(self) -> "Dummy":
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: Any,
        ) -> bool:
            return False

    def track_submit(*_args: Any, **kwargs: Any) -> bool:
        calls["form_submit_button"].append(kwargs)
        return False

    def record_markdown(*args: Any, **kwargs: Any) -> None:
        calls["markdown"].append((args, kwargs))

    def empty_text_area(*_args: Any, **_kwargs: Any) -> str:
        return ""

    def empty_selectbox(*_args: Any, **_kwargs: Any) -> None:
        return None

    def zero_slider(*_args: Any, **_kwargs: Any) -> int:
        return 0

    def false_button(*_args: Any, **_kwargs: Any) -> bool:
        return False

    def paired_columns(*_args: Any, **_kwargs: Any) -> tuple[Dummy, Dummy]:
        return (Dummy(), Dummy())

    def make_container(*_args: Any, **_kwargs: Any) -> Dummy:
        return Dummy()

    def make_form(*_args: Any, **_kwargs: Any) -> Dummy:
        return Dummy()

    fake_st = types.SimpleNamespace(
        markdown=record_markdown,
        text_area=empty_text_area,
        selectbox=empty_selectbox,
        slider=zero_slider,
        button=false_button,
        columns=paired_columns,
        container=make_container,
        form=make_form,
        form_submit_button=track_submit,
        session_state=types.SimpleNamespace(
            config=types.SimpleNamespace(
                reasoning_mode=streamlit_app.ReasoningMode.DIALECTICAL, loops=2
            )
        ),
    )
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    streamlit_app.display_query_input()
    assert any(
        "aria-label='Query input area'" in args[0] for args, _ in calls["markdown"]
    )
    assert any(
        "run your query" in kw.get("help", "") for kw in calls["form_submit_button"]
    )
