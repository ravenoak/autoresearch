import json
import logging
from dataclasses import dataclass
from io import StringIO

from loguru import logger as loguru_logger
from pytest import MonkeyPatch

from autoresearch.logging_utils import (
    InterceptHandler,
    configure_logging,
    get_logger,
)


@dataclass
class DummyStream:
    """Mimic the subset of a Loguru stream used by the handler."""

    closed: bool = True


@dataclass
class DummySink:
    """Wrapper exposing ``_stream`` attribute."""

    _stream: DummyStream


@dataclass
class DummyHandler:
    """Handler entry stored in the Loguru core mapping."""

    _sink: DummySink


@dataclass
class DummyCore:
    """Subset of the Loguru core needed for the test."""

    handlers: dict[int, DummyHandler]


def test_get_logger() -> None:
    configure_logging()
    log = get_logger("test")
    assert hasattr(log, "info")
    log.info("message")


def test_structured_output_and_redaction() -> None:
    configure_logging()
    buffer = StringIO()
    loguru_logger.remove()
    loguru_logger.add(buffer, serialize=True)
    log = get_logger("unit")
    secret = "secret-token"
    log.info("login", user="bob", token="[REDACTED]")
    buffer.seek(0)
    record = json.loads(buffer.getvalue())
    payload = json.loads(record["text"].split(" - ", 1)[1])
    assert payload["token"] == "[REDACTED]"
    assert secret not in record["text"]


def test_intercept_handler_handles_closed_stream(monkeypatch: MonkeyPatch) -> None:
    handler = InterceptHandler()
    dummy_core = DummyCore(handlers={1: DummyHandler(_sink=DummySink(_stream=DummyStream()))})
    monkeypatch.setattr(loguru_logger, "_core", dummy_core)
    record = logging.LogRecord(
        name="unit",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="message",
        args=(),
        exc_info=None,
    )

    handler.emit(record)
