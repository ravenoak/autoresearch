from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from autoresearch.api.routing import create_app
from autoresearch.storage import StorageManager


class DummyContext:
    def __init__(self) -> None:
        self.entered = False
        self.exited = False

    def __enter__(self) -> "DummyContext":
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.exited = True


class DummyLoader:
    def __init__(self) -> None:
        self.ctx = DummyContext()
        self.stop_watching = MagicMock()

    def watching(self) -> DummyContext:
        return self.ctx


def test_lifespan_startup_shutdown(monkeypatch) -> None:
    loader = DummyLoader()
    setup_mock = MagicMock()
    monkeypatch.setattr(StorageManager, "setup", setup_mock)
    app = create_app(config_loader=loader)

    assert getattr(app.state, "watch_ctx", None) is None

    with TestClient(app):
        assert app.state.watch_ctx is loader.ctx

    assert setup_mock.called
    assert loader.ctx.entered and loader.ctx.exited
    assert loader.stop_watching.called
    assert getattr(app.state, "watch_ctx", None) is None
