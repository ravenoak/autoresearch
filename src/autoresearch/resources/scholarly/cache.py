"""Filesystem-backed cache for scholarly content integrated with storage."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from ...config.loader import ConfigLoader
from ...storage import StorageManager
from ...storage_utils import canonical_namespace
from .models import (
    CachedPaper,
    PaperDocument,
    PaperMetadata,
    PaperProvenance,
)


class CacheValidationError(RuntimeError):
    """Raised when cached content fails checksum verification."""


class ScholarlyCache:
    """Persist scholarly papers to disk and DuckDB storage."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir

    def _base_path(self) -> Path:
        if self._base_dir is not None:
            return self._base_dir
        cfg = ConfigLoader().config.storage
        duckdb_path = Path(cfg.duckdb_path).expanduser()
        root = duckdb_path.parent if duckdb_path.parent != Path("") else Path.cwd()
        return (root / "scholarly_cache").resolve()

    def _resolve_path(self, metadata: PaperMetadata) -> Path:
        base = self._base_path()
        identifier = metadata.identifier
        cache_dir = base / identifier.provider
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{identifier.filename_stem()}.md"

    def cache_document(
        self,
        document: PaperDocument,
        *,
        namespace: str,
        content_type: str = "text/plain",
    ) -> CachedPaper:
        """Persist *document* within ``namespace`` and record provenance."""

        StorageManager.setup()
        resolved_namespace = canonical_namespace(namespace)
        metadata = document.metadata.with_namespace(resolved_namespace)
        checksum = document.checksum()
        cache_path = self._resolve_path(metadata)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            existing_body = cache_path.read_text(encoding="utf-8")
            existing_checksum = hashlib.sha256(existing_body.encode("utf-8", "ignore")).hexdigest()
            if existing_checksum != checksum:
                raise CacheValidationError(
                    "Cached content checksum mismatch for paper",  # pragma: no cover - defensive
                )
        provenance = PaperProvenance(
            source_url=metadata.primary_url or metadata.identifier.value,
            retrieved_at=time.time(),
            checksum=checksum,
            content_type=content_type,
        )
        cached = CachedPaper(
            metadata=metadata,
            provenance=provenance,
            cache_path=cache_path,
            references=document.references,
            embedding=tuple(float(v) for v in document.embedding) if document.embedding else None,
        )
        cache_path.write_text(document.body, encoding="utf-8")
        meta_path = cache_path.with_suffix(".meta.json")
        meta_payload = cached.serialise_cache_document()
        meta_path.write_text(json.dumps(meta_payload, indent=2, sort_keys=True), encoding="utf-8")
        StorageManager.save_scholarly_paper(cached.to_payload())
        return cached

    def list_cached(
        self,
        *,
        namespace: str | None = None,
        provider: str | None = None,
    ) -> list[CachedPaper]:
        """Return cached papers optionally filtered by namespace/provider."""

        StorageManager.setup()
        payloads = StorageManager.list_scholarly_papers(namespace=namespace, provider=provider)
        return [CachedPaper.from_payload(item) for item in payloads]

    def get_cached(self, namespace: str, provider: str, paper_id: str) -> CachedPaper:
        """Return a cached paper, raising if it is absent."""

        StorageManager.setup()
        payload = StorageManager.get_scholarly_paper(namespace, provider, paper_id)
        return CachedPaper.from_payload(payload)


__all__ = ["ScholarlyCache", "CacheValidationError"]
