# mypy: ignore-errors
from pathlib import Path

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig, StorageConfig
from autoresearch.errors import ConfigError

SPEC_PATH = Path(__file__).resolve().parents[3] / "docs/algorithms/config_utils.md"


def test_config_spec_exists() -> None:
    """Configuration specification document must exist."""
    assert SPEC_PATH.is_file()


def test_invalid_rdf_backend():
    """Invalid RDF backend should raise ConfigError."""
    with pytest.raises(ConfigError):
        ConfigModel(storage=StorageConfig(rdf_backend="bad"))


def test_weights_must_sum_to_one():
    """Relevance ranking weights that do not sum to one raise ConfigError."""
    with pytest.raises(ConfigError):
        ConfigModel(
            search=SearchConfig(
                semantic_similarity_weight=0.5,
                bm25_weight=0.5,
                source_credibility_weight=0.5,
            )
        )
    with pytest.raises(ConfigError):
        ConfigModel(
            search=SearchConfig(
                semantic_similarity_weight=0.8,
                bm25_weight=0.3,
            )
        )


def test_default_config_loads_without_error():
    """Default ConfigModel should load without raising ConfigError."""
    loader = ConfigLoader.new_for_tests()
    loader._update_watch_paths()
    try:
        loader.load_config()
    except ConfigError as exc:  # pragma: no cover - should not happen
        pytest.fail(f"ConfigModel failed to load: {exc}")
