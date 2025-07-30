import builtins
import sys
import types

from autoresearch import resource_monitor


def test_get_gpu_stats_pynvml(monkeypatch):
    fake_pynvml = types.SimpleNamespace(
        nvmlInit=lambda: None,
        nvmlShutdown=lambda: None,
        nvmlDeviceGetCount=lambda: 2,
        nvmlDeviceGetHandleByIndex=lambda i: i,
        nvmlDeviceGetUtilizationRates=lambda h: types.SimpleNamespace(gpu=10.0 * (h + 1)),
        nvmlDeviceGetMemoryInfo=lambda h: types.SimpleNamespace(used=(h + 1) * 1024 * 1024),
    )
    monkeypatch.setitem(sys.modules, "pynvml", fake_pynvml)
    util, mem = resource_monitor._get_gpu_stats()
    assert util == 15.0
    assert mem == 3.0


def test_get_gpu_stats_cli_psutil(monkeypatch):
    class FakeProc:
        def communicate(self, timeout=None):
            return "25, 512", ""

    fake_psutil = types.SimpleNamespace(Popen=lambda *a, **k: FakeProc())
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    orig_import = builtins.__import__
    monkeypatch.setattr(
        builtins,
        "__import__",
        lambda name, *a, **k: (_ for _ in ()).throw(ImportError())
        if name == "pynvml"
        else orig_import(name, *a, **k),
    )
    util, mem = resource_monitor._get_gpu_stats()
    assert util == 25.0
    assert mem == 512.0


def test_get_gpu_stats_cli_subprocess(monkeypatch):
    def fake_run(*args, **kwargs):
        class FakeRes:
            stdout = "30, 1024"
        return FakeRes()

    orig_import = builtins.__import__
    monkeypatch.setattr(
        builtins,
        "__import__",
        lambda name, *a, **k: (_ for _ in ()).throw(ImportError())
        if name in {"pynvml", "psutil"}
        else orig_import(name, *a, **k),
    )
    monkeypatch.setitem(sys.modules, "subprocess", types.SimpleNamespace(run=fake_run, PIPE=None, DEVNULL=None))
    util, mem = resource_monitor._get_gpu_stats()
    assert util == 30.0
    assert mem == 1024.0
