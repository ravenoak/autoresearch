"""Tests for resource monitor CPU and memory usage helpers."""

import builtins
import sys
import types

from autoresearch.resource_monitor import _get_usage


def test_get_usage_psutil(monkeypatch):
    """Return mocked CPU and memory statistics."""

    class FakeProcess:
        def memory_info(self):
            return types.SimpleNamespace(rss="104857600")

    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: "5.0",
        Process=lambda: FakeProcess(),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    cpu, mem = _get_usage()
    assert cpu == 5.0
    assert mem == 100.0


def test_get_usage_no_psutil(monkeypatch):
    """Fallback to zeros when psutil is unavailable."""
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError()
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setitem(sys.modules, "psutil", None)
    cpu, mem = _get_usage()
    assert cpu == 0.0
    assert mem == 0.0


def test_get_usage_handles_runtime_errors(monkeypatch):
    class FakeProcess:
        def memory_info(self):
            raise RuntimeError("boom")

    def cpu_percent(interval=None):
        raise RuntimeError("nope")

    fake_psutil = types.SimpleNamespace(
        cpu_percent=cpu_percent,
        Process=lambda: FakeProcess(),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    cpu, mem = _get_usage()
    assert cpu == 0.0
    assert mem == 0.0


def test_get_usage_normalizes_iterable_values(monkeypatch):
    class FakeProcess:
        def memory_info(self):
            return types.SimpleNamespace(rss=[2097152])

    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: ["12.5"],
        Process=lambda: FakeProcess(),
    )

    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    cpu, mem = _get_usage()
    assert cpu == 12.5
    assert mem == 2.0
