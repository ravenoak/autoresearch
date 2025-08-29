import json
from io import StringIO

from loguru import logger as loguru_logger

from autoresearch.logging_utils import configure_logging, get_logger


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
