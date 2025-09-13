import pytest
from typer.testing import CliRunner


@pytest.fixture
def bdd_context() -> dict:
    """Mutable mapping for sharing data between BDD steps."""
    ctx: dict = {}
    yield ctx
    broker = ctx.get("broker")
    if broker and hasattr(broker, "shutdown"):
        broker.shutdown()


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI runner for behavior scenarios."""
    return CliRunner()
