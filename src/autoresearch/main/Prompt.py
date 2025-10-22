"""Interactive prompt helpers with optional prompt-toolkit support."""

from __future__ import annotations

import os
import sys
from collections import deque
from functools import lru_cache
from typing import Any, Callable, Iterable, Sequence

import typer

PromptValidator = Callable[[str], str | None]

_SUPPORTED_KWARGS = {"default", "prompt_suffix", "show_default", "show_choices", "choices"}
_PROMPT_TOOLKIT_SENTINEL: object = object()
_PROMPT_TOOLKIT_MODULES: dict[str, Any] | object = _PROMPT_TOOLKIT_SENTINEL
_PROMPT_SESSION: Any | None = None
_PROMPT_HISTORY: Any | None = None
_RECENT_ENTRIES: deque[str] = deque(maxlen=32)


def ask(text: str, *args: Any, **kwargs: Any) -> str:
    """Prompt the user for input with optional prompt-toolkit enhancements.

    Args:
        text: Prompt shown to the user.
        *args: Positional arguments forwarded to :func:`typer.prompt` when the
            enhanced prompt cannot be used.
        **kwargs: Keyword arguments accepted by :func:`typer.prompt`. This
            function additionally recognises ``validator`` for post-processing
            the response and ``choices`` for tab completion.

    Returns:
        Sanitised user input gathered from the console.
    """

    typer_kwargs = dict(kwargs)
    validator: PromptValidator | None = typer_kwargs.pop("validator", None)
    unsupported = set(typer_kwargs).difference(_SUPPORTED_KWARGS)

    use_prompt_toolkit = not args and not unsupported and _should_use_prompt_toolkit()

    if use_prompt_toolkit:
        choices = typer_kwargs.pop("choices", None)
        prompt_callable = _prompt_toolkit_callable(text, choices=choices, **typer_kwargs)
    else:
        choices = typer_kwargs.get("choices")

        def prompt_callable() -> str:
            return typer.prompt(text, *args, **typer_kwargs)

    while True:
        raw_value = prompt_callable()
        value = _normalize_default(raw_value, default=typer_kwargs.get("default"))
        try:
            value = _run_validator(value, validator)
        except typer.BadParameter as exc:  # pragma: no cover - defensive
            typer.echo(str(exc))
            continue
        except ValueError as exc:
            typer.echo(str(exc))
            continue

        if not _validate_choice(value, choices):
            typer.echo(f"Invalid choice: {value}. Valid options: {', '.join(choices or [])}")
            continue

        _record_response(value)
        return value


def _should_use_prompt_toolkit() -> bool:
    modules = _ensure_prompt_toolkit()
    if modules is None:
        return False
    if os.getenv("AUTORESEARCH_BARE_MODE", "false").lower() in {"true", "1", "yes", "on"}:
        return False
    return bool(sys.stdin and sys.stdin.isatty() and sys.stdout and sys.stdout.isatty())


def _prompt_toolkit_callable(
    text: str,
    *,
    default: Any | None = None,
    prompt_suffix: str | None = None,
    show_default: bool = True,
    show_choices: bool = True,
    choices: Sequence[str] | None = None,
) -> Callable[[], str]:
    modules = _ensure_prompt_toolkit()
    if modules is None:  # pragma: no cover - defensive
        raise RuntimeError("prompt_toolkit modules unavailable")

    message = _format_message(
        text,
        prompt_suffix=prompt_suffix if prompt_suffix is not None else ": ",
        default=default,
        show_default=show_default,
        show_choices=show_choices,
        choices=choices,
    )

    options = _gather_completion_candidates(choices=choices, default=default)

    session = _ensure_prompt_session(modules)
    session.completer = _build_completer(modules, options)

    def _prompt() -> str:
        return session.prompt(
            message,
            default=str(default) if default not in (None, "") else "",
            multiline=True,
            complete_in_thread=True,
        )

    return _prompt


