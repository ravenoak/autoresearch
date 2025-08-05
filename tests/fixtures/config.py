from __future__ import annotations

import pytest

from autoresearch.config.loader import ConfigLoader


@pytest.fixture()
def config_loader(tmp_path) -> ConfigLoader:
    """Provide a ConfigLoader instance backed by a minimal config file."""
    (tmp_path / "autoresearch.toml").write_text("[core]\n")
    loader = ConfigLoader.new_for_tests()
    loader._update_watch_paths()
    return loader


@pytest.fixture()
def config(config_loader: ConfigLoader, monkeypatch: pytest.MonkeyPatch):
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
