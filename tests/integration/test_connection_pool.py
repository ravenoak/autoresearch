import autoresearch.search as search
from autoresearch.llm.adapters import LMStudioAdapter
from autoresearch.config import ConfigModel
from autoresearch.llm import pool as llm_pool


def test_search_session_reuse_and_cleanup(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    session_ids = []

    def dummy_backend(q, max_results=5):
        session_ids.append(id(search.get_http_session()))
        return []

    monkeypatch.setitem(search.Search.backends, "dummy", dummy_backend)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    search.Search.external_lookup("a")
    search.Search.external_lookup("b")
    assert len(set(session_ids)) == 1

    first = session_ids[0]
    search.close_http_session()
    search.Search.external_lookup("c")
    assert session_ids[-1] != first


def test_llm_session_reuse_and_cleanup(monkeypatch):
    session_ids = []

    def mock_post(self, url, json=None, timeout=30, headers=None):
        session_ids.append(id(self))
        class R:
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}
        return R()

    session = llm_pool.get_session()
    monkeypatch.setattr(session, "post", mock_post)

    adapter = LMStudioAdapter()
    adapter.generate("hi")
    adapter.generate("there")
    assert len(set(session_ids)) == 1

    first = session_ids[0]
    llm_pool.close_session()
    session2 = llm_pool.get_session()
    assert id(session2) != first

