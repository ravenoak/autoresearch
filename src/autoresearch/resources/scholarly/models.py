"""Typed data structures for scholarly paper ingestion and caching."""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, SupportsFloat

from ...storage_typing import JSONDict, ensure_mutable_mapping, to_json_dict

_NAMESPACE_PATTERN = re.compile(r"[^a-z0-9_-]+")
_IDENTIFIER_PATTERN = re.compile(r"[^a-z0-9_.-]+", re.IGNORECASE)
_DOI_PREFIX = re.compile(r"^https?://(?:dx\.)?doi\.org/", re.IGNORECASE)


def _normalise_namespace(value: str) -> str:
    token = value.strip().lower()
    token = _NAMESPACE_PATTERN.sub("-", token)
    token = token.strip("-") or "default"
    return token[:64]


def _normalise_identifier(value: str) -> str:
    token = value.strip()
    token = _IDENTIFIER_PATTERN.sub("_", token)
    token = token.strip("_") or "resource"
    return token[:128]


@dataclass(slots=True)
class PaperIdentifier:
    """Unique identifier for a scholarly paper within a namespace."""

    provider: str
    value: str
    namespace: str

    def filename_stem(self) -> str:
        """Return a deterministic filename stem for cache artifacts."""

        ns = _normalise_namespace(self.namespace)
        identifier = _normalise_identifier(self.value)
        return f"{ns}__{identifier}"[:180]

    def as_dict(self) -> JSONDict:
        """Serialise the identifier for storage payloads."""

        return {
            "provider": self.provider,
            "value": self.value,
            "namespace": self.namespace,
        }


@dataclass(slots=True)
class PaperProvenance:
    """Captured provenance metadata for cached scholarly content."""

    source_url: str
    retrieved_at: float
    checksum: str
    content_type: str | None = None
    version: str | None = None
    latency_ms: float | None = None
    provider_version: str | None = None

    def to_payload(self) -> JSONDict:
        """Return a JSON-compatible mapping."""

        payload: JSONDict = {
            "source_url": self.source_url,
            "retrieved_at": float(self.retrieved_at),
            "checksum": self.checksum,
        }
        if self.content_type is not None:
            payload["content_type"] = self.content_type
        if self.version is not None:
            payload["version"] = self.version
        if self.latency_ms is not None:
            payload["latency_ms"] = float(self.latency_ms)
        if self.provider_version is not None:
            payload["provider_version"] = self.provider_version
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PaperProvenance":
        """Construct a provenance record from persisted data."""

        data = to_json_dict(payload)
        latency_raw = data.get("latency_ms")
        latency_value: float | None = None
        if latency_raw:
            with suppress(TypeError, ValueError):
                latency_value = float(latency_raw)
        return cls(
            source_url=str(data.get("source_url", "")),
            retrieved_at=float(data.get("retrieved_at", 0.0)),
            checksum=str(data.get("checksum", "")),
            content_type=str(data.get("content_type")) if data.get("content_type") else None,
            version=str(data.get("version")) if data.get("version") else None,
            latency_ms=latency_value,
            provider_version=str(data.get("provider_version"))
            if data.get("provider_version")
            else None,
        )


@dataclass(slots=True)
class PaperMetadata:
    """Core bibliographic metadata for a scholarly paper."""

    identifier: PaperIdentifier
    title: str
    abstract: str
    authors: tuple[str, ...] = field(default_factory=tuple)
    published: datetime | None = None
    primary_url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    subjects: tuple[str, ...] = field(default_factory=tuple)

    def primary_key(self) -> str:
        """Return the canonical identifier string."""

        if self.doi:
            return self.doi
        if self.arxiv_id:
            return self.arxiv_id
        return self.identifier.value

    def with_namespace(self, namespace: str) -> "PaperMetadata":
        """Return a copy of the metadata bound to ``namespace``."""

        identifier = PaperIdentifier(
            provider=self.identifier.provider,
            value=self.identifier.value,
            namespace=namespace,
        )
        return PaperMetadata(
            identifier=identifier,
            title=self.title,
            abstract=self.abstract,
            authors=self.authors,
            published=self.published,
            primary_url=self.primary_url,
            doi=self.doi,
            arxiv_id=self.arxiv_id,
            tags=self.tags,
            subjects=self.subjects,
        )

    def to_payload(self) -> JSONDict:
        """Serialise metadata to a JSON-compatible mapping."""

        payload: JSONDict = {
            "identifier": self.identifier.as_dict(),
            "title": self.title,
            "abstract": self.abstract,
            "authors": list(self.authors),
            "tags": list(self.tags),
        }
        if self.published is not None:
            payload["published"] = self.published.isoformat()
        if self.primary_url is not None:
            payload["primary_url"] = self.primary_url
        if self.doi is not None:
            payload["doi"] = self.doi
        if self.arxiv_id is not None:
            payload["arxiv_id"] = self.arxiv_id
        if self.subjects:
            payload["subjects"] = list(self.subjects)
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PaperMetadata":
        """Rehydrate metadata from stored JSON."""

        data = to_json_dict(payload)
        identifier_payload = ensure_mutable_mapping(data.get("identifier", {}))
        identifier = PaperIdentifier(
            provider=str(identifier_payload.get("provider", "")),
            value=str(identifier_payload.get("value", "")),
            namespace=str(identifier_payload.get("namespace", "")),
        )
        published_raw = data.get("published")
        published_dt = None
        if isinstance(published_raw, str) and published_raw:
            try:
                published_dt = datetime.fromisoformat(published_raw)
            except ValueError:
                published_dt = None
        authors_payload = data.get("authors") or []
        tags_payload = data.get("tags") or []
        return cls(
            identifier=identifier,
            title=str(data.get("title", "")),
            abstract=str(data.get("abstract", "")),
            authors=tuple(str(author) for author in authors_payload),
            tags=tuple(str(tag) for tag in tags_payload),
            published=published_dt,
            primary_url=str(data.get("primary_url")) if data.get("primary_url") else None,
            doi=str(data.get("doi")) if data.get("doi") else None,
            arxiv_id=str(data.get("arxiv_id")) if data.get("arxiv_id") else None,
            subjects=tuple(str(tag) for tag in data.get("subjects", []) or []),
        )


