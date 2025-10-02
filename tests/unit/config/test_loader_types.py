"""Tests for typed configuration loader helpers."""

from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from autoresearch.config.loader import ConfigLoader, LoadedConfigFile, load_config_file
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.errors import ConfigError


def test_load_config_file_returns_defaults_when_missing(tmp_path: Path) -> None:
    """No config file should return an empty payload."""

    missing = tmp_path / "missing.toml"
    result = load_config_file([missing])

    assert result == LoadedConfigFile(path=None, data={}, modified_time=None)


def test_load_config_file_rejects_non_mapping(tmp_path: Path) -> None:
    """A TOML file that parses to a non-mapping should raise a ConfigError."""

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n")

    with patch("autoresearch.config.loader.tomllib.load", return_value=["not", "a", "mapping"]):
        with pytest.raises(ConfigError, match="Invalid config file structure"):
            load_config_file([config_path])


def test_env_storage_override_round_trips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment overrides should flow through typed storage settings."""

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 2\n")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AUTORESEARCH_STORAGE__VECTOR_NPROBE", "5")

    loader = ConfigLoader.new_for_tests(search_paths=[config_path])
    try:
        config = loader.load_config()
    finally:
        ConfigLoader.reset_instance()

    assert config.storage.vector_nprobe == 5
    assert config.storage.ontology_reasoner == "owlrl"


def test_storage_defaults(tmp_path: Path) -> None:
    """Loading a minimal config should keep storage defaults intact."""

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n")

    loader = ConfigLoader.new_for_tests(search_paths=[config_path])
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            config = loader.load_config()
    finally:
        ConfigLoader.reset_instance()

    assert not caught
    assert config.storage.minimum_deterministic_resident_nodes == 2


def test_normalize_ranking_weights_balances_missing_values() -> None:
    """The ranking weights validator should balance unspecified weights."""

    config = SearchConfig(semantic_similarity_weight=0.7)

    assert pytest.approx(config.semantic_similarity_weight) == 0.7
    remaining = 1.0 - config.semantic_similarity_weight
    assert pytest.approx(config.bm25_weight + config.source_credibility_weight) == remaining
    assert config.bm25_weight > 0.0
    assert config.source_credibility_weight > 0.0


def test_config_model_deep_copy_preserves_storage_settings() -> None:
    """Deep copies should keep storage settings equal but independent."""

    config = ConfigModel()
    config.storage.rdf_backend = "duckdb"
    config.storage.rdf_path = "custom"
    original_storage = config.model_dump(mode="python")["storage"]

    cloned = config.model_copy(deep=True)
    cloned_storage = cloned.model_dump(mode="python")["storage"]

    assert cloned.storage is not config.storage
    assert cloned_storage == original_storage
    assert cloned_storage is not original_storage

    cloned.storage.rdf_backend = "memory"

    assert config.storage.rdf_backend == "duckdb"
