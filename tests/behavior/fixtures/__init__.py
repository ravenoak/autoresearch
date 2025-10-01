from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from tests.typing_helpers import TypedFixture


@pytest.fixture
def bdd_context() -> TypedFixture[dict[str, Any]]:
    """Mutable mapping for sharing data between BDD steps."""
    ctx: dict[str, Any] = {}
    yield ctx
    broker = ctx.get("broker")
    if broker and hasattr(broker, "shutdown"):
        broker.shutdown()
    return None


@pytest.fixture
def cli_runner() -> TypedFixture[CliRunner]:
    """Provide a Typer CLI runner for behavior scenarios."""
    return CliRunner()