def _normalize_default(value: str, *, default: Any | None) -> str:
    if value == "" and default not in (None, ""):
        return str(default)
    return value


def _run_validator(value: str, validator: PromptValidator | None) -> str:
    if validator is None:
        return value
    result = validator(value)
    if result is None:
        return value
    return result


def _validate_choice(value: str, choices: Sequence[str] | None) -> bool:
    if not choices or value == "":
        return True
    return value in choices


def _record_response(value: str) -> None:
    trimmed = value.strip()
    if trimmed:
        _RECENT_ENTRIES.append(trimmed)


def _format_message(
    text: str,
    *,
    prompt_suffix: str,
    default: Any | None,
    show_default: bool,
    show_choices: bool,
    choices: Sequence[str] | None,
) -> str:
    extras: list[str] = []
    if show_choices and choices:
        extras.append("/".join(choices))
    if show_default and default not in (None, ""):
        default_str = str(default)
        if not choices or default_str not in choices:
            extras.append(default_str)
    suffix = f" [{' | '.join(extras)}]" if extras else ""
    return f"{text}{suffix}{prompt_suffix}"


def _gather_completion_candidates(
    *, choices: Sequence[str] | None, default: Any | None
) -> Iterable[str]:
    options: set[str] = set()
    options.update(_collect_agent_names())
    options.update(_collect_command_options())
    options.update(_RECENT_ENTRIES)
    if choices:
        options.update(choices)
    if default not in (None, ""):
        options.add(str(default))
    return sorted({opt for opt in options if opt})


def _build_completer(modules: dict[str, Any], words: Iterable[str]) -> Any:
    completer_base = modules["Completer"]
    completion_cls = modules["Completion"]
    word_list = list(words)

    class _DynamicCompleter(completer_base):  # type: ignore[misc]
        def get_completions(self, document: Any, complete_event: Any) -> Iterable[Any]:
            before_cursor = document.text_before_cursor or ""
            word = before_cursor.split()[-1] if before_cursor.strip() else ""
            lower = word.lower()
            for option in word_list:
                if not lower or option.lower().startswith(lower):
                    yield completion_cls(option, start_position=-len(word))

    return _DynamicCompleter()


def _ensure_prompt_session(modules: dict[str, Any]) -> Any:
    global _PROMPT_SESSION, _PROMPT_HISTORY
    if _PROMPT_SESSION is None:
        history_cls = modules["History"]
        session_cls = modules["PromptSession"]
        _PROMPT_HISTORY = history_cls()
        _PROMPT_SESSION = session_cls(history=_PROMPT_HISTORY)
    return _PROMPT_SESSION


def _ensure_prompt_toolkit() -> dict[str, Any] | None:
    global _PROMPT_TOOLKIT_MODULES
    if _PROMPT_TOOLKIT_MODULES is _PROMPT_TOOLKIT_SENTINEL:
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.completion import Completer, Completion
            from prompt_toolkit.history import InMemoryHistory
        except ImportError:
            _PROMPT_TOOLKIT_MODULES = None
        else:
            _PROMPT_TOOLKIT_MODULES = {
                "PromptSession": PromptSession,
                "Completer": Completer,
                "Completion": Completion,
                "History": InMemoryHistory,
            }
    return _PROMPT_TOOLKIT_MODULES if isinstance(_PROMPT_TOOLKIT_MODULES, dict) else None


def _collect_agent_names() -> Iterable[str]:
    try:
        from ..agents.registry import AgentRegistry

        names = set(AgentRegistry.list_available())
        names.update(AgentRegistry.list_coalitions())
        return names
    except Exception:
        return []


@lru_cache(maxsize=1)
def _collect_command_options() -> Iterable[str]:
    try:
        from typer.main import get_command

        from .app import app

        click_app = get_command(app)
        options: set[str] = set()
        for command in click_app.commands.values():
            for param in getattr(command, "params", []):
                for opt in getattr(param, "opts", []):
                    options.add(opt)
        return options
    except Exception:
        return []
