from __future__ import annotations

from typing import Optional
from threading import Lock
import requests

from ..config import get_config

_session: Optional[requests.Session] = None
_lock = Lock()


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
