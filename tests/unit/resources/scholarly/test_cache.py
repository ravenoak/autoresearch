from __future__ import annotations

from pathlib import Path

import pytest

from autoresearch.resources.scholarly.cache import ScholarlyCache
from autoresearch.resources.scholarly.models import (
    PaperDocument,
    PaperIdentifier,
    PaperMetadata,
)
from autoresearch.storage import StorageContext, StorageManager, StorageState


@pytest.fixture()
def storage_state(tmp_path: Path) -> tuple[StorageContext, StorageState]:
    context = StorageContext()
    state = StorageState(context=context)
    db_path = tmp_path / "scholarly.duckdb"
    StorageManager.setup(db_path=str(db_path), context=context, state=state)
    yield context, state
    StorageManager.teardown(remove_db=True, context=context, state=state)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()


def _make_document() -> PaperDocument:
    identifier = PaperIdentifier(provider="arxiv", value="1234.5678", namespace="workspace-alpha")
    metadata = PaperMetadata(
        identifier=identifier,
        title="Cached Paper",
        abstract="Body text",
        authors=("Analyst",),
    )
    return PaperDocument(metadata=metadata, body="Body text")


def test_cache_persists_metadata(tmp_path: Path, storage_state) -> None:
    cache = ScholarlyCache(base_dir=tmp_path / "cache")
    document = _make_document()
    cached = cache.cache_document(document, namespace="workspace-alpha")
    assert cached.cache_path.exists()
    payloads = StorageManager.list_scholarly_papers(namespace="workspace-alpha")
    assert len(payloads) == 1
    assert payloads[0]["paper_id"] == document.metadata.primary_key()

    cached_again = cache.cache_document(document, namespace="workspace-alpha")
    assert cached_again.cache_path == cached.cache_path

    listed = cache.list_cached(namespace="workspace-alpha")
    assert len(listed) == 1
    assert listed[0].metadata.title == "Cached Paper"
