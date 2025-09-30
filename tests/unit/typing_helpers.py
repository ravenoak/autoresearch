"""Typed helper factories for unit tests.

These helpers replace dynamic ``types.SimpleNamespace`` objects that previously
stubbed configuration or monitoring objects.  They provide the same limited
interface that the tests exercise while offering static structure for type
checking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence


@dataclass(slots=True)
class ContextAwareConfig:
    """Minimal context-aware configuration stub."""

    enabled: bool = False


@dataclass(slots=True)
class SearchConfig:
    """Search configuration subset consumed in tests."""

    backends: list[str] = field(default_factory=list)
    hybrid_query: bool = False
    use_semantic_similarity: bool = False
    embedding_backends: list[str] = field(default_factory=list)
    context_aware: ContextAwareConfig = field(default_factory=ContextAwareConfig)
    max_workers: int = 1
    http_pool_size: int | None = None


@dataclass(slots=True)
class DistributedConfig:
    """Distributed configuration stub with the single flag used in tests."""

    enabled: bool = False


@dataclass(slots=True)
class StorageConfig:
    """Storage configuration subset required by unit tests."""

    duckdb_path: str = ":memory:"


@dataclass(slots=True)
class RuntimeConfig:
    """Top-level configuration combining the pieces referenced in tests."""

    search: SearchConfig = field(default_factory=SearchConfig)
    loops: int = 1
    distributed: bool = False
    distributed_config: DistributedConfig = field(default_factory=DistributedConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


def make_search_config(
    *,
    backends: Iterable[str] | None = None,
    hybrid_query: bool = False,
    use_semantic_similarity: bool = False,
    embedding_backends: Sequence[str] | None = None,
    context_aware_enabled: bool = False,
    max_workers: int = 1,
    http_pool_size: int | None = None,
) -> SearchConfig:
    """Build a ``SearchConfig`` stub with only the attributes tests rely on."""

    return SearchConfig(
        backends=list(backends or []),
        hybrid_query=hybrid_query,
        use_semantic_similarity=use_semantic_similarity,
        embedding_backends=list(embedding_backends or []),
        context_aware=ContextAwareConfig(enabled=context_aware_enabled),
        max_workers=max_workers,
        http_pool_size=http_pool_size,
    )


def make_storage_config(*, duckdb_path: str = ":memory:") -> StorageConfig:
    """Return a minimal storage configuration stub."""

    return StorageConfig(duckdb_path=duckdb_path)


def make_runtime_config(
    *,
    search: SearchConfig | None = None,
    loops: int = 1,
    distributed: bool = False,
    distributed_enabled: bool = False,
    storage: StorageConfig | None = None,
) -> RuntimeConfig:
    """Combine configuration components into a runtime config stub."""

    return RuntimeConfig(
        search=search or SearchConfig(),
        loops=loops,
        distributed=distributed,
        distributed_config=DistributedConfig(enabled=distributed_enabled),
        storage=storage or StorageConfig(),
    )


@dataclass(slots=True)
class MemoryInfo:
    """Process memory information returned by psutil stubs."""

    rss: int


@dataclass(slots=True)
class ProcessStub:
    """Minimal ``psutil.Process`` replacement."""

    memory: MemoryInfo

    def memory_info(self) -> MemoryInfo:  # pragma: no cover - trivial
        return self.memory


@dataclass(slots=True)
class VirtualMemoryInfo:
    """Subset of virtual memory metrics consumed in Streamlit tests."""

    percent: float
    used: int
    total: int


@dataclass(slots=True)
class PsutilStub:
    """Expose the psutil APIs patched within unit tests."""

    cpu_percent_value: float
    virtual_memory_info: VirtualMemoryInfo
    process_memory: MemoryInfo

    def cpu_percent(self, interval: float | None = None) -> float:  # pragma: no cover - trivial
        return self.cpu_percent_value

    def virtual_memory(self) -> VirtualMemoryInfo:  # pragma: no cover - trivial
        return self.virtual_memory_info

    def Process(self, pid: int | None = None) -> ProcessStub:  # pragma: no cover - trivial
        return ProcessStub(self.process_memory)


def make_psutil_stub(
    *,
    cpu_percent: float = 0.0,
    memory_percent: float = 0.0,
    memory_used: int = 0,
    memory_total: int = 0,
    process_rss: int = 0,
) -> PsutilStub:
    """Create a psutil stub exposing only the metrics exercised in tests."""

    return PsutilStub(
        cpu_percent_value=cpu_percent,
        virtual_memory_info=VirtualMemoryInfo(
            percent=memory_percent,
            used=memory_used,
            total=memory_total,
        ),
        process_memory=MemoryInfo(rss=process_rss),
    )


class StreamlitSessionState(dict):
    """Dictionary with attribute access to mirror Streamlit's session state."""

    def __getattr__(self, key: str):  # pragma: no cover - trivial
        return self[key]

    def __setattr__(self, key: str, value):  # pragma: no cover - trivial
        self[key] = value


@dataclass(slots=True)
class StreamlitStub:
    """Minimal Streamlit interface required for tests."""

    session_state: StreamlitSessionState
    markdown: Callable[..., None]


def make_streamlit_stub(
    *,
    markdown: Callable[..., None] | None = None,
) -> StreamlitStub:
    """Return a Streamlit stub with a mutable session state."""

    def _default_markdown(*_args, **_kwargs) -> None:  # pragma: no cover - trivial
        return None

    return StreamlitStub(
        session_state=StreamlitSessionState(),
        markdown=markdown or _default_markdown,
    )


@dataclass(slots=True)
class LLMPoolConfig:
    """Minimal configuration for the LLM pool used in unit tests."""

    llm_pool_size: int


def make_llm_pool_config(size: int) -> LLMPoolConfig:
    """Construct an ``LLMPoolConfig`` exposing the configured pool size."""

    return LLMPoolConfig(llm_pool_size=size)

