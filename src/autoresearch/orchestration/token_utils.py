from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Protocol, TypeGuard, cast

from ..config.models import ConfigModel
from .metrics import OrchestrationMetrics
from .state import QueryState  # for type hints in execute_with_adapter
from .types import AgentExecutionResult


class AdapterProtocol(Protocol):
    """Structural protocol capturing the ``generate`` method used by adapters."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: object) -> str:
        """Generate a response for ``prompt``."""


class SupportsExecute(Protocol):
    """Structural protocol capturing the execute signature used by agents."""

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        **kwargs: object,
    ) -> AgentExecutionResult:
        """Execute the agent with optional keyword arguments."""


class SupportsAdapterMutation(Protocol):
    """Protocol for agents exposing temporary adapter mutation hooks."""

    def set_adapter(self, adapter: AdapterProtocol) -> None:  # pragma: no cover - structural
        """Inject a temporary adapter implementation."""

    def get_adapter(self) -> AdapterProtocol:  # pragma: no cover - structural
        """Return the currently configured adapter."""


class SupportsAdapterSetter(Protocol):
    """Protocol for agents that accept temporary adapter injection."""

    def set_adapter(self, adapter: AdapterProtocol) -> None:
        """Inject a temporary adapter implementation."""


class SupportsExecuteWithAdapterSetter(SupportsExecute, SupportsAdapterSetter, Protocol):
    """Agent protocol combining execution and adapter setter hooks."""


class SupportsExecuteWithMutation(
    SupportsExecuteWithAdapterSetter, SupportsAdapterMutation, Protocol
):
    """Agent protocol exposing both setter and getter adapter hooks."""


def supports_adapter_mutation(obj: object) -> TypeGuard[SupportsExecuteWithMutation]:
    """Return ``True`` when ``obj`` exposes ``set_adapter``/``get_adapter`` hooks."""

    set_adapter = getattr(obj, "set_adapter", None)
    get_adapter = getattr(obj, "get_adapter", None)
    execute = getattr(obj, "execute", None)
    return callable(set_adapter) and callable(get_adapter) and callable(execute)


def supports_adapter_setter(obj: object) -> TypeGuard[SupportsExecuteWithAdapterSetter]:
    """Return ``True`` when ``obj`` supports adapter injection via ``set_adapter``."""

    set_adapter = getattr(obj, "set_adapter", None)
    execute = getattr(obj, "execute", None)
    return callable(set_adapter) and callable(execute)


def is_agent_execution_result(result: object) -> TypeGuard[AgentExecutionResult]:
    """Return ``True`` for mapping results compatible with :class:`AgentExecutionResult`."""

    if not isinstance(result, Mapping):
        return False
    return all(isinstance(key, str) for key in result.keys())


@contextmanager
def _capture_token_usage(
    agent_name: str, metrics: OrchestrationMetrics, config: ConfigModel
) -> Iterator[tuple[dict[str, int], AdapterProtocol]]:
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
    adapter: AdapterProtocol = llm.get_pooled_adapter(backend)
    token_budget: int | None = getattr(config, "token_budget", None)

    with count_tokens(agent_name, adapter, metrics, token_budget) as (
        token_counter,
        base_adapter,
    ):
        wrapped: AdapterProtocol = base_adapter
        if token_budget is not None:
            tb: int = token_budget

            class PromptCompressAdapter:
                def __init__(self, inner: AdapterProtocol) -> None:
                    self.inner = inner

                def generate(
                    self, prompt: str, model: str | None = None, **kwargs: object
                ) -> str:
                    prompt = metrics.compress_prompt_if_needed(prompt, tb)
                    return self.inner.generate(prompt, model=model, **kwargs)

                def __getattr__(self, name: str) -> object:  # pragma: no cover
                    return getattr(self.inner, name)

            wrapped = cast(AdapterProtocol, PromptCompressAdapter(wrapped))
        yield token_counter, wrapped


def _execute_with_adapter(
    agent: SupportsExecute,
    state: QueryState,
    config: ConfigModel,
    adapter: AdapterProtocol,
) -> AgentExecutionResult:
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
        result = agent.execute(state, config, adapter=adapter)
    elif supports_adapter_setter(agent):
        adapter_agent = agent
        original_adapter: AdapterProtocol | None = None
        if supports_adapter_mutation(adapter_agent):
            original_adapter = adapter_agent.get_adapter()
        try:
            adapter_agent.set_adapter(adapter)
            result = agent.execute(state, config)
        finally:
            if original_adapter is not None:
                adapter_agent.set_adapter(original_adapter)
    else:
        result = agent.execute(state, config)

    if not is_agent_execution_result(result):
        raise TypeError(
            "Agent.execute must return a mapping compatible with QueryState.update"
        )

    return result
