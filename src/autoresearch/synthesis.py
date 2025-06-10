"""Simple synthesis helpers for answer and rationale generation."""
from typing import List, Dict

from .logging_utils import get_logger

log = get_logger(__name__)


def build_answer(query: str, claims: List[Dict[str, str]]) -> str:
    """Create a brief answer given a query and supporting claims."""
    log.info("Generating answer")
    return f"Answer for '{query}' using {len(claims)} claims."


def build_rationale(claims: List[Dict[str, str]]) -> str:
    """Summarize reasoning based on the provided claims."""
    return f"Rationale derived from {len(claims)} claims."

