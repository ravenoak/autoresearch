# mypy: ignore-errors
import threading
import types

import networkx as nx
import autoresearch.storage as storage
from autoresearch.storage import StorageManager


def test_setup_thread_safe(monkeypatch):
    calls: list[int] = []
    original_setup = storage.setup

    def counted_setup(*args, **kwargs):
        calls.append(1)
        return original_setup(*args, **kwargs)

    monkeypatch.setattr(storage, "setup", counted_setup)
    StorageManager.context.db_backend = None
    StorageManager.context.graph = None
    StorageManager.context.rdf_store = None

    contexts: list = []
    thread_errors: list[BaseException] = []

    def worker() -> None:
        try:
            ctx = StorageManager.setup(db_path=":memory:")
        except BaseException as exc:  # pragma: no cover - defensive guard
            thread_errors.append(exc)
            raise
        else:
            contexts.append(ctx)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not thread_errors, f"worker threads failed: {thread_errors!r}"
    assert len(calls) == 1
    assert len(contexts) == len(threads)
    assert len({id(c) for c in contexts}) == 1
    assert StorageManager.context.db_backend is not None, "setup did not complete"
    StorageManager.teardown(remove_db=True)


def test_persist_claim_thread_safe(monkeypatch):
    # Save original context state
    original_graph = StorageManager.context.graph
    original_rdf_store = StorageManager.context.rdf_store
    original_db_backend = StorageManager.context.db_backend

    try:
        StorageManager.context.graph = nx.DiGraph()
        StorageManager.context.rdf_store = object()

        class DummyBackend:
            def persist_claim(self, claim) -> None:  # pragma: no cover - stub
                pass

            def update_claim(self, claim, partial_update) -> None:  # pragma: no cover
                pass

            def get_connection(self):  # pragma: no cover - stub
                return self

            def _create_tables(self, skip_migrations: bool = False) -> None:  # pragma: no cover - stub
                pass

        StorageManager.context.db_backend = DummyBackend()

        monkeypatch.setattr(
            storage,
            "ConfigLoader",
            lambda: types.SimpleNamespace(config=types.SimpleNamespace(ram_budget_mb=0)),
        )
        monkeypatch.setattr(StorageManager, "_persist_to_rdf", lambda c: None)
        monkeypatch.setattr(StorageManager, "_update_rdf_claim", lambda c, p: None)
        monkeypatch.setattr(StorageManager, "_persist_to_kuzu", lambda c: None)
        monkeypatch.setattr(StorageManager, "_enforce_ram_budget", lambda b: None)
        monkeypatch.setattr(StorageManager, "has_vss", lambda: False)

        claims = [
            {"id": f"c{i}", "type": "fact", "content": f"content {i}"}
            for i in range(10)
        ]

        def worker(claim: dict) -> None:
            StorageManager.persist_claim(claim)

        threads = [threading.Thread(target=worker, args=(cl,)) for cl in claims]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        graph = StorageManager.get_graph()
        assert graph.number_of_nodes() == len(claims)
    finally:
        # Restore original context state
        StorageManager.context.graph = original_graph
        StorageManager.context.rdf_store = original_rdf_store
        StorageManager.context.db_backend = original_db_backend
