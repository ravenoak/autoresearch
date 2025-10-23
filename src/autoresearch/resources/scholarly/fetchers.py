"""Provider fetchers for scholarly metadata and content."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Sequence

from .client import get_http_client
from .models import PaperDocument, PaperIdentifier, PaperMetadata

_DEFAULT_NAMESPACE = "__public__"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


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


class ArxivFetcher(ScholarlyFetcher):
    """Interact with the arXiv Atom feed to retrieve papers."""

    provider = "arxiv"
    _SEARCH_URL = "https://export.arxiv.org/api/query"

    def _metadata_from_entry(self, entry: ET.Element, namespace: str) -> PaperMetadata:
        id_text = entry.findtext("atom:id", namespaces=_ATOM_NS) or ""
        title = (entry.findtext("atom:title", namespaces=_ATOM_NS) or "").strip()
        summary = (entry.findtext("atom:summary", namespaces=_ATOM_NS) or "").strip()
        published = _parse_timestamp(entry.findtext("atom:published", namespaces=_ATOM_NS))
        doi = entry.findtext("arxiv:doi", namespaces=_ATOM_NS)
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
        primary_url = id_text or None
        tags = [
            cat.attrib.get("term", "")
            for cat in entry.findall("atom:category", namespaces=_ATOM_NS)
            if cat.attrib.get("term")
        ]
        return PaperMetadata(
            identifier=identifier,
            title=title,
            abstract=summary,
            authors=tuple(author for author in authors if author),
            published=published,
            primary_url=primary_url,
            doi=doi,
            arxiv_id=arxiv_id,
            tags=tuple(tag for tag in tags if tag),
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> Sequence[PaperMetadata]:
        client = get_http_client()
        params = {"search_query": f"all:{query}", "max_results": str(limit), "start": "0"}
        response = client.get(self._SEARCH_URL, params=params)
        response.raise_for_status()
        tree = ET.fromstring(response.text)
        entries = tree.findall("atom:entry", namespaces=_ATOM_NS)
        target_namespace = namespace or _DEFAULT_NAMESPACE
        return [self._metadata_from_entry(entry, target_namespace) for entry in entries]

    def fetch(self, identifier: str) -> PaperDocument:
        client = get_http_client()
        params = {"id_list": identifier}
        response = client.get(self._SEARCH_URL, params=params)
        response.raise_for_status()
        tree = ET.fromstring(response.text)
        entry = tree.find("atom:entry", namespaces=_ATOM_NS)
        if entry is None:
            raise ValueError(f"arXiv identifier '{identifier}' not found")
        metadata = self._metadata_from_entry(entry, _DEFAULT_NAMESPACE)
        links = [
            link.attrib.get("href")
            for link in entry.findall("atom:link", namespaces=_ATOM_NS)
            if link.attrib.get("href")
        ]
        references: tuple[str, ...] = tuple(link for link in links if link)
        document = PaperDocument(metadata=metadata, body=metadata.abstract, references=references)
        return document


class HuggingFacePapersFetcher(ScholarlyFetcher):
    """Fetch scholarly papers indexed by Hugging Face."""

    provider = "huggingface"
    _BASE_URL = "https://huggingface.co/api/papers"

    def _metadata_from_payload(self, payload: dict[str, object], namespace: str) -> PaperMetadata:
        identifier_value = str(payload.get("paperId") or payload.get("id") or payload.get("slug") or "")
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
                str(author.get("name") if isinstance(author, dict) else author).strip()
                for author in authors_raw
            ]
        else:
            authors = []
        published = _parse_timestamp(str(payload.get("publishedAt") or payload.get("published") or ""))
        primary_url = str(payload.get("url") or payload.get("homepage") or "").strip() or None
        doi_value = payload.get("doi")
        arxiv_value = payload.get("arxivId") or payload.get("arxiv_id")
        tags_payload = payload.get("tags") or []
        tags: list[str] = []
        if isinstance(tags_payload, Iterable):
            for tag in tags_payload:
                tags.append(str(tag))
        return PaperMetadata(
            identifier=identifier,
            title=title,
            abstract=abstract,
            authors=tuple(author for author in authors if author),
            published=published,
            primary_url=primary_url,
            doi=str(doi_value) if doi_value else None,
            arxiv_id=str(arxiv_value) if arxiv_value else None,
            tags=tuple(tag for tag in tags if tag),
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
    ) -> Sequence[PaperMetadata]:
        client = get_http_client()
        params = {"q": query, "limit": limit}
        response = client.get(f"{self._BASE_URL}/search", params=params)  # type: ignore[arg-type]
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") if isinstance(payload, dict) else None
        if results is None:
            if isinstance(payload, list):
                results = payload
            else:
                results = []
        target_namespace = namespace or _DEFAULT_NAMESPACE
        return [self._metadata_from_payload(item, target_namespace) for item in results]

    def fetch(self, identifier: str) -> PaperDocument:
        client = get_http_client()
        response = client.get(f"{self._BASE_URL}/{identifier}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected payload from Hugging Face Papers API")
        metadata = self._metadata_from_payload(payload, _DEFAULT_NAMESPACE)
        references_payload = payload.get("references") or []
        references: list[str] = []
        if isinstance(references_payload, Iterable):
            for ref in references_payload:
                references.append(str(ref))
        body = str(payload.get("content") or payload.get("abstract") or "")
        if not body:
            body = metadata.abstract
        return PaperDocument(
            metadata=metadata,
            body=body,
            references=tuple(references),
        )


__all__ = ["ScholarlyFetcher", "ArxivFetcher", "HuggingFacePapersFetcher"]
