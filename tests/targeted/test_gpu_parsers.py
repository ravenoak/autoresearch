from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

import pytest

try:
    from tests.optional_imports import import_or_skip
except Exception:  # pragma: no cover - path fallback for --noconftest runs
    import importlib.util

    _mod_path = Path(__file__).resolve().parents[1] / "optional_imports.py"
    spec = importlib.util.spec_from_file_location("tests.optional_imports", str(_mod_path))
    if spec and spec.loader:
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
        import_or_skip = getattr(_mod, "import_or_skip")
    else:  # pragma: no cover - defensive fallback
        raise ModuleNotFoundError(
            "Could not import tests.optional_imports via direct path fallback"
        )

from tests.typing_helpers import TypedFixture


@pytest.fixture
def stub_bertopic_module(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[ModuleType]:
    """Provide a stub BERTopic module and restore ``sys.modules`` afterward."""

    stub = ModuleType("bertopic")

    class _StubBERTopic:  # pragma: no cover - simple container
        pass

    setattr(stub, "BERTopic", _StubBERTopic)
    monkeypatch.setitem(sys.modules, "bertopic", stub)
    return stub


@pytest.fixture
def reset_bertopic_state(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[ModuleType]:
    """Reset ``context`` globals before and after a BERTopic import test."""

    from autoresearch.search import context

    monkeypatch.setattr(context, "BERTopic", None)
    monkeypatch.setattr(context, "BERTOPIC_AVAILABLE", False)
    return context


@pytest.mark.requires_gpu
def test_bertopic_integration(
    monkeypatch: pytest.MonkeyPatch,
    stub_bertopic_module: ModuleType,
    reset_bertopic_state: ModuleType,
) -> None:
    """BERTopic integration activates when GPU extras are available."""

    context = reset_bertopic_state
    monkeypatch.setattr(
        context,
        "get_config",
        lambda: SimpleNamespace(
            search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True))
        ),
    )

    assert context._try_import_bertopic() is True
    assert context.BERTopic is stub_bertopic_module.BERTopic
    assert context.BERTOPIC_AVAILABLE is True

    # Second call should be a no-op while still reporting success.
    assert context._try_import_bertopic() is True
    assert context.BERTopic is stub_bertopic_module.BERTopic
    assert context.BERTOPIC_AVAILABLE is True


@pytest.mark.requires_parsers
def test_docx_backend_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local file backend indexes DOCX files when parsers extras are installed."""

    docx = import_or_skip("docx")
    from autoresearch.search import core

    doc_path = tmp_path / "example.docx"
    document = docx.Document()
    if not hasattr(document, "add_paragraph"):
        pytest.skip("docx package lacks add_paragraph")
    seed_text = "hello world"
    document.add_paragraph(seed_text)
    document.save(doc_path)

    consumed = False

    class TrackingParagraphs(list[SimpleNamespace]):
        def __iter__(self) -> Iterator[SimpleNamespace]:  # pragma: no cover - simple flag update
            nonlocal consumed
            consumed = True
            return super().__iter__()

    class StubDocument:
        def __init__(self, path: str) -> None:
            assert path == str(doc_path)
            self.paragraphs = TrackingParagraphs([SimpleNamespace(text=seed_text)])

    cfg = SimpleNamespace(
        search=SimpleNamespace(
            local_file=SimpleNamespace(path=str(tmp_path), file_types=["docx"])
        )
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Document", StubDocument)

    results = core._local_file_backend("hello", 1)
    assert results and results[0]["title"] == "example.docx"
    assert seed_text in results[0]["snippet"]
    assert consumed
