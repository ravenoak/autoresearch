import builtins
import pytest

from autoresearch.distributed.broker import get_message_broker


@pytest.mark.requires_distributed
def test_redis_broker_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate missing redis package when requesting Redis broker."""
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "redis":
            raise ModuleNotFoundError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ModuleNotFoundError):
        get_message_broker("redis")
