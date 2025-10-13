"""Intelligent prompt chunking for large context handling.

This module provides semantic-aware chunking strategies for breaking large prompts
into manageable segments while preserving meaning and context flow.
"""

from __future__ import annotations

import re
import logging
from typing import List, Tuple, Optional, Callable, Protocol

logger = logging.getLogger(__name__)


class Tokenizer(Protocol):
    """Protocol for token counting implementations."""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        ...


def chunk_prompt(
    prompt: str,
    max_tokens: int,
    overlap: int = 100,
    tokenizer: Optional[Tokenizer] = None,
) -> List[Tuple[str, int, int]]:
    """Chunk prompt into segments preserving semantic boundaries.

    Args:
        prompt: The prompt text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Token overlap between chunks
        tokenizer: Optional tokenizer for accurate counting

    Returns:
        List of (chunk_text, start_token, end_token) tuples
    """
    if not prompt.strip():
        return []

    # Try to split on semantic boundaries first
    # Priority: 1) Sections (##, ###), 2) Paragraphs, 3) Sentences

    # First try section headers
    sections = re.split(r'\n(#{1,3}\s+.+)\n', prompt)
    if len(sections) > 1:
        return _chunk_by_delimiter(sections, max_tokens, overlap, tokenizer)

    # Try paragraphs
    paragraphs = prompt.split('\n\n')
    if len(paragraphs) > 1:
        return _chunk_by_delimiter(paragraphs, max_tokens, overlap, tokenizer)

    # Fall back to sentences
    sentences = re.split(r'([.!?]+\s+)', prompt)
    return _chunk_by_delimiter(sentences, max_tokens, overlap, tokenizer)


def _chunk_by_delimiter(
    parts: List[str],
    max_tokens: int,
    overlap: int,
    tokenizer: Optional[Tokenizer],
) -> List[Tuple[str, int, int]]:
    """Group parts into chunks under max_tokens with overlap.

    Args:
        parts: List of text parts (sentences, paragraphs, etc.)
        max_tokens: Maximum tokens per chunk
        overlap: Token overlap between chunks
        tokenizer: Optional tokenizer for accurate counting

    Returns:
        List of (chunk_text, start_token, end_token) tuples
    """
    chunks = []
    current_chunk = []
    current_tokens = 0
    start_token = 0

    def get_token_count(text: str) -> int:
        """Get token count for text using provided tokenizer or approximation."""
        if tokenizer:
            return tokenizer.count_tokens(text)
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4

    for part in parts:
        part = part.strip()
        if not part:
            continue

        part_tokens = get_token_count(part)

        if current_tokens + part_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunk_text = ''.join(current_chunk)
            end_token = start_token + get_token_count(chunk_text)
            chunks.append((chunk_text, start_token, end_token))

            # Start new chunk with overlap
            overlap_parts = current_chunk[-(overlap // len(current_chunk)):]
            current_chunk = overlap_parts + [part]
            start_token = start_token + current_tokens - get_token_count(''.join(overlap_parts))
            current_tokens = get_token_count(''.join(current_chunk))
        else:
            current_chunk.append(part)
            current_tokens += part_tokens

    # Add final chunk
    if current_chunk:
        chunk_text = ''.join(current_chunk)
        end_token = start_token + get_token_count(chunk_text)
        chunks.append((chunk_text, start_token, end_token))

    return chunks


def synthesize_chunk_results(
    results: List[str],
    query: str,
    adapter: Any,  # LLMAdapter type would create circular import
    model: str,
) -> str:
    """Synthesize results from multiple chunks into coherent response.

    Args:
        results: List of results from individual chunks
        query: Original query for context
        adapter: LLM adapter for synthesis generation
        model: Model name for synthesis

    Returns:
        Synthesized response combining all chunk results
    """
    if len(results) == 1:
        return results[0]

    # Create synthesis prompt
    synthesis_prompt = f"""Given these partial responses to the query "{query}":

{chr(10).join(f"Part {i+1}: {result}" for i, result in enumerate(results))}

Synthesize a coherent, comprehensive response that integrates all parts while maintaining logical flow and avoiding redundancy."""

    try:
        return adapter.generate(synthesis_prompt, model=model)
    except Exception as e:
        logger.warning(f"Failed to synthesize chunk results: {e}")
        # Fall back to simple concatenation
        return "\n\n".join(results)


def estimate_chunking_overhead(
    prompt: str,
    max_tokens: int,
    overlap: int = 100,
) -> float:
    """Estimate the overhead introduced by chunking.

    Args:
        prompt: Original prompt
        max_tokens: Maximum tokens per chunk
        overlap: Token overlap between chunks

    Returns:
        Estimated overhead factor (1.0 = no overhead, >1.0 = overhead)
    """
    if not prompt.strip():
        return 1.0

    # Count tokens in original prompt (approximation)
    original_tokens = len(prompt) // 4

    if original_tokens <= max_tokens:
        return 1.0

    # Calculate number of chunks needed
    chunks = chunk_prompt(prompt, max_tokens, overlap)
    total_chunk_tokens = sum(end - start for _, start, end in chunks)

    # Estimate synthesis tokens (roughly 20% of total)
    synthesis_tokens = total_chunk_tokens * 0.2

    total_tokens = total_chunk_tokens + synthesis_tokens
    overhead = total_tokens / original_tokens if original_tokens > 0 else 1.0

    return min(overhead, 3.0)  # Cap at 3x overhead
