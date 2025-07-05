"""Token counting utilities for LLM adapters.

This module provides tools for tracking and measuring token usage in LLM interactions.
It includes:
- TokenCountingAdapter: A wrapper for LLM adapters that counts tokens
- count_tokens: A context manager for token counting
- with_token_counting: A decorator for functions that use LLM adapters
- compress_prompt: Utility to truncate prompts to a token budget

These utilities help monitor resource usage and costs when interacting with LLMs.
"""

from typing import (
    Dict,
    Any,
    Optional,
    Protocol,
    Iterator,
    Tuple,
    Callable,
    TypeVar,
)
from contextlib import contextmanager
import functools

from ..orchestration.metrics import OrchestrationMetrics


def compress_prompt(
    prompt: str,
    token_budget: int,
    summarizer: Optional[Callable[[str, int], str]] = None,
) -> str:
    """Compress ``prompt`` so it stays within ``token_budget`` tokens.

    The implementation keeps the beginning and end of the prompt and
    truncates the middle when necessary. Tokens are approximated using
    simple whitespace splitting to avoid external dependencies.

    Args:
        prompt: The original prompt text.
        token_budget: Maximum number of tokens to keep.

    Returns:
        The compressed prompt text. If the prompt fits within the
        budget it is returned unchanged. When truncated an ellipsis is
        inserted to indicate removed content.
    """

    tokens = prompt.split()
    if len(tokens) <= token_budget:
        return prompt

    if summarizer is not None:
        summary = summarizer(prompt, token_budget)
        if len(summary.split()) <= token_budget:
            return summary

    half = max(1, (token_budget - 1) // 2)
    return " ".join(tokens[:half] + ["..."] + tokens[-half:])


def prune_context(context: list[str], token_budget: int) -> list[str]:
    """Prune a list of context strings to fit within ``token_budget`` tokens.

    Older items are removed first until the remaining context totals at
    most ``token_budget`` tokens.

    Args:
        context: Ordered list of context strings (oldest first).
        token_budget: Maximum total tokens allowed.

    Returns:
        The pruned context list.
    """

    pruned = list(context)
    token_count = sum(len(c.split()) for c in pruned)

    while pruned and token_count > token_budget:
        removed = pruned.pop(0)
        token_count -= len(removed.split())

    return pruned


class LLMAdapter(Protocol):
    """Protocol defining the interface for LLM adapters."""

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        """Generate text from a prompt."""
        ...


class TokenCountingAdapter:
    """Wrapper for LLM adapters that counts tokens without modifying the original adapter."""

    def __init__(
        self,
        adapter: LLMAdapter,
        agent_name: str,
        metrics: OrchestrationMetrics,
        token_budget: Optional[int] = None,
        summarizer: Optional[Callable[[str, int], str]] = None,
    ):
        """Initialize the token counting adapter.

        Args:
            adapter: The LLM adapter to wrap
            agent_name: The name of the agent using this adapter
            metrics: The metrics collector to record token usage
            summarizer: Optional function used to summarize prompts when they
                exceed ``token_budget``
        """
        self.adapter = adapter
        self.agent_name = agent_name
        self.metrics = metrics
        self.token_counter = {"in": 0, "out": 0}
        self.token_budget = token_budget
        self.summarizer = summarizer

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        """Generate text from a prompt and count tokens.

        Args:
            prompt: The prompt to generate from
            model: Optional model override
            **kwargs: Additional arguments to pass to the generate method

        Returns:
            The generated text
        """
        if self.token_budget is not None:
            prompt = compress_prompt(
                prompt, self.token_budget, summarizer=self.summarizer
            )
        result = self.adapter.generate(prompt, model=model, **kwargs)
        self.token_counter["in"] += len(prompt.split())
        self.token_counter["out"] += len(str(result).split())
        return result

    def record_usage(self) -> None:
        """Record token usage to metrics."""
        self.metrics.record_tokens(
            self.agent_name,
            self.token_counter["in"],
            self.token_counter["out"],
        )


@contextmanager
def count_tokens(
    agent_name: str,
    adapter: LLMAdapter,
    metrics: OrchestrationMetrics,
    token_budget: Optional[int] = None,
    summarizer: Optional[Callable[[str, int], str]] = None,
) -> Iterator[Tuple[Dict[str, int], "TokenCountingAdapter"]]:
    """Context manager for counting tokens.

    Args:
        agent_name: The name of the agent
        adapter: The LLM adapter to count tokens for
        metrics: The metrics collector to record token usage
        token_budget: Optional token budget to apply to prompts
        summarizer: Optional function used to summarize prompts when they
            exceed ``token_budget``

    Yields:
        A dictionary with token counts and the wrapped adapter
    """
    token_counter = TokenCountingAdapter(
        adapter,
        agent_name,
        metrics,
        token_budget,
        summarizer,
    )
    try:
        yield token_counter.token_counter, token_counter
    finally:
        token_counter.record_usage()


T = TypeVar("T")


def with_token_counting(
    agent_name: str,
    metrics: OrchestrationMetrics,
    token_budget: Optional[int] = None,
    summarizer: Optional[Callable[[str, int], str]] = None,
) -> Callable[[Callable[[LLMAdapter, Any], T]], Callable[[LLMAdapter, Any], T]]:
    """Decorator for functions that use LLM adapters to count tokens.

    Args:
        agent_name: The name of the agent
        metrics: The metrics collector to record token usage
        token_budget: Optional token budget to apply to prompts
        summarizer: Optional function used to summarize prompts when they
            exceed ``token_budget``

    Returns:
        A decorator function
    """

    def decorator(
        func: Callable[[LLMAdapter, Any], T],
    ) -> Callable[[LLMAdapter, Any], T]:
        @functools.wraps(func)
        def wrapper(adapter: LLMAdapter, *args: Any, **kwargs: Any) -> T:
            with count_tokens(
                agent_name, adapter, metrics, token_budget, summarizer
            ) as (
                token_counter,
                counting_adapter,
            ):
                return func(counting_adapter, *args, **kwargs)

        return wrapper

    return decorator
