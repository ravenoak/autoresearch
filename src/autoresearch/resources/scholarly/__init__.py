"""Scholarly resource integration for Autoresearch."""

from .cache import ScholarlyCache, CacheValidationError
from .fetchers import ArxivFetcher, HuggingFacePapersFetcher, ScholarlyFetcher
from .models import CachedPaper, PaperDocument, PaperMetadata, PaperProvenance
from .service import ScholarlyService, SearchResult

__all__ = [
    "ScholarlyCache",
    "CacheValidationError",
    "ArxivFetcher",
    "HuggingFacePapersFetcher",
    "ScholarlyFetcher",
    "CachedPaper",
    "PaperDocument",
    "PaperMetadata",
    "PaperProvenance",
    "ScholarlyService",
    "SearchResult",
]
