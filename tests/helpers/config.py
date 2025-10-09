"""Configuration helpers tailored for unit tests.

These dataclasses provide a light-weight stand-in for :class:`ConfigModel`
instances. They expose the attributes accessed by orchestrator and search
unit tests without importing the full pydantic models. Factory helpers
produce instances with sensible defaults while still allowing tests to
override specific fields explicitly. TypedDict exports mirror the
structure produced by :meth:`ConfigModelStub.model_dump`.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Optional, TypedDict

from autoresearch.models import ReasoningMode


class ContextAwareSearchConfigDump(TypedDict):
    """Serialized form of :class:`ContextAwareSearchConfigStub`."""

    enabled: bool
    use_query_expansion: bool
    expansion_factor: float
    use_search_history: bool
    max_history_items: int
    graph_signal_weight: float
    planner_graph_conditioning: bool


class QueryRewriteConfigDump(TypedDict):
    """Serialized representation of :class:`QueryRewriteConfigStub`."""

    enabled: bool
    max_attempts: int
    min_results: int
    min_unique_sources: int
    coverage_gap_threshold: float


class AdaptiveKConfigDump(TypedDict):
    """Serialized representation of :class:`AdaptiveKConfigStub`."""

    enabled: bool
    min_k: int
    max_k: int
    step: int
    coverage_gap_threshold: float


class SearchConfigDump(TypedDict):
    """Serialized representation of :class:`SearchConfigStub`."""

    context_aware: ContextAwareSearchConfigDump
    query_rewrite: QueryRewriteConfigDump
    adaptive_k: AdaptiveKConfigDump


class ConfigModelDump(TypedDict):
    """Structure returned by :meth:`ConfigModelStub.model_dump`."""

    token_budget: Optional[int]
    loops: int
    adaptive_max_factor: int
    adaptive_min_buffer: int
    search: SearchConfigDump
    gate_graph_contradiction_threshold: float
    gate_graph_similarity_threshold: float
    gate_capture_query_strategy: bool
    gate_capture_self_critique: bool
    agents: list[str]
    reasoning_mode: Optional[str]
    llm_backend: str


ContextOverrideValue = bool | float | int


@dataclass(slots=True)
class ContextAwareSearchConfigStub:
    """Subset of context-aware search settings required in unit tests."""

    enabled: bool = True
    use_query_expansion: bool = True
    expansion_factor: float = 0.3
    use_search_history: bool = True
    max_history_items: int = 10
    graph_signal_weight: float = 0.2
    planner_graph_conditioning: bool = False


@dataclass(slots=True)
class SearchConfigStub:
    """Search configuration stub exposing the context-aware settings."""

    context_aware: ContextAwareSearchConfigStub = field(
        default_factory=ContextAwareSearchConfigStub
    )
    query_rewrite: "QueryRewriteConfigStub" = field(
        default_factory=lambda: QueryRewriteConfigStub()
    )
    adaptive_k: "AdaptiveKConfigStub" = field(
        default_factory=lambda: AdaptiveKConfigStub()
    )


@dataclass(slots=True)
class QueryRewriteConfigStub:
    """Subset of query rewrite settings required in tests."""

    enabled: bool = True
    max_attempts: int = 2
    min_results: int = 3
    min_unique_sources: int = 3
    coverage_gap_threshold: float = 0.45


@dataclass(slots=True)
class AdaptiveKConfigStub:
    """Subset of adaptive fetch configuration for tests."""

    enabled: bool = True
    min_k: int = 5
    max_k: int = 12
    step: int = 3
    coverage_gap_threshold: float = 0.4


@dataclass(slots=True)
class ConfigModelStub:
    """Minimal configuration object compatible with ``ConfigModel`` access."""

    token_budget: Optional[int] = None
    loops: int = 2
    adaptive_max_factor: int = 20
    adaptive_min_buffer: int = 10
    search: SearchConfigStub = field(default_factory=SearchConfigStub)
    gate_graph_contradiction_threshold: float = 0.25
    gate_graph_similarity_threshold: float = 0.0
    gate_capture_query_strategy: bool = True
    gate_capture_self_critique: bool = True
    agents: list[str] = field(default_factory=list)
    reasoning_mode: ReasoningMode = ReasoningMode.DIALECTICAL
    llm_backend: str = "lmstudio"

    def model_dump(self) -> ConfigModelDump:
        """Return a dictionary representation mirroring ``BaseModel``."""

        return {
            "token_budget": self.token_budget,
            "loops": self.loops,
            "adaptive_max_factor": self.adaptive_max_factor,
            "adaptive_min_buffer": self.adaptive_min_buffer,
            "search": {
                "context_aware": {
                    "enabled": self.search.context_aware.enabled,
                    "use_query_expansion": (
                        self.search.context_aware.use_query_expansion
                    ),
                    "expansion_factor": self.search.context_aware.expansion_factor,
                    "use_search_history": (
                        self.search.context_aware.use_search_history
                    ),
                    "max_history_items": (
                        self.search.context_aware.max_history_items
                    ),
                    "graph_signal_weight": (
                        self.search.context_aware.graph_signal_weight
                    ),
                    "planner_graph_conditioning": (
                        self.search.context_aware.planner_graph_conditioning
                    ),
                },
                "query_rewrite": {
                    "enabled": self.search.query_rewrite.enabled,
                    "max_attempts": self.search.query_rewrite.max_attempts,
                    "min_results": self.search.query_rewrite.min_results,
                    "min_unique_sources": (
                        self.search.query_rewrite.min_unique_sources
                    ),
                    "coverage_gap_threshold": (
                        self.search.query_rewrite.coverage_gap_threshold
                    ),
                },
                "adaptive_k": {
                    "enabled": self.search.adaptive_k.enabled,
                    "min_k": self.search.adaptive_k.min_k,
                    "max_k": self.search.adaptive_k.max_k,
                    "step": self.search.adaptive_k.step,
                    "coverage_gap_threshold": (
                        self.search.adaptive_k.coverage_gap_threshold
                    ),
                },
            },
            "gate_graph_contradiction_threshold": (
                self.gate_graph_contradiction_threshold
            ),
            "gate_graph_similarity_threshold": self.gate_graph_similarity_threshold,
            "gate_capture_query_strategy": self.gate_capture_query_strategy,
            "gate_capture_self_critique": self.gate_capture_self_critique,
            "agents": list(self.agents),
            "reasoning_mode": self.reasoning_mode.value,
            "llm_backend": self.llm_backend,
        }

    def model_copy(self, *, deep: bool = False) -> ConfigModelStub:
        """Mimic ``BaseModel.model_copy`` for orchestration helpers."""

        return deepcopy(self) if deep else copy(self)


def make_context_aware_config(
    overrides: Mapping[str, ContextOverrideValue] | None = None,
) -> ContextAwareSearchConfigStub:
    """Return a context-aware configuration stub with optional overrides."""

    config = ContextAwareSearchConfigStub()
    if not overrides:
        return config
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise AttributeError(
                f"ContextAwareSearchConfigStub has no attribute '{key}'"
            )
        setattr(config, key, value)
    return config


SearchOverrideValue = bool | float | int


def make_search_config(
    *,
    context_overrides: Mapping[str, ContextOverrideValue] | None = None,
    overrides: Mapping[str, SearchOverrideValue] | None = None,
    query_rewrite_overrides: Mapping[str, SearchOverrideValue] | None = None,
    adaptive_overrides: Mapping[str, SearchOverrideValue] | None = None,
) -> SearchConfigStub:
    """Construct a search configuration stub for unit tests."""

    context_cfg = make_context_aware_config(context_overrides)
    query_rewrite_cfg = QueryRewriteConfigStub()
    if query_rewrite_overrides:
        for key, value in query_rewrite_overrides.items():
            if not hasattr(query_rewrite_cfg, key):
                raise AttributeError(
                    f"QueryRewriteConfigStub has no attribute '{key}' to override"
                )
            setattr(query_rewrite_cfg, key, value)
    adaptive_cfg = AdaptiveKConfigStub()
    if adaptive_overrides:
        for key, value in adaptive_overrides.items():
            if not hasattr(adaptive_cfg, key):
                raise AttributeError(
                    f"AdaptiveKConfigStub has no attribute '{key}' to override"
                )
            setattr(adaptive_cfg, key, value)
    search_cfg = SearchConfigStub(
        context_aware=context_cfg,
        query_rewrite=query_rewrite_cfg,
        adaptive_k=adaptive_cfg,
    )
    if overrides:
        for key, value in overrides.items():
            if key == "context_aware":
                raise ValueError(
                    "Use 'context_overrides' to customise context-aware settings"
                )
            if not hasattr(search_cfg, key):
                raise AttributeError(
                    f"SearchConfigStub has no attribute '{key}' to override"
                )
            setattr(search_cfg, key, value)
    return search_cfg


def make_config_model(
    *,
    token_budget: Optional[int] = None,
    loops: int = 2,
    adaptive_max_factor: int = 20,
    adaptive_min_buffer: int = 10,
    reasoning_mode: ReasoningMode = ReasoningMode.DIRECT,
    search_overrides: Mapping[str, SearchOverrideValue] | None = None,
    context_overrides: Mapping[str, ContextOverrideValue] | None = None,
    query_rewrite_overrides: Mapping[str, SearchOverrideValue] | None = None,
    adaptive_overrides: Mapping[str, SearchOverrideValue] | None = None,
) -> ConfigModelStub:
    """Create a :class:`ConfigModelStub` with explicit overrides when needed."""

    search_cfg = make_search_config(
        context_overrides=context_overrides,
        overrides=search_overrides,
        query_rewrite_overrides=query_rewrite_overrides,
        adaptive_overrides=adaptive_overrides,
    )
    return ConfigModelStub(
        token_budget=token_budget,
        loops=loops,
        adaptive_max_factor=adaptive_max_factor,
        adaptive_min_buffer=adaptive_min_buffer,
        reasoning_mode=reasoning_mode,
        search=search_cfg,
    )


__all__ = [
    "ConfigModelStub",
    "ContextAwareSearchConfigStub",
    "SearchConfigStub",
    "make_config_model",
    "make_search_config",
    "make_context_aware_config",
]
