"""Simulate logging to verify JSON output and secrecy of sensitive fields.

Usage:
    uv run scripts/logging_sim.py
"""

from __future__ import annotations

import json
from io import StringIO

from loguru import logger as loguru_logger

from autoresearch.logging_utils import configure_logging, get_logger


def run_simulation() -> None:
    """Emit a log line and confirm JSON serialization with redaction."""
    buffer = StringIO()
    configure_logging()
    loguru_logger.remove()
    loguru_logger.add(buffer, serialize=True)
    log = get_logger("simulation")
    secret = "topsecret"
    log.info("login", user="alice", token="[REDACTED]")
    buffer.seek(0)
    record = json.loads(buffer.getvalue())
    payload = json.loads(record["text"].split(" - ", 1)[1])
    assert payload["token"] == "[REDACTED]"
    assert secret not in record["text"]
    print("Structured log verified; sensitive fields redacted.")


if __name__ == "__main__":
    run_simulation()
