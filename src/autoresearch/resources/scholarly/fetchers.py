"""Provider fetchers for scholarly metadata and content."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlparse

import httpx
from tenacity import (  # type: ignore[import-not-found]
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .client import get_http_client
from .models import (
    PaperAsset,
    PaperContentVariant,
    PaperDocument,
    PaperIdentifier,
    PaperMetadata,
    normalise_doi,
    normalise_subjects,
)

_DEFAULT_NAMESPACE = "__public__"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_LOGGER = logging.getLogger(__name__)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


class ScholarlyFetcher(ABC):
    """Abstract base class for scholarly content providers."""

    provider: str
    provider_version: str | None = None
    _RETRY_ATTEMPTS = 3

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> Sequence[PaperMetadata]:
        """Return lightweight metadata for papers matching ``query``."""

    @abstractmethod
    def fetch(self, identifier: str) -> PaperDocument:
        """Return the full paper document for ``identifier``."""

    def _http_get(
        self,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP GET with exponential backoff."""

        client = get_http_client()

        @retry(  # pragma: no cover - retry decorator configuration
            retry=retry_if_exception_type(httpx.HTTPError),
            wait=wait_exponential(multiplier=0.4, min=0.4, max=4.0),
            stop=stop_after_attempt(self._RETRY_ATTEMPTS),
        )
        def _do_request() -> httpx.Response:
            response = client.get(
                url,
                params=dict(params or {}),
                follow_redirects=True,
            )
            response.raise_for_status()
            return response

        return _do_request()

    def _download_content(
        self,
        url: str,
        *,
        expected_type: str | None = None,
    ) -> PaperContentVariant | None:
        """Download *url* and return a cached content variant when available."""

        try:
            response = self._http_get(url)
        except httpx.HTTPError as exc:  # pragma: no cover - network failures
            _LOGGER.warning("Failed to download asset %s: %s", url, exc)
            return None
        content_type = expected_type or response.headers.get("Content-Type", "").split(";")[0]
        if not content_type:
            content_type = expected_type or "application/octet-stream"
        filename = Path(urlparse(url).path).name or None
        if filename and "." not in filename:
            if content_type == "text/html":
                filename = f"{filename}.html"
            elif content_type == "application/pdf":
                filename = f"{filename}.pdf"
            elif content_type.startswith("text/"):
                filename = f"{filename}.txt"
        return PaperContentVariant(
            content_type=content_type,
            data=response.content,
            filename=filename,
            source_url=url,
        )


