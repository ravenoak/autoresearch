"""Search subpackage.

See :mod:`docs.search_spec` for behaviour and test details. Algorithm
background for relevance ranking lives in
``docs/algorithms/bm25.md``, ``docs/algorithms/semantic_similarity.md``,
and ``docs/algorithms/source_credibility.md``. Convergence of the combined
score is analysed in ``docs/algorithms/relevance_ranking.md``.
"""

from ..config.loader import get_config
from .context import (
    BERTOPIC_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    SPACY_AVAILABLE,
    SearchContext,
    spacy,
)
from .core import Search, get_search
from .http import _http_session, close_http_session, get_http_session, set_http_session

__all__ = [
    "Search",
    "get_search",
    "SearchContext",
    "get_http_session",
    "set_http_session",
    "close_http_session",
    "_http_session",
    "get_config",
    "SPACY_AVAILABLE",
    "BERTOPIC_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    "spacy",
]
