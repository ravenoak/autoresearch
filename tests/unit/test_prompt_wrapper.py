"""Tests for the enhanced prompt wrapper."""

from __future__ import annotations

from collections import deque
from typing import Any

import typer

from autoresearch.main import Prompt


def test_prompt_toolkit_flow_uses_history_and_completions(monkeypatch: Any) -> None:
    """Ensure the prompt-toolkit path wires history and completions."""

    class FakeHistory:
        def __init__(self) -> None:
            self.entries: list[str] = []

        def append_string(self, value: str) -> None:
            self.entries.append(value)

    class FakeCompletion:
        def __init__(self, text: str, start_position: int = 0) -> None:
            self.text = text
            self.start_position = start_position

    class FakeCompleter:
        def get_completions(self, document: Any, complete_event: Any) -> list[Any]:
            return []

    class FakeDocument:
        def __init__(self, text: str) -> None:
            self.text_before_cursor = text

    class FakePromptSession:
        instances: list["FakePromptSession"] = []

        def __init__(self, *, history: FakeHistory | None = None) -> None:
            self.history = history or FakeHistory()
            self.completer: Any = None
            self.calls: list[dict[str, Any]] = []
            self.completions: dict[str, list[str]] = {}
            FakePromptSession.instances.append(self)

        def prompt(
            self,
            message: str,
            *,
            default: str = "",
            multiline: bool = False,
            complete_in_thread: bool = False,
        ) -> str:
            self.calls.append(
                {
                    "message": message,
                    "default": default,
                    "multiline": multiline,
                    "complete_in_thread": complete_in_thread,
                }
            )
            if self.completer is not None:
                for probe in ("Synth", "--"):
                    completions = list(self.completer.get_completions(FakeDocument(probe), None))
                    self.completions[probe] = [completion.text for completion in completions]
            if self.history is not None:
                self.history.append_string(" Synthesizer ")
            return " Synthesizer "

    FakePromptSession.instances = []

    fake_modules = {
        "PromptSession": FakePromptSession,
        "Completer": type("BaseCompleter", (FakeCompleter,), {}),
        "Completion": FakeCompletion,
        "History": FakeHistory,
    }

    monkeypatch.setattr(Prompt, "_PROMPT_TOOLKIT_MODULES", fake_modules)
    monkeypatch.setattr(Prompt, "_PROMPT_SESSION", None)
    monkeypatch.setattr(Prompt, "_PROMPT_HISTORY", None)
    monkeypatch.setattr(Prompt, "_RECENT_ENTRIES", deque(maxlen=32))
    monkeypatch.setattr(Prompt, "_should_use_prompt_toolkit", lambda: True)
    monkeypatch.setattr(Prompt, "_collect_agent_names", lambda: {"Synthesizer"})
    monkeypatch.setattr(Prompt, "_collect_command_options", lambda: {"--interactive"})

    result = Prompt.ask(
        "Enter query",
        default="",
        validator=lambda value: value.strip(),
    )

    session = FakePromptSession.instances[-1]
    assert session.calls[0]["multiline"] is True
    assert "Synthesizer" in session.completions.get("Synth", [])
    assert "--interactive" in session.completions.get("--", [])
    assert result == "Synthesizer"
    assert list(Prompt._RECENT_ENTRIES)[-1] == "Synthesizer"


def test_typer_fallback_retries_until_valid(monkeypatch: Any) -> None:
    """The Typer fallback honours validators and choices."""

    monkeypatch.setattr(Prompt, "_should_use_prompt_toolkit", lambda: False)
    monkeypatch.setattr(Prompt, "_RECENT_ENTRIES", deque(maxlen=32))

    responses = iter(["invalid", "  good  "])
    calls: list[dict[str, Any]] = []

    def fake_prompt(text: str, *args: Any, **kwargs: Any) -> str:
        calls.append({"text": text, "kwargs": kwargs})
        return next(responses)

    messages: list[str] = []

    def fake_echo(message: str) -> None:
        messages.append(message)

    monkeypatch.setattr(typer, "prompt", fake_prompt)
    monkeypatch.setattr(typer, "echo", fake_echo)

    def _validator(value: str) -> str:
        cleaned = value.strip()
        if cleaned != "good":
            raise typer.BadParameter("try again")
        return cleaned

    result = Prompt.ask("Confirm", choices=["good"], validator=_validator)

    assert result == "good"
    assert len(calls) == 2
    assert any("try again" in message for message in messages)
    assert list(Prompt._RECENT_ENTRIES)[-1] == "good"
