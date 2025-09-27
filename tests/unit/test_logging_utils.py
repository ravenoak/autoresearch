import json
import logging
from io import StringIO
from types import SimpleNamespace

from loguru import logger as loguru_logger

from autoresearch.logging_utils import (
    InterceptHandler,
    configure_logging,
    get_logger,
)


def test_get_logger():
    configure_logging()
    log = get_logger("test")
    assert hasattr(log, "info")
    log.info("message")


def test_structured_output_and_redaction():
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


def test_intercept_handler_handles_closed_stream(monkeypatch):
    handler = InterceptHandler()

    class DummyHandler:
        _sink = SimpleNamespace(_stream=SimpleNamespace(closed=True))

    class DummyCore:
        handlers = {1: DummyHandler()}

    monkeypatch.setattr(loguru_logger, "_core", DummyCore())
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
