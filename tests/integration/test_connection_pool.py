import autoresearch.search as search
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from autoresearch.config.models import ConfigModel
from autoresearch.llm import pool as llm_pool
from autoresearch.storage import StorageManager
import autoresearch.storage as storage
from autoresearch.config.loader import ConfigLoader


def test_search_session_reuse_and_cleanup(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    session_ids = []

    def dummy_backend(q, max_results=5):
        session_ids.append(id(search.get_http_session()))
        return []

    monkeypatch.setitem(search.Search.backends, "dummy", dummy_backend)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    search.Search.external_lookup("a")
    search.Search.external_lookup("b")
    assert len(set(session_ids)) == 1

    first = session_ids[0]
    search.close_http_session()
    search.Search.external_lookup("c")
    assert session_ids[-1] != first


def test_llm_session_reuse_and_cleanup(monkeypatch):
    session_ids = []

    def mock_post(url, json=None, timeout=30, headers=None):
        session_ids.append(id(session))

        class R:

            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return R()

    session = llm_pool.get_session()
    monkeypatch.setattr(session, "post", mock_post)

    adapter = llm_pool.get_adapter("lmstudio")
    adapter.generate("hi")
    adapter.generate("there")
    assert len(set(session_ids)) == 1

    first = session_ids[0]
    llm_pool.close_session()
    session2 = llm_pool.get_session()
    assert id(session2) != first


def test_llm_adapter_pool_concurrency(monkeypatch):
    """Adapters should be reused across threads."""
    session = llm_pool.get_session()

    def mock_post(url, json=None, timeout=30, headers=None):
        class R:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return R()

    monkeypatch.setattr(session, "post", mock_post)

    ids = []

    def call():
        adapter = llm_pool.get_adapter("lmstudio")
        adapter.generate("x")
        ids.append(id(adapter))

    with ThreadPoolExecutor(max_workers=5) as ex:
        for _ in range(20):
            ex.submit(call)

    assert len(set(ids)) == 1
    first_adapter = llm_pool.get_adapter("lmstudio")
    llm_pool.close_adapters()
    assert llm_pool.get_adapter("lmstudio") is not first_adapter


def test_duckdb_connection_pool_concurrency(tmp_path):
    cfg = ConfigModel(
        loops=1,
        storage=dict(max_connections=2, duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    llm_pool.close_adapters()
    search.close_http_session()
    storage.teardown(remove_db=True)
    with patch("autoresearch.config.loader.ConfigLoader.load_config", lambda self: cfg):
        ConfigLoader.reset_instance()
        StorageManager.setup(cfg.storage.duckdb_path)
    ids = []

    def use_conn():
        with StorageManager.connection() as conn:
            conn.execute("SELECT 1").fetchall()
            ids.append(id(conn))

    with ThreadPoolExecutor(max_workers=4) as ex:
        for _ in range(10):
            ex.submit(use_conn)

    backend = storage.StorageManager.context.db_backend
    assert backend is not None
    assert len(set(ids)) <= backend._max_connections
    storage.teardown(remove_db=True)
