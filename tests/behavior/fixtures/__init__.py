from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tests.behavior.context import BehaviorContext
from tests.typing_helpers import TypedFixture


@pytest.fixture
def bdd_context() -> TypedFixture[BehaviorContext]:
    """Mutable mapping for sharing data between BDD steps."""
    ctx: BehaviorContext = {}
    yield ctx
    broker = ctx.get("broker")
    if broker and hasattr(broker, "shutdown"):
        broker.shutdown()
    return None


@pytest.fixture
def cli_runner() -> TypedFixture[CliRunner]:
    """Provide a Typer CLI runner for behavior scenarios."""
    return CliRunner()
