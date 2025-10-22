"""Filesystem-backed cache for scholarly content integrated with storage."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Mapping

from ...config.loader import ConfigLoader
from ...storage import StorageManager
from ...storage_utils import NamespaceTokens
from .models import (
    CachedContentVariant,
    CachedPaper,
    PaperContentVariant,
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
        namespace: NamespaceTokens | Mapping[str, str] | str,
        content_type: str = "text/markdown",
    ) -> CachedPaper:
        """Persist *document* within ``namespace`` and record provenance."""

        StorageManager.setup()
        resolved_namespace = StorageManager._resolve_namespace_label(namespace)
        metadata = document.metadata.with_namespace(resolved_namespace)
        base_path = self._resolve_path(metadata)
        cache_dir = base_path.parent
        cache_dir.mkdir(parents=True, exist_ok=True)

        def _variant_suffix(variant: PaperContentVariant) -> str:
            if variant.content_type == "text/markdown":
                return ".md"
            if variant.content_type == "text/html":
                return ".html"
            if variant.content_type == "application/pdf":
                return ".pdf"
            subtype = variant.content_type.split("/", 1)[-1] if variant.content_type else "bin"
            return f".{subtype or 'bin'}"

        def _write_variant(variant: PaperContentVariant, target_path: Path) -> CachedContentVariant:
            checksum = variant.checksum()
            if target_path.exists():
                if variant.is_textual():
                    existing_bytes = target_path.read_text(encoding="utf-8").encode("utf-8")
                else:
                    existing_bytes = target_path.read_bytes()
                existing_checksum = hashlib.sha256(existing_bytes).hexdigest()
                if existing_checksum != checksum:
                    raise CacheValidationError(
                        "Cached content checksum mismatch for paper variant",
                    )
            else:
                if variant.is_textual():
                    target_path.write_text(
                        variant.data.decode("utf-8", "ignore"),
                        encoding="utf-8",
                    )
                else:
                    target_path.write_bytes(variant.data)
            return CachedContentVariant(
                content_type=variant.content_type,
                path=target_path,
                checksum=checksum,
            )

        stem = metadata.identifier.filename_stem()
        variants = list(document.contents or ())
        if not variants:
            fallback_variant = PaperContentVariant.from_text(
                document.body,
                content_type=content_type,
            )
            if fallback_variant.filename is None:
                fallback_variant.filename = f"{stem}{_variant_suffix(fallback_variant)}"
            variants.append(fallback_variant)
        textual_variant = next((item for item in variants if item.is_textual()), None)
        if textual_variant is None:
            textual_variant = PaperContentVariant.from_text(
                document.body,
                content_type=content_type,
            )
            textual_variant.filename = f"{stem}{_variant_suffix(textual_variant)}"
            variants.insert(0, textual_variant)

        cached_variants: list[CachedContentVariant] = []
        for variant in variants:
            filename = variant.filename or f"{stem}{_variant_suffix(variant)}"
            safe_name = Path(filename).name
            target_path = cache_dir / safe_name
            cached_variants.append(_write_variant(variant, target_path))

        candidate_paths = (
            item.path
            for item in cached_variants
            if item.content_type == textual_variant.content_type
        )
        text_path = next(
            candidate_paths,
            cache_dir / (textual_variant.filename or base_path.name),
        )
        checksum = textual_variant.checksum()
        provenance = PaperProvenance(
            source_url=metadata.primary_url or metadata.identifier.value,
            retrieved_at=time.time(),
            checksum=checksum,
            content_type=textual_variant.content_type,
            version=document.provider_version,
            latency_ms=document.retrieval_latency_ms,
            provider_version=document.provider_version,
        )
        cached = CachedPaper(
            metadata=metadata,
            provenance=provenance,
            cache_path=text_path,
            references=document.references,
            embedding=tuple(float(v) for v in document.embedding) if document.embedding else None,
            contents=tuple(cached_variants),
            assets=document.assets,
        )
        meta_path = text_path.with_suffix(text_path.suffix + ".meta.json")
        meta_payload = cached.serialise_cache_document()
        meta_path.write_text(json.dumps(meta_payload, indent=2, sort_keys=True), encoding="utf-8")
        StorageManager.save_scholarly_paper(cached.to_payload())
        return cached

    def list_cached(
        self,
        *,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
        provider: str | None = None,
    ) -> list[CachedPaper]:
        """Return cached papers optionally filtered by namespace/provider."""

        StorageManager.setup()
        payloads = StorageManager.list_scholarly_papers(namespace=namespace, provider=provider)
        return [CachedPaper.from_payload(item) for item in payloads]

    def get_cached(
        self,
        namespace: NamespaceTokens | Mapping[str, str] | str,
        provider: str,
        paper_id: str,
    ) -> CachedPaper:
        """Return a cached paper, raising if it is absent."""

        StorageManager.setup()
        payload = StorageManager.get_scholarly_paper(namespace, provider, paper_id)
        return CachedPaper.from_payload(payload)


__all__ = ["ScholarlyCache", "CacheValidationError"]
