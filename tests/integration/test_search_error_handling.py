from __future__ import annotations

from typing import Mapping, Sequence

import pytest
import requests

from autoresearch.config.models import ConfigModel
from autoresearch.errors import TimeoutError
from autoresearch.search import Search


def test_external_lookup_timeout_integration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify timeout exceptions propagate through integration layer."""

    def timeout_backend(query: str, max_results: int = 5) -> Sequence[Mapping[str, object]]:
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setitem(Search.backends, "timeout", timeout_backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["timeout"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    with pytest.raises(TimeoutError):
        Search.external_lookup("q")
