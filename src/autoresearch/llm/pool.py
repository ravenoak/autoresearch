from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, cast
from threading import Lock

import requests

from ..config.loader import get_config
from ..typing.http import HTTPAdapter, RequestsAdapterProtocol, RequestsSessionProtocol

_session: Optional[RequestsSessionProtocol] = None
_lock = Lock()


def set_session(session: RequestsSessionProtocol) -> None:
    """Inject a pre-created HTTP session."""
    global _session
    with _lock:
        _session = session


# Pool of instantiated LLM adapters keyed by backend name
if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from .adapters import LLMAdapter

_adapters: Dict[str, "LLMAdapter"] = {}
_adapter_lock = Lock()


def _build_llm_adapter(pool_size: int) -> RequestsAdapterProtocol:
    """Return a configured HTTP adapter for LLM traffic."""

    return HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)


def get_session() -> RequestsSessionProtocol:
    """Return a pooled HTTP session for LLM adapters."""
    global _session
    with _lock:
        if _session is None:
            cfg = get_config()
            size = getattr(cfg, "llm_pool_size", 2)
            session = requests.Session()
            try:
                adapter = _build_llm_adapter(size)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
            except Exception:
                session.close()
                raise
            _session = cast(RequestsSessionProtocol, session)
        assert _session is not None
        return _session


def close_session() -> None:
    """Close the pooled HTTP session."""
    global _session
    with _lock:
        if _session is not None:
            _session.close()
            _session = None


def get_adapter(name: str) -> "LLMAdapter":
    """Return a pooled LLM adapter instance."""
    from .registry import LLMFactory

    with _adapter_lock:
        adapter = _adapters.get(name)
        if adapter is None:
            adapter = LLMFactory.get(name)
            _adapters[name] = adapter
        return adapter


def close_adapters() -> None:
    """Clear cached LLM adapters and close their HTTP session."""
    with _adapter_lock:
        _adapters.clear()
    close_session()
