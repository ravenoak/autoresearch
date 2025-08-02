import builtins
import types
from autoresearch import storage


def test_current_ram_fallback(monkeypatch):
    orig_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "psutil":
            raise ImportError
        return orig_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(storage, "resource", types.SimpleNamespace(getrusage=lambda x: types.SimpleNamespace(ru_maxrss=1024*1024)))
    mb = storage.StorageManager._current_ram_mb()
    assert mb == 1024.0


def test_pop_low_score_empty(monkeypatch):
    monkeypatch.setattr(storage.StorageManager.context, "graph", None)
    assert storage.StorageManager._pop_low_score() is None
