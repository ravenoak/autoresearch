"""Global connection and process pools used across the project."""
from __future__ import annotations

import multiprocessing
import threading

import requests


_process_pool: multiprocessing.pool.Pool | None = None
_process_lock = threading.Lock()

_http_session: requests.Session | None = None
_http_lock = threading.Lock()


def get_process_pool(size: int) -> multiprocessing.pool.Pool:
    """Return a global multiprocessing pool of the given size."""
    global _process_pool
    with _process_lock:
        if _process_pool is None or getattr(_process_pool, "_processes", None) != size:
            if _process_pool is not None:
                _process_pool.close()
                _process_pool.join()
            ctx = multiprocessing.get_context("spawn")
            _process_pool = ctx.Pool(processes=size)
        return _process_pool


def close_process_pool() -> None:
    """Close the global multiprocessing pool if it exists."""
    global _process_pool
    with _process_lock:
        if _process_pool is not None:
            _process_pool.close()
            _process_pool.join()
            _process_pool = None


def get_http_session(size: int = 10) -> requests.Session:
    """Return a pooled HTTP session for search backends."""
    global _http_session
    with _http_lock:
        if _http_session is None:
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            _http_session = session
        return _http_session


def close_http_session() -> None:
    """Close the pooled HTTP session if open."""
    global _http_session
    with _http_lock:
        if _http_session is not None:
            _http_session.close()
            _http_session = None
