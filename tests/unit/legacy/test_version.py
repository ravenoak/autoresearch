# mypy: ignore-errors
import importlib.metadata
import tomllib
from pathlib import Path

import autoresearch


ROOT = Path(__file__).resolve().parents[3]


def test_init_version_matches_pyproject():
    pyproject = ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    assert autoresearch.__version__ == data["project"]["version"]


def test_release_date_matches_pyproject():
    pyproject = ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    release_date = data["tool"]["autoresearch"]["release_date"]

    # Handle both string and None values for release_date
    if autoresearch.__release_date__ is None:
        assert release_date == "unreleased"
    else:
        assert autoresearch.__release_date__ == release_date


def test_init_version_matches_metadata():
    assert autoresearch.__version__ == importlib.metadata.version("autoresearch")
