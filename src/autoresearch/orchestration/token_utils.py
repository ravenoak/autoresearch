from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator

from ..config.models import ConfigModel
from .metrics import OrchestrationMetrics
from .state import QueryState  # for type hints in execute_with_adapter


@contextmanager
def _capture_token_usage(
    agent_name: str, metrics: OrchestrationMetrics, config: ConfigModel
) -> Iterator[tuple[dict[str, int], Any]]:
    """Capture token usage for all LLM calls within the block.

    This method uses the TokenCountingAdapter to count tokens for all LLM calls
    made within the context manager block. It yields a tuple containing a dictionary
    with token counts and the wrapped adapter that should be used for LLM calls.

    Args:
        agent_name: The name of the agent making the LLM calls
        metrics: The metrics collector to record token usage
        config: The system configuration containing the LLM backend

    Yields:
        A tuple containing (token_counter, wrapped_adapter)
    """
    from autoresearch.llm.token_counting import count_tokens
    import autoresearch.llm as llm

    backend = config.llm_backend
    adapter = llm.get_pooled_adapter(backend)
    token_budget: int | None = getattr(config, "token_budget", None)

    with count_tokens(agent_name, adapter, metrics, token_budget) as (
        token_counter,
        base_adapter,
    ):
        wrapped: Any = base_adapter
        if token_budget is not None:
            tb: int = token_budget

            class PromptCompressAdapter:
                def __init__(self, inner: Any) -> None:
                    self.inner = inner

                def generate(
                    self, prompt: str, model: str | None = None, **kwargs: Any
                ) -> str:
                    prompt = metrics.compress_prompt_if_needed(prompt, tb)
                    return self.inner.generate(prompt, model=model, **kwargs)

                def __getattr__(self, name: str) -> Any:  # pragma: no cover
                    return getattr(self.inner, name)

            wrapped = PromptCompressAdapter(wrapped)
        yield token_counter, wrapped


def _execute_with_adapter(
    agent: Any, state: QueryState, config: ConfigModel, adapter: Any
) -> Dict[str, Any]:
    """Execute an agent with a specific adapter.

    This method handles executing an agent with a specific adapter, either by:
    1. Passing the adapter directly to the execute method if it supports it
    2. Temporarily setting the adapter in the agent's context

    Args:
        agent: The agent to execute
        state: The current query state
        config: The system configuration
        adapter: The adapter to use for LLM calls

    Returns:
        The result of agent execution
    """
    import inspect

    sig = inspect.signature(agent.execute)

    if "adapter" in sig.parameters:
        return agent.execute(state, config, adapter=adapter)
    elif hasattr(agent, "set_adapter"):
        original_adapter = (
            agent.get_adapter() if hasattr(agent, "get_adapter") else None
        )
        try:
            agent.set_adapter(adapter)
            return agent.execute(state, config)
        finally:
            if original_adapter is not None:
                agent.set_adapter(original_adapter)
    else:
        return agent.execute(state, config)
