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
    Union,
)
from contextlib import contextmanager
import functools
import logging

from ..orchestration.metrics import OrchestrationMetrics

logger = logging.getLogger(__name__)

# Lazy import for tiktoken to avoid hard dependency
_tiktoken: Any = None

def _get_tiktoken() -> Any:
    """Lazy load tiktoken if available."""
    global _tiktoken
    if _tiktoken is None:
        try:
            import tiktoken
            _tiktoken = tiktoken
        except ImportError:
            logger.debug("tiktoken not available, using approximation")
            _tiktoken = False
    return _tiktoken if _tiktoken else None


def compress_prompt(
    prompt: str,
    token_budget: int,
    summarizer: Optional[Callable[[str, int], str]] = None,
    model: str = "unknown",
    provider: str = "lmstudio",
) -> str:
    """Compress ``prompt`` so it stays within ``token_budget`` tokens.

    The implementation keeps the beginning and end of the prompt and
    truncates the middle when necessary. Uses accurate token counting
    when available, falls back to approximation.

    Args:
        prompt: The original prompt text.
        token_budget: Maximum number of tokens to keep.
        summarizer: Optional summarizer function for compression.
        model: Model name for accurate token counting.
        provider: Provider name for accurate token counting.

    Returns:
        The compressed prompt text. If the prompt fits within the
        budget it is returned unchanged. When truncated an ellipsis is
        inserted to indicate removed content.
    """
    try:
        # Try accurate token counting first
        tokenizer = get_tokenizer(model, provider)
        token_count = tokenizer.count_tokens(prompt)

        if token_count <= token_budget:
            return prompt

        # Try summarizer if available
        if summarizer is not None:
            summary = summarizer(prompt, token_budget)
            summary_tokens = tokenizer.count_tokens(summary)
            if summary_tokens <= token_budget:
                return summary

    except Exception as e:
        logger.debug(f"Accurate token counting failed, using approximation: {e}")
        # Fall back to approximation
        tokens = prompt.split()
        if len(tokens) <= token_budget:
            return prompt

        if summarizer is not None:
            summary = summarizer(prompt, token_budget)
            if len(summary.split()) <= token_budget:
                return summary

    # Fall back to simple truncation
    tokens = prompt.split()
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


class Tokenizer(Protocol):
    """Protocol for token counting implementations."""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        ...


class TiktokenCounter:
    """Accurate token counter using tiktoken for OpenAI models."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize with tiktoken encoding.

        Args:
            encoding_name: tiktoken encoding name (cl100k_base for GPT-4/GPT-3.5)
        """
        tk = _get_tiktoken()
        if not tk:
            raise ImportError("tiktoken not available")
        self.encoding = tk.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))


class ApproximateCounter:
    """Fallback token counter using character-based approximation."""

    def __init__(self, chars_per_token: int = 4):
        """Initialize with character-to-token ratio.

        Args:
            chars_per_token: Characters per token for approximation
        """
        self.chars_per_token = chars_per_token

    def count_tokens(self, text: str) -> int:
        """Approximate token count using character division."""
        return max(1, len(text) // self.chars_per_token)


def is_tiktoken_available() -> bool:
    """Check if tiktoken is available for accurate token counting.

    Returns:
        True if tiktoken can be imported and used
    """
    return _get_tiktoken() is not None


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
        model: str = "unknown",
        provider: str = "lmstudio",
    ):
        """Initialize the token counting adapter.

        Args:
            adapter: The LLM adapter to wrap
            agent_name: The name of the agent using this adapter
            metrics: The metrics collector to record token usage
            summarizer: Optional function used to summarize prompts when they
                exceed ``token_budget``
            model: Model name for accurate token counting
            provider: Provider name for accurate token counting
        """
        self.adapter = adapter
        self.agent_name = agent_name
        self.metrics = metrics
        self.token_counter = {"in": 0, "out": 0}
        self.token_budget = token_budget
        self.summarizer = summarizer
        self.model = model
        self.provider = provider

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
                prompt, self.token_budget, summarizer=self.summarizer,
                model=self.model, provider=self.provider
            )
        result = self.adapter.generate(prompt, model=model, **kwargs)
        # Use accurate token counting for input and output
        self.token_counter["in"] += count_tokens_accurate(prompt, self.model, self.provider)
        self.token_counter["out"] += count_tokens_accurate(str(result), self.model, self.provider)
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
    model: str = "unknown",
    provider: str = "lmstudio",
) -> Iterator[Tuple[Dict[str, int], "TokenCountingAdapter"]]:
    """Context manager for counting tokens.

    Args:
        agent_name: The name of the agent
        adapter: The LLM adapter to count tokens for
        metrics: The metrics collector to record token usage
        token_budget: Optional token budget to apply to prompts
        summarizer: Optional function used to summarize prompts when they
            exceed ``token_budget``
        model: Model name for accurate token counting
        provider: Provider name for accurate token counting

    Yields:
        A dictionary with token counts and the wrapped adapter
    """
    token_counter = TokenCountingAdapter(
        adapter,
        agent_name,
        metrics,
        token_budget,
        summarizer,
        model,
        provider,
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
    model: str = "unknown",
    provider: str = "lmstudio",
) -> Callable[[Callable[[LLMAdapter, Any], T]], Callable[[LLMAdapter, Any], T]]:
    """Decorator for functions that use LLM adapters to count tokens.

    Args:
        agent_name: The name of the agent
        metrics: The metrics collector to record token usage
        token_budget: Optional token budget to apply to prompts
        summarizer: Optional function used to summarize prompts when they
            exceed ``token_budget``
        model: Model name for accurate token counting
        provider: Provider name for accurate token counting

    Returns:
        A decorator function
    """

    def decorator(
        func: Callable[[LLMAdapter, Any], T],
    ) -> Callable[[LLMAdapter, Any], T]:
        @functools.wraps(func)
        def wrapper(adapter: LLMAdapter, *args: Any, **kwargs: Any) -> T:
            with count_tokens(
                agent_name, adapter, metrics, token_budget, summarizer, model, provider
            ) as (
                token_counter,
                counting_adapter,
            ):
                return func(counting_adapter, *args, **kwargs)

        return wrapper

    return decorator


def get_tokenizer(model: str, provider: str = "lmstudio") -> Tokenizer:
    """Get appropriate tokenizer for model and provider.

    Args:
        model: Model name (e.g., "gpt-3.5-turbo", "llama-2-7b")
        provider: Provider name (e.g., "openai", "lmstudio", "openrouter")

    Returns:
        Tokenizer instance appropriate for the model/provider

    Raises:
        ImportError: If tiktoken is needed but not available
    """
    # Try tiktoken for OpenAI models and compatible providers
    if provider == "openai" or "gpt" in model.lower():
        try:
            # Map models to appropriate encodings
            if "gpt-4" in model.lower():
                return TiktokenCounter("cl100k_base")
            elif "gpt-3.5" in model.lower():
                return TiktokenCounter("cl100k_base")
            else:
                return TiktokenCounter("cl100k_base")
        except (ImportError, Exception) as e:
            logger.debug(f"tiktoken unavailable for {model}, using approximation: {e}")

    # Default to approximation for other models
    return ApproximateCounter(chars_per_token=4)


def count_tokens_accurate(text: str, model: str, provider: str = "lmstudio") -> int:
    """Count tokens accurately using appropriate tokenizer.

    Args:
        text: Text to count tokens for
        model: Model name for tokenizer selection
        provider: Provider name for tokenizer selection

    Returns:
        Accurate token count using best available method
    """
    tokenizer = get_tokenizer(model, provider)
    return tokenizer.count_tokens(text)
