import json
import pytest

from autoresearch.error_utils import (
    ErrorInfo,
    ErrorSeverity,
    format_error_for_cli,
    format_error_for_gui,
    format_error_for_api,
    format_error_for_a2a,
    get_error_info,
)
from autoresearch.errors import ConfigError, LLMError, TimeoutError
from typing import Any


def test_error_info_to_dict_and_str() -> None:
    info = ErrorInfo(
        "msg",
        severity=ErrorSeverity.WARNING,
        suggestions=["hint"],
        code_examples=["cmd"],
        context={"k": "v"},
    )
    d = info.to_dict()
    assert d["message"] == "msg"
    assert d["severity"] == ErrorSeverity.WARNING
    s = str(info)
    assert "WARNING" in s and "msg" in s


def test_formatters() -> None:
    info = ErrorInfo(
        "oops",
        severity=ErrorSeverity.ERROR,
        suggestions=["do"],
        code_examples=["cmd"],
    )
    cli = format_error_for_cli(info)
    assert cli == ("oops", "do", "cmd")
    gui = format_error_for_gui(info)
    assert "• do" in gui
    api = format_error_for_api(info)
    assert api["error"] == "oops"
    a2a = format_error_for_a2a(info)
    assert a2a["status"] == "error"


def test_timeout_sets_warning() -> None:
    exc = TimeoutError("late", timeout=3)
    info = get_error_info(exc)
    assert info.severity == ErrorSeverity.WARNING


def test_redacted_context_preserved() -> None:
    exc = LLMError("bad key", api_key="[REDACTED]")
    info = get_error_info(exc)
    assert info.context["api_key"] == "[REDACTED]"


@pytest.mark.parametrize(
    "exc, substr",
    [
        (ConfigError("bad"), "Check your configuration file"),
        (LLMError("api_key missing", model="gpt"), "API key"),
        (TimeoutError("t", timeout=5), "5"),
    ],
)
def test_get_error_info(exc: Any, substr: Any) -> None:
    info = get_error_info(exc)
    joined = json.dumps(info.to_dict())
    assert substr.lower() in joined.lower()
