from __future__ import annotations

import pytest

from autoresearch.config.loader import ConfigLoader


def test_invalid_env_falls_back_to_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid environment values should not raise and use defaults instead."""
    monkeypatch.setenv("STORAGE__HNSW_EF_SEARCH", "bad")

    loader = ConfigLoader.new_for_tests()
    cfg = loader.load_config()

    assert cfg.storage.hnsw_ef_search == 10
