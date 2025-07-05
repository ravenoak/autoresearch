from __future__ import annotations

from typing import Optional, Dict, TYPE_CHECKING
from threading import Lock
import requests

from ..config import get_config

_session: Optional[requests.Session] = None
_lock = Lock()


def set_session(session: requests.Session) -> None:
    """Inject a pre-created HTTP session."""
    global _session
    with _lock:
        _session = session


# Pool of instantiated LLM adapters keyed by backend name
if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from .adapters import LLMAdapter

_adapters: Dict[str, "LLMAdapter"] = {}
_adapter_lock = Lock()


def get_session() -> requests.Session:
    """Return a pooled HTTP session for LLM adapters."""
    global _session
    with _lock:
        if _session is None:
            cfg = get_config()
            size = getattr(cfg, "llm_pool_size", 2)
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=size,
                pool_maxsize=size,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            _session = session
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
