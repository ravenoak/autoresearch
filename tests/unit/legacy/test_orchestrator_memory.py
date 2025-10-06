# mypy: ignore-errors
import builtins
import sys
import types
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils


def test_get_memory_usage_psutil(monkeypatch):
    fake_psutil = types.SimpleNamespace(
        Process=lambda: types.SimpleNamespace(memory_info=lambda: types.SimpleNamespace(rss=42 * 1024 * 1024))
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    assert OrchestrationUtils.get_memory_usage() == 42.0


def test_get_memory_usage_fallback(monkeypatch):
    if "psutil" in sys.modules:
        del sys.modules["psutil"]

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    fake_resource = types.SimpleNamespace(
        getrusage=lambda *a, **k: types.SimpleNamespace(ru_maxrss=2048),
        RUSAGE_SELF=0,
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)
    assert OrchestrationUtils.get_memory_usage() == 2.0
