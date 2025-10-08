# mypy: ignore-errors
import importlib
import pytest


@pytest.mark.requires_gpu
def test_try_import_bertopic_success(monkeypatch):
    """_try_import_bertopic should return True when dependency is available."""
    from autoresearch.search import context

    # Reset the module state
    monkeypatch.setattr(context, "BERTopic", None)
    monkeypatch.setattr(context, "BERTOPIC_AVAILABLE", False)
    importlib.reload(context)

    # Since gpu extra is installed, BERTopic should be importable
    assert context._try_import_bertopic() is True
