import pytest
from typer.testing import CliRunner


@pytest.fixture
def bdd_context() -> dict:
    """Mutable mapping for sharing data between BDD steps."""
    return {}


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI runner for behavior scenarios."""
    return CliRunner()
