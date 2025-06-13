"""Simple synthesis helpers for answer and rationale generation."""

from typing import List, Dict

from .logging_utils import get_logger

log = get_logger(__name__)


def build_answer(query: str, claims: List[Dict[str, str]]) -> str:
    """Create a concise answer incorporating provided claim content."""

    log.info("Generating answer")

    if not claims:
        return f"No answer found for '{query}'."

    summary = "; ".join(c.get("content", "") for c in claims[:3])
    if len(claims) > 3:
        summary += f" ... ({len(claims)} claims total)"

    return summary


def build_rationale(claims: List[Dict[str, str]]) -> str:
    """Summarize reasoning based on the provided claims."""

    if not claims:
        return "No rationale available."

    bullet_points = "\n".join(f"- {c.get('content', '')}" for c in claims)
    return f"The reasoning is based on:\n{bullet_points}"