class ArxivFetcher(ScholarlyFetcher):
    """Interact with the arXiv Atom feed to retrieve papers."""

    provider = "arxiv"
    provider_version = "atom:v1"
    _SEARCH_URL = "https://export.arxiv.org/api/query"

    def _metadata_from_entry(self, entry: ET.Element, namespace: str) -> PaperMetadata:
        id_text = entry.findtext("atom:id", namespaces=_ATOM_NS) or ""
        title = (entry.findtext("atom:title", namespaces=_ATOM_NS) or "").strip()
        summary = (entry.findtext("atom:summary", namespaces=_ATOM_NS) or "").strip()
        published = _parse_timestamp(entry.findtext("atom:published", namespaces=_ATOM_NS))
        doi_raw = entry.findtext("arxiv:doi", namespaces=_ATOM_NS)
        doi = normalise_doi(doi_raw)
        arxiv_id = id_text.rsplit("/", 1)[-1]
        identifier = PaperIdentifier(
            provider=self.provider,
            value=arxiv_id,
            namespace=namespace,
        )
        authors = [
            (author.findtext("atom:name", namespaces=_ATOM_NS) or "").strip()
            for author in entry.findall("atom:author", namespaces=_ATOM_NS)
        ]
        links = list(entry.findall("atom:link", namespaces=_ATOM_NS))
        html_url = next(
            (
                link.attrib.get("href")
                for link in links
                if link.attrib.get("rel") == "alternate" and link.attrib.get("href")
            ),
            id_text or None,
        )
        tags = [
            cat.attrib.get("term", "")
            for cat in entry.findall("atom:category", namespaces=_ATOM_NS)
            if cat.attrib.get("term")
        ]
        subjects = normalise_subjects(tags)
        return PaperMetadata(
            identifier=identifier,
            title=title,
            abstract=summary,
            authors=tuple(author for author in authors if author),
            published=published,
            primary_url=html_url,
            doi=doi,
            arxiv_id=arxiv_id,
            tags=tuple(tag for tag in tags if tag),
            subjects=subjects,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> Sequence[PaperMetadata]:
        params = {"search_query": f"all:{query}", "max_results": str(limit), "start": "0"}
        response = self._http_get(self._SEARCH_URL, params=params)
        tree = ET.fromstring(response.text)
        entries = tree.findall("atom:entry", namespaces=_ATOM_NS)
        target_namespace = namespace or _DEFAULT_NAMESPACE
        return [self._metadata_from_entry(entry, target_namespace) for entry in entries]

    def fetch(self, identifier: str) -> PaperDocument:
        params = {"id_list": identifier}
        start = time.perf_counter()
        response = self._http_get(self._SEARCH_URL, params=params)
        latency_ms = (time.perf_counter() - start) * 1000
        tree = ET.fromstring(response.text)
        entry = tree.find("atom:entry", namespaces=_ATOM_NS)
        if entry is None:
            raise ValueError(f"arXiv identifier '{identifier}' not found")
        metadata = self._metadata_from_entry(entry, _DEFAULT_NAMESPACE)
        references: list[str] = []
        content_variants: list[PaperContentVariant] = [
            PaperContentVariant.from_text(
                metadata.abstract,
                content_type="text/markdown",
                filename=f"{metadata.identifier.value}.md",
                source_url=metadata.primary_url,
            )
        ]
        assets: list[PaperAsset] = []
        for link in entry.findall("atom:link", namespaces=_ATOM_NS):
            href = link.attrib.get("href")
            if not href:
                continue
            references.append(href)
            rel = link.attrib.get("rel") or ""
            link_type = link.attrib.get("type") or ""
            title = (link.attrib.get("title") or "").lower()
            if "pdf" in title or link_type == "application/pdf":
                pdf_variant = self._download_content(
                    href,
                    expected_type="application/pdf",
                )
                if pdf_variant is not None:
                    content_variants.append(pdf_variant)
                else:
                    assets.append(PaperAsset(url=href, kind="pdf", content_type="application/pdf"))
            elif rel == "alternate" and (link_type == "text/html" or not link_type):
                html_variant = self._download_content(href, expected_type="text/html")
                if html_variant is not None:
                    content_variants.append(html_variant)
            else:
                assets.append(PaperAsset(url=href, kind=rel or "link", content_type=link_type or None))
        document = PaperDocument(
            metadata=metadata,
            body=metadata.abstract,
            references=tuple(references),
            contents=tuple(content_variants),
            assets=tuple(assets),
            provider_version=self.provider_version,
            retrieval_latency_ms=latency_ms,
        )
        return document


class HuggingFacePapersFetcher(ScholarlyFetcher):
    """Fetch scholarly papers indexed by Hugging Face."""

    provider = "huggingface"
    provider_version = "papers:v1"
    _BASE_URL = "https://huggingface.co/api/papers"

    def _metadata_from_payload(self, payload: Mapping[str, object], namespace: str) -> PaperMetadata:
        identifier_value = str(
            payload.get("paperId") or payload.get("id") or payload.get("slug") or ""
        )
        identifier = PaperIdentifier(
            provider=self.provider,
            value=identifier_value,
            namespace=namespace,
        )
        abstract = str(payload.get("abstract") or payload.get("summary") or "").strip()
        title = str(payload.get("title") or identifier_value).strip()
        authors_raw = payload.get("authors") or []
        if isinstance(authors_raw, Iterable):
            authors = [
                str(author.get("name") if isinstance(author, Mapping) else author).strip()
                for author in authors_raw
            ]
        else:
            authors = []
        published = _parse_timestamp(str(payload.get("publishedAt") or payload.get("published") or ""))
        primary_url = str(payload.get("url") or payload.get("homepage") or "").strip() or None
        doi = normalise_doi(str(payload.get("doi")) if payload.get("doi") else None)
        arxiv_value = payload.get("arxivId") or payload.get("arxiv_id")
        tags_payload = payload.get("tags") or []
        tags: list[str] = []
        if isinstance(tags_payload, Iterable):
            for tag in tags_payload:
                tags.append(str(tag))
        subjects = normalise_subjects(tags)
        return PaperMetadata(
            identifier=identifier,
            title=title,
            abstract=abstract,
            authors=tuple(author for author in authors if author),
            published=published,
            primary_url=primary_url,
            doi=doi,
            arxiv_id=str(arxiv_value) if arxiv_value else None,
            tags=tuple(tag for tag in tags if tag),
            subjects=subjects,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> Sequence[PaperMetadata]:
        params = {"q": query, "limit": limit}
        response = self._http_get(f"{self._BASE_URL}/search", params=params)
        payload = response.json()
        results = payload.get("results") if isinstance(payload, Mapping) else None
        if results is None:
            if isinstance(payload, list):
                results = payload
            else:
                results = []
        target_namespace = namespace or _DEFAULT_NAMESPACE
        return [self._metadata_from_payload(item, target_namespace) for item in results]

    def _extract_asset_urls(self, payload: Mapping[str, object]) -> list[tuple[str, str | None]]:
        urls: list[tuple[str, str | None]] = []
        for key, value in payload.items():
            if not isinstance(value, (str, list, tuple)):
                continue
            key_lower = str(key).lower()
            if "url" not in key_lower:
                continue
            if isinstance(value, str):
                urls.append((value, key_lower))
            else:
                for item in value:
                    if isinstance(item, Mapping):
                        url_value = item.get("url") or item.get("href")
                        if isinstance(url_value, str):
                            urls.append((url_value, key_lower))
                    elif isinstance(item, str):
                        urls.append((item, key_lower))
        return urls

    def fetch(self, identifier: str) -> PaperDocument:
        start = time.perf_counter()
        response = self._http_get(f"{self._BASE_URL}/{identifier}")
        latency_ms = (time.perf_counter() - start) * 1000
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("Unexpected payload from Hugging Face Papers API")
        metadata = self._metadata_from_payload(payload, _DEFAULT_NAMESPACE)
        references_payload = payload.get("references") or []
        references: list[str] = []
        if isinstance(references_payload, Iterable):
            for ref in references_payload:
                references.append(str(ref))
        body = str(
            payload.get("content")
            or payload.get("contentMarkdown")
            or payload.get("content_markdown")
            or payload.get("abstract")
            or ""
        )
        if not body:
            body = metadata.abstract
        content_variants: list[PaperContentVariant] = [
            PaperContentVariant.from_text(
                body,
                content_type="text/markdown",
                filename=f"{metadata.identifier.value}.md",
                source_url=metadata.primary_url,
            )
        ]
        assets: list[PaperAsset] = []
        for url, key in self._extract_asset_urls(payload):
            url_value = url.strip()
            if not url_value:
                continue
            key_kind = key or "asset"
            if "pdf" in key_kind:
                variant = self._download_content(url_value, expected_type="application/pdf")
                if variant is not None:
                    content_variants.append(variant)
                else:
                    assets.append(PaperAsset(url=url_value, kind="pdf", content_type="application/pdf"))
            elif key_kind.endswith("url") and "html" in key_kind:
                variant = self._download_content(url_value, expected_type="text/html")
                if variant is not None:
                    content_variants.append(variant)
                else:
                    assets.append(PaperAsset(url=url_value, kind="html", content_type="text/html"))
            else:
                assets.append(PaperAsset(url=url_value, kind=key_kind, content_type=None))
        document = PaperDocument(
            metadata=metadata,
            body=body,
            references=tuple(references),
            contents=tuple(content_variants),
            assets=tuple(assets),
            provider_version=self.provider_version,
            retrieval_latency_ms=latency_ms,
        )
        embedding = payload.get("embedding")
        if isinstance(embedding, Iterable):
            try:
                document.embedding = tuple(float(value) for value in embedding)  # type: ignore[attr-defined]
            except (TypeError, ValueError):  # pragma: no cover - defensive coercion
                document.embedding = None  # type: ignore[attr-defined]
        return document


__all__ = ["ScholarlyFetcher", "ArxivFetcher", "HuggingFacePapersFetcher"]
