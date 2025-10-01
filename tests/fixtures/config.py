from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.typing_helpers import TypedFixture

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel


@dataclass
class ConfigContext:
    """Bundle configuration and sample data for complex test scenarios."""

    loader: ConfigLoader
    config: ConfigModel
    data_dir: Path


@pytest.fixture()
def config_loader(tmp_path: Path) -> TypedFixture[ConfigLoader]:
    """Provide a ConfigLoader instance backed by a minimal config file."""
    (tmp_path / "autoresearch.toml").write_text("[core]\n")
    loader = ConfigLoader.new_for_tests()
    loader._update_watch_paths()
    try:
        yield loader
    finally:
        ConfigLoader.reset_instance()
    return None


@pytest.fixture()
def config(config_loader: ConfigLoader, monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    """Return the ConfigModel loaded from the test configuration.

    The fixture ensures search ranking weights are explicitly set so that
    downstream tests always operate with a complete, valid configuration.
    Additionally, required environment variables are provided so tests do not
    depend on external configuration.
    """
    # Provide required environment variables for search backends.
    monkeypatch.setenv("SERPER_API_KEY", "test_key")

    cfg = config_loader.load_config()
    # Ensure relevance ranking weights sum to 1.0
    cfg.search.semantic_similarity_weight = 0.5
    cfg.search.bm25_weight = 0.3
    cfg.search.source_credibility_weight = 0.2
    return cfg


SAMPLE_CONFIG = """
[core]
llm_backend = "openai"
loops = 2
agents = ["Synthesizer", "Contrarian"]

[search]
semantic_similarity_weight = 0.5
bm25_weight = 0.3
source_credibility_weight = 0.2

[storage]
duckdb_path = "{duckdb_path}"
rdf_path = "{rdf_path}"

[profiles.offline]
llm_backend = "lmstudio"

[profiles.online]
llm_backend = "openai"
"""


@pytest.fixture()
def config_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TypedFixture[ConfigContext]:
    """Return a ConfigContext with representative config and data samples.

    The context writes a realistic configuration file and creates placeholder
    storage artefacts. Tests can extend this context or compose it with other
    fixtures to build complex scenarios.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "kg.duckdb").touch()
    (data_dir / "rdf_store").mkdir()

    cfg_text = SAMPLE_CONFIG.format(
        duckdb_path=(data_dir / "kg.duckdb").as_posix(),
        rdf_path=(data_dir / "rdf_store").as_posix(),
    )
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(cfg_text)

    loader = ConfigLoader.new_for_tests()
    loader.search_paths = [cfg_path]
    loader._update_watch_paths()

    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    config = loader.load_config()
    try:
        yield ConfigContext(loader=loader, config=config, data_dir=data_dir)
    finally:
        ConfigLoader.reset_instance()
    return None
