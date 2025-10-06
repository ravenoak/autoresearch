from autoresearch.config.models import ConfigModel
import autoresearch.search as search
from autoresearch.llm import pool as llm_pool
import requests


def test_search_pool_reuse_and_cleanup(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.http_pool_size = 1
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    search.close_http_session()
    s1 = search.get_http_session()
    s2 = search.get_http_session()
    assert s1 is s2
    search.close_http_session()
    s3 = search.get_http_session()
    assert s3 is not s1


def test_llm_pool_reuse_and_cleanup(monkeypatch):
    cfg = ConfigModel()
    monkeypatch.setattr("autoresearch.llm.pool.get_config", lambda: cfg)
    llm_pool.close_session()
    s1 = llm_pool.get_session()
    s2 = llm_pool.get_session()
    assert s1 is s2
    llm_pool.close_session()
    s3 = llm_pool.get_session()
    assert s3 is not s1


def test_set_http_session(monkeypatch):
    """Injected session is returned by ``get_http_session``."""
    search.close_http_session()
    session = requests.Session()
    search.set_http_session(session)
    assert search.get_http_session() is session
    search.close_http_session()
