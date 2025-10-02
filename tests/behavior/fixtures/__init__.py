from __future__ import annotations

from collections.abc import Generator

import pytest
from typer.testing import CliRunner

from tests.behavior.context import BehaviorContext


@pytest.fixture
def bdd_context() -> Generator[BehaviorContext, None, None]:
    """Mutable mapping for sharing data between BDD steps."""
    ctx: BehaviorContext = {}
    yield ctx
    broker = ctx.get("broker")
    if broker and hasattr(broker, "shutdown"):
        broker.shutdown()
    return None


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI runner for behavior scenarios."""
    return CliRunner()