@dataclass(slots=True)
class PaperDocument:
    """Fetched paper content with metadata and optional embeddings."""

    metadata: PaperMetadata
    body: str
    references: tuple[str, ...] = field(default_factory=tuple)
    embedding: Sequence[SupportsFloat] | None = None
    contents: tuple["PaperContentVariant", ...] = field(default_factory=tuple)
    assets: tuple["PaperAsset", ...] = field(default_factory=tuple)
    provider_version: str | None = None
    retrieval_latency_ms: float | None = None

    def __post_init__(self) -> None:
        if self.embedding is not None and not isinstance(self.embedding, tuple):
            normalised = tuple(float(value) for value in self.embedding)
            self.embedding = normalised
        if not self.contents:
            variant = PaperContentVariant.from_text(
                self.body,
                content_type="text/markdown",
            )
            self.contents = (variant,)
        if not self.body:
            text_variant = next((item for item in self.contents if item.is_textual()), None)
            if text_variant is not None:
                try:
                    self.body = text_variant.data.decode("utf-8")
                except UnicodeDecodeError:
                    self.body = ""

    def checksum(self, content_type: str | None = None) -> str:
        """Return a SHA-256 checksum for the requested content type."""

        if content_type is None:
            content = next((item for item in self.contents if item.is_textual()), None)
        else:
            content = next(
                (item for item in self.contents if item.content_type == content_type),
                None,
            )
        target = content or PaperContentVariant.from_text(self.body)
        return target.checksum()


@dataclass(slots=True)
class PaperContentVariant:
    """Binary representation of a fetched content variant."""

    content_type: str
    data: bytes
    filename: str | None = None
    source_url: str | None = None

    def checksum(self) -> str:
        """Return the SHA-256 checksum for the variant."""

        digest = hashlib.sha256(self.data)
        return digest.hexdigest()

    def is_textual(self) -> bool:
        """Return ``True`` when the content type is text-based."""

        return self.content_type.startswith("text/") or self.content_type == "application/json"

    @classmethod
    def from_text(
        cls,
        content: str,
        *,
        content_type: str = "text/plain",
        filename: str | None = None,
        source_url: str | None = None,
    ) -> "PaperContentVariant":
        """Create a text-based content variant."""

        return cls(
            content_type=content_type,
            data=content.encode("utf-8"),
            filename=filename,
            source_url=source_url,
        )


@dataclass(slots=True)
class PaperAsset:
    """Reference to an external supplementary asset."""

    url: str
    kind: str
    content_type: str | None = None


