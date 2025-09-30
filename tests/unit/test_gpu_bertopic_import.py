import importlib
import pytest


@pytest.mark.requires_gpu
def test_try_import_bertopic_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """_try_import_bertopic should return False when dependency is absent."""
    from autoresearch.search import context

    monkeypatch.setattr(context, "BERTopic", None)
    monkeypatch.setattr(context, "BERTOPIC_AVAILABLE", False)
    importlib.reload(context)
    assert context._try_import_bertopic() is False
