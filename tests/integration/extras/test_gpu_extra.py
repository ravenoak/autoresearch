"""Tests for the GPU optional extra."""

from __future__ import annotations

import pytest

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search.context import _try_import_bertopic


@pytest.mark.requires_gpu
def test_bertopic_import() -> None:
    """The GPU extra exposes BERTopic for topic modeling."""
    cfg = get_config()
    cfg.search.context_aware.enabled = True
    with temporary_config(cfg):
        if not _try_import_bertopic():
            pytest.skip("BERTopic import failed")
