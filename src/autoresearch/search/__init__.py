"""Search subpackage."""

from .core import Search
from .context import (
    SearchContext,
    SPACY_AVAILABLE,
    BERTOPIC_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    spacy,
)
from .http import get_http_session, set_http_session, close_http_session, _http_session
from ..config import get_config

__all__ = [
    "Search",
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
