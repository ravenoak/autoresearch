from __future__ import annotations

import pytest

from autoresearch.config.loader import ConfigLoader


@pytest.fixture()
def config_loader() -> ConfigLoader:
    """Provide a ConfigLoader instance for tests.

    The loader uses its built-in defaults and does not rely on an external
    ``autoresearch.toml`` file. This keeps unit tests self-contained and makes
    configuration behaviour consistent regardless of the working directory.
    """
    loader = ConfigLoader.new_for_tests()
    # Ensure watch paths reflect the default search paths
    loader._update_watch_paths()
    return loader


@pytest.fixture()
def config(config_loader: ConfigLoader):
    """Return the ConfigModel loaded from the test configuration.

    The fixture ensures search ranking weights are explicitly set so that
    downstream tests always operate with a complete, valid configuration.
    """
    cfg = config_loader.load_config()
    cfg.search.semantic_similarity_weight = 0.5
    cfg.search.bm25_weight = 0.3
    cfg.search.source_credibility_weight = 0.2
    return cfg
