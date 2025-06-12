"""Reasoning mode definitions and protocol interface."""
from __future__ import annotations

from enum import Enum
from typing import Protocol, TYPE_CHECKING

from ..models import QueryResponse

if TYPE_CHECKING:
    from ..config import ConfigModel
    from ..agents.registry import AgentFactory


class ReasoningMode(str, Enum):
    """Supported reasoning modes."""

    DIRECT = "direct"
    DIALECTICAL = "dialectical"
    CHAIN_OF_THOUGHT = "chain-of-thought"


class ReasoningStrategy(Protocol):
    """Interface for reasoning strategies."""

    def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
        """Execute reasoning for a query."""
        raise NotImplementedError


class ChainOfThoughtStrategy:
    """Simple strategy that records intermediate thoughts at each loop."""

    def run_query(
        self,
        query: str,
        config: "ConfigModel",
        *,
        agent_factory: type["AgentFactory"] | None = None,
    ) -> QueryResponse:
        """Run the query using repeated synthesizer steps."""
        from .state import QueryState
        from .metrics import OrchestrationMetrics
        from ..agents.registry import AgentFactory

        factory = agent_factory or AgentFactory
        synthesizer = factory.get("Synthesizer")

        loops = getattr(config, "loops", 1)

        state = QueryState(query=query)
        metrics = OrchestrationMetrics()
        thoughts: list[str] = []

        for _ in range(loops):
            metrics.start_cycle()
            result = synthesizer.execute(state, config)
            metrics.end_cycle()
            state.update(result)

            step = (
                result.get("results", {}).get("thesis")
                or result.get("results", {}).get("synthesis")
                or result.get("results", {}).get("final_answer")
            )
            if step:
                thoughts.append(step)
            state.cycle += 1

        state.metadata["execution_metrics"] = metrics.get_summary()
        state.results["chain_of_thought"] = thoughts

        return state.synthesize()
