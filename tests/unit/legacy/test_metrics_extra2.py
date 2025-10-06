# mypy: ignore-errors
import sys
import builtins
import types
from autoresearch.orchestration import metrics


def test_get_system_usage_success(monkeypatch):
    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: 42.0,
        Process=lambda: types.SimpleNamespace(
            memory_info=lambda: types.SimpleNamespace(rss=1024 * 1024)
        ),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    cpu, mem, gpu, gpu_mem = metrics._get_system_usage()
    assert cpu == 42.0 and mem == 1.0 and gpu == 0.0 and gpu_mem == 0.0


def test_get_system_usage_failure(monkeypatch):
    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError
        return orig_import(name, *args, **kwargs)

    orig_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", fake_import)
    cpu, mem, gpu, gpu_mem = metrics._get_system_usage()
    assert cpu == 0.0 and mem == 0.0 and gpu == 0.0 and gpu_mem == 0.0
