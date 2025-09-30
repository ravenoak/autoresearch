from __future__ import annotations

import atexit
import threading
from typing import Optional, cast

import requests
from urllib3.util.retry import Retry

from ..config.loader import get_config
from ..logging_utils import get_logger
from ..typing.http import (
    HTTPAdapter,
    RequestsAdapterProtocol,
    RequestsSessionProtocol,
)

log = get_logger(__name__)

_http_session: Optional[RequestsSessionProtocol] = None
_http_lock = threading.Lock()
_atexit_registered = False


def _build_search_adapter(
    pool_size: int, retries: Retry
) -> RequestsAdapterProtocol:
    """Return a configured HTTP adapter for search traffic."""

    return HTTPAdapter(
        pool_connections=pool_size,
        pool_maxsize=pool_size,
        max_retries=retries,
    )


def set_http_session(session: RequestsSessionProtocol) -> None:
    """Inject an existing HTTP session (for distributed workers)."""
    global _http_session, _atexit_registered
    with _http_lock:
        _http_session = session
        if not _atexit_registered:
            atexit.register(close_http_session)
            _atexit_registered = True


def get_http_session() -> RequestsSessionProtocol:
    """Return a pooled HTTP session."""
    global _http_session, _atexit_registered
    with _http_lock:
        if _http_session is None:
            cfg = get_config()
            size = getattr(cfg.search, "http_pool_size", 10)
            session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET", "POST"],
            )
            try:
                adapter = _build_search_adapter(size, retries)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
            except Exception:
                session.close()
                raise
            _http_session = cast(RequestsSessionProtocol, session)
            if not _atexit_registered:
                atexit.register(close_http_session)
                _atexit_registered = True
        assert _http_session is not None
        return _http_session


def close_http_session() -> None:
    """Close the pooled HTTP session."""
    global _http_session, _atexit_registered
    with _http_lock:
        if _http_session is not None:
            _http_session.close()
            _http_session = None
            _atexit_registered = False
