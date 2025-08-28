from __future__ import annotations

import atexit
import threading
from typing import Optional

import requests
from urllib3.util.retry import Retry

from ..config.loader import get_config
from ..logging_utils import get_logger

log = get_logger(__name__)

_http_session: Optional[requests.Session] = None
_http_lock = threading.Lock()
_atexit_registered = False


def set_http_session(session: requests.Session) -> None:
    """Inject an existing HTTP session (for distributed workers)."""
    global _http_session, _atexit_registered
    with _http_lock:
        _http_session = session
        if not _atexit_registered:
            atexit.register(close_http_session)
            _atexit_registered = True


def get_http_session() -> requests.Session:
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
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=size,
                pool_maxsize=size,
                max_retries=retries,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            _http_session = session
            if not _atexit_registered:
                atexit.register(close_http_session)
                _atexit_registered = True
        return _http_session


def close_http_session() -> None:
    """Close the pooled HTTP session."""
    global _http_session, _atexit_registered
    with _http_lock:
        if _http_session is not None:
            _http_session.close()
            _http_session = None
            _atexit_registered = False
