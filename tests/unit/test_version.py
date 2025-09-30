import importlib.metadata
import tomllib
from pathlib import Path

import autoresearch


def test_init_version_matches_pyproject() -> None:
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    assert autoresearch.__version__ == data["project"]["version"]


def test_release_date_matches_pyproject() -> None:
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    release_date = data["tool"]["autoresearch"]["release_date"]
    assert autoresearch.__release_date__ == release_date


def test_init_version_matches_metadata() -> None:
    assert autoresearch.__version__ == importlib.metadata.version("autoresearch")
