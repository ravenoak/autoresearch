import tomllib
from pathlib import Path
import autoresearch


def test_init_version_matches_pyproject():
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    assert autoresearch.__version__ == data["project"]["version"]
