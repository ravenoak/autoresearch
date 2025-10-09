"""Search subpackage.

See :mod:`docs.search_spec` for behaviour and test details. Algorithm
background for relevance ranking lives in
``docs/algorithms/bm25.md``, ``docs/algorithms/semantic_similarity.md``,
and ``docs/algorithms/source_credibility.md``. Convergence of the combined
score is analysed in ``docs/algorithms/relevance_ranking.md``.
"""

from ..cache import SearchCache, get_cache
from ..config.loader import get_config
from ..storage import StorageManager
from .context import (
    BERTOPIC_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    SPACY_AVAILABLE,
    SearchContext,
    spacy,
)
from .core import ExternalLookupResult, Search, get_search
from .http import _http_session, close_http_session, get_http_session, set_http_session

# Expose the ``core`` module for tests that patch internals via
# ``autoresearch.search.core``. Without this explicit import, the module is not
# registered as an attribute of the package which leads to ``AttributeError``
# during monkeypatch resolution in integration tests.
from . import context, core, storage  # noqa: F401  (re-exported for test accessibility)

__all__ = [
    "ExternalLookupResult",
    "Search",
    "get_search",
    "SearchContext",
    "get_http_session",
    "set_http_session",
    "close_http_session",
    "_http_session",
    "SearchCache",
    "get_cache",
    "get_config",
    "StorageManager",
    "context",
    "storage",
    "SPACY_AVAILABLE",
    "BERTOPIC_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    "spacy",
    "core",
]
