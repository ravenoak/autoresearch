import builtins
import sys
import types

from autoresearch import resource_monitor
from structlog.testing import capture_logs


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
        lambda name, *a, **k: (
            (_ for _ in ()).throw(ImportError()) if name == "pynvml" else orig_import(name, *a, **k)
        ),
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
        lambda name, *a, **k: (
            (_ for _ in ()).throw(ImportError())
            if name in {"pynvml", "psutil"}
            else orig_import(name, *a, **k)
        ),
    )
    fake_subprocess = types.ModuleType("subprocess")
    setattr(fake_subprocess, "run", fake_run)
    setattr(fake_subprocess, "PIPE", object())
    setattr(fake_subprocess, "DEVNULL", object())
    monkeypatch.setitem(sys.modules, "subprocess", fake_subprocess)
    util, mem = resource_monitor._get_gpu_stats()
    assert util == 30.0
    assert mem == 1024.0


def test_get_gpu_stats_logs_info_without_gpu_extra(monkeypatch):
    monkeypatch.setattr(resource_monitor, "_gpu_extra_enabled", lambda: False)
    monkeypatch.delitem(sys.modules, "pynvml", raising=False)
    monkeypatch.delitem(sys.modules, "psutil", raising=False)

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"pynvml", "psutil"}:
            raise ModuleNotFoundError(name)
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    fake_subprocess = types.ModuleType("subprocess")
    setattr(fake_subprocess, "PIPE", object())
    setattr(fake_subprocess, "DEVNULL", object())

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("nvidia-smi missing")

    setattr(fake_subprocess, "run", fake_run)
    monkeypatch.setitem(sys.modules, "subprocess", fake_subprocess)

    with capture_logs() as logs:
        util, mem = resource_monitor._get_gpu_stats()

    assert (util, mem) == (0.0, 0.0)
    dependency_events = [
        entry for entry in logs if entry.get("event") == "gpu_metrics_dependency_missing"
    ]
    assert {entry["dependency"] for entry in dependency_events} == {
        "pynvml",
        "nvidia-smi",
    }
    assert all(entry["log_level"] == "info" for entry in dependency_events)


def test_get_gpu_stats_logs_debug_with_gpu_extra(monkeypatch):
    monkeypatch.setattr(resource_monitor, "_gpu_extra_enabled", lambda: True)
    monkeypatch.delitem(sys.modules, "pynvml", raising=False)
    monkeypatch.delitem(sys.modules, "psutil", raising=False)

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"pynvml", "psutil"}:
            raise ModuleNotFoundError(name)
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    fake_subprocess = types.ModuleType("subprocess")
    setattr(fake_subprocess, "PIPE", object())
    setattr(fake_subprocess, "DEVNULL", object())
    setattr(
        fake_subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(stdout="0, 0"),
    )
    monkeypatch.setitem(sys.modules, "subprocess", fake_subprocess)

    with capture_logs() as logs:
        resource_monitor._get_gpu_stats()

    dependency_events = [
        entry for entry in logs if entry.get("event") == "gpu_metrics_dependency_missing"
    ]
    assert dependency_events
    assert all(entry["log_level"] == "debug" for entry in dependency_events)
