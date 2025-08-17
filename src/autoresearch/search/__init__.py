"""Search subpackage."""

from ..config.loader import get_config
from .context import (
    BERTOPIC_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    SPACY_AVAILABLE,
    SearchContext,
    spacy,
)
from .core import Search, SearchInstance, get_search
from .http import _http_session, close_http_session, get_http_session, set_http_session

__all__ = [
    "Search",
    "SearchInstance",
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
