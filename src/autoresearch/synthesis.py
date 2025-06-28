"""Simple synthesis helpers for answer and rationale generation.

This module provides utility functions for generating concise answers and
rationales based on claims extracted from various sources. These functions
are used by the orchestration system to format the final output for users.
"""

from typing import List, Dict

from .logging_utils import get_logger

log = get_logger(__name__)


def build_answer(query: str, claims: List[Dict[str, str]]) -> str:
    """Create a concise answer incorporating provided claim content.

    This function generates a concise answer by combining the content of
    the top claims. It limits the output to the first 3 claims to keep
    the answer concise, but indicates the total number of claims if more
    than 3 are provided.

    Args:
        query: The original user query
        claims: A list of claim dictionaries, each containing at least a 'content' key
               with the claim text. Claims should be ordered by relevance or importance.

    Returns:
        A formatted answer string incorporating the claim content, or a message
        indicating no answer was found if the claims list is empty.
    """
    log.info("Generating answer")

    if not claims:
        return f"No answer found for '{query}'."

    summary = "; ".join(c.get("content", "") for c in claims[:3])
    if len(claims) > 3:
        summary += f" ... ({len(claims)} claims total)"

    return summary


def build_rationale(claims: List[Dict[str, str]]) -> str:
    """Summarize reasoning based on the provided claims.

    This function generates a rationale by listing all claims as bullet points.
    Unlike build_answer, this function includes all claims to provide a complete
    picture of the reasoning process.

    Args:
        claims: A list of claim dictionaries, each containing at least a 'content' key
               with the claim text.

    Returns:
        A formatted rationale string with all claims as bullet points, or a message
        indicating no rationale is available if the claims list is empty.
    """
    if not claims:
        return "No rationale available."

    bullet_points = "\n".join(f"- {c.get('content', '')}" for c in claims)
    return f"The reasoning is based on:\n{bullet_points}"


def compress_prompt(prompt: str, token_budget: int) -> str:
    """Compress a prompt so it does not exceed the token budget.

    The algorithm keeps the beginning and end of the prompt while
    truncating the middle when necessary. Tokens are approximated by
    whitespace splitting to avoid heavy dependencies.

    Args:
        prompt: The original prompt text.
        token_budget: Maximum allowed tokens.

    Returns:
        The compressed prompt string.
    """

    tokens = prompt.split()
    if len(tokens) <= token_budget:
        return prompt

    half = max(1, token_budget // 2)
    return " ".join(tokens[:half] + ["..."] + tokens[-half:])


def compress_claims(claims: List[Dict[str, str]], token_budget: int) -> List[Dict[str, str]]:
    """Trim claim list so total tokens stay within ``token_budget``.

    Claims are kept in order and truncated when the remaining budget is
    insufficient. The final claim may be shortened with an ellipsis if
    required.

    Args:
        claims: Claims with ``content`` fields.
        token_budget: Maximum total tokens to retain.

    Returns:
        A list of claims respecting the budget.
    """

    compressed: List[Dict[str, str]] = []
    tokens_used = 0
    for claim in claims:
        text = claim.get("content", "")
        tokens = text.split()
        if tokens_used + len(tokens) <= token_budget:
            compressed.append(claim)
            tokens_used += len(tokens)
            continue

        remaining = token_budget - tokens_used
        if remaining <= 0:
            break
        truncated = " ".join(tokens[:remaining]) + "..."
        new_claim = {**claim, "content": truncated}
        compressed.append(new_claim)
        break

    return compressed
