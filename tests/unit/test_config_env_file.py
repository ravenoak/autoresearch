from pathlib import Path

from autoresearch.config.loader import ConfigLoader
from typing import Any

SPEC_PATH = Path(__file__).resolve().parents[2] / "docs/algorithms/config_utils.md"


def test_config_spec_exists() -> None:
    """Configuration specification document must exist."""
    assert SPEC_PATH.is_file()


def test_env_file_parsing(example_env_file: Any) -> None:
    """ConfigLoader should populate ConfigModel from .env file."""
    env_path = example_env_file
    env_path.write_text("loops=5\nstorage__rdf_path=env.db\n")
    loader = ConfigLoader.new_for_tests(env_path=env_path)
    cfg = loader.load_config()
    assert cfg.loops == 5
    assert cfg.storage.rdf_path == "env.db"