@dataclass(slots=True)
class CachedContentVariant:
    """Metadata for cached content persisted to disk."""

    content_type: str
    path: Path
    checksum: str

    def to_payload(self) -> JSONDict:
        """Return a JSON payload describing the cached content variant."""

        return {
            "content_type": self.content_type,
            "path": str(self.path),
            "checksum": self.checksum,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "CachedContentVariant":
        """Hydrate cached content metadata from persisted JSON."""

        data = to_json_dict(payload)
        return cls(
            content_type=str(data.get("content_type", "")),
            path=Path(str(data.get("path", ""))),
            checksum=str(data.get("checksum", "")),
        )


@dataclass(slots=True)
class CachedPaper:
    """Persisted paper record combining metadata, provenance, and cache info."""

    metadata: PaperMetadata
    provenance: PaperProvenance
    cache_path: Path
    references: tuple[str, ...] = field(default_factory=tuple)
    embedding: tuple[float, ...] | None = None
    contents: tuple[CachedContentVariant, ...] = field(default_factory=tuple)
    assets: tuple[PaperAsset, ...] = field(default_factory=tuple)

    def to_payload(self) -> JSONDict:
        """Return a storage-ready representation of the cached paper."""

        payload: JSONDict = {
            "namespace": self.metadata.identifier.namespace,
            "provider": self.metadata.identifier.provider,
            "paper_id": self.metadata.primary_key(),
            "metadata": self.metadata.to_payload(),
            "provenance": self.provenance.to_payload(),
            "cache_path": str(self.cache_path),
            "references": list(self.references),
        }
        if self.embedding is not None:
            payload["embedding"] = list(self.embedding)
        if self.contents:
            payload["contents"] = [item.to_payload() for item in self.contents]
        if self.assets:
            payload["assets"] = [
                {
                    "url": asset.url,
                    "kind": asset.kind,
                    "content_type": asset.content_type,
                }
                for asset in self.assets
            ]
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "CachedPaper":
        """Create a cached paper from persisted JSON payload."""

        data = to_json_dict(payload)
        metadata_raw = ensure_mutable_mapping(data.get("metadata", {}))
        provenance_raw = ensure_mutable_mapping(data.get("provenance", {}))
        metadata = PaperMetadata.from_payload(metadata_raw)
        provenance = PaperProvenance.from_payload(provenance_raw)
        cache_path = Path(str(data.get("cache_path", "")))
        references_raw = data.get("references") or []
        embedding_raw = data.get("embedding")
        embedding: tuple[float, ...] | None = None
        if isinstance(embedding_raw, Iterable):
            embedding = tuple(float(value) for value in embedding_raw)
        contents_payload = data.get("contents") or []
        contents: list[CachedContentVariant] = []
        if isinstance(contents_payload, Iterable):
            for item in contents_payload:
                if isinstance(item, Mapping):
                    contents.append(CachedContentVariant.from_payload(item))
        assets_payload = data.get("assets") or []
        assets: list[PaperAsset] = []
        if isinstance(assets_payload, Iterable):
            for asset in assets_payload:
                if isinstance(asset, Mapping):
                    assets.append(
                        PaperAsset(
                            url=str(asset.get("url", "")),
                            kind=str(asset.get("kind", "")),
                            content_type=str(asset.get("content_type"))
                            if asset.get("content_type")
                            else None,
                        )
                    )
        return cls(
            metadata=metadata,
            provenance=provenance,
            cache_path=cache_path,
            references=tuple(str(ref) for ref in references_raw),
            embedding=embedding,
            contents=tuple(contents),
            assets=tuple(assets),
        )

    def serialise_cache_document(self) -> JSONDict:
        """Return the JSON payload written alongside cached content."""

        payload = self.to_payload()
        body_payload: JSONDict = {
            "body_path": str(self.cache_path),
            "metadata": payload["metadata"],
            "provenance": payload["provenance"],
            "references": payload.get("references", []),
        }
        if self.embedding is not None:
            body_payload["embedding"] = list(self.embedding)
        if self.contents:
            body_payload["contents"] = [item.to_payload() for item in self.contents]
        if self.assets:
            body_payload["assets"] = [
                {
                    "url": asset.url,
                    "kind": asset.kind,
                    "content_type": asset.content_type,
                }
                for asset in self.assets
            ]
        return body_payload


def dump_cache_document(path: Path, body: str, metadata: CachedPaper) -> None:
    """Write cached document content and metadata to disk."""

    path.write_text(body, encoding="utf-8")
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    meta_payload = metadata.serialise_cache_document()
    meta_path.write_text(json.dumps(meta_payload, indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "PaperIdentifier",
    "PaperProvenance",
    "PaperMetadata",
    "PaperDocument",
    "PaperContentVariant",
    "PaperAsset",
    "CachedContentVariant",
    "CachedPaper",
    "dump_cache_document",
    "normalise_doi",
    "normalise_subjects",
]


def normalise_doi(value: str | None) -> str | None:
    """Return a canonical DOI string or ``None`` when not provided."""

    if not value:
        return None
    token = value.strip()
    if not token:
        return None
    token = _DOI_PREFIX.sub("", token)
    token = token.lower()
    return token or None


def normalise_subjects(values: Iterable[str] | None) -> tuple[str, ...]:
    """Return normalised subject tokens preserving insertion order."""

    seen: set[str] = set()
    subjects: list[str] = []
    if not values:
        return tuple()
    for raw in values:
        token = str(raw).strip()
        if not token:
            continue
        canonical = token.lower()
        if canonical in seen:
            continue
        seen.add(canonical)
        subjects.append(canonical)
    return tuple(subjects)
