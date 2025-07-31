import pytest

from autoresearch.config.models import ConfigModel, StorageConfig, SearchConfig
from autoresearch.errors import ConfigError


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
