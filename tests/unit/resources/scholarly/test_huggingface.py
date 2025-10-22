from __future__ import annotations

import httpx

from autoresearch.resources.scholarly.fetchers import HuggingFacePapersFetcher


def test_huggingface_search_handles_results(httpx_mock) -> None:
    payload = {
        "results": [
            {
                "paperId": "hf-paper-1",
                "title": "Neural Architectures",
                "abstract": "Summary text.",
                "authors": ["Jane Doe", {"name": "John Smith"}],
                "publishedAt": "2024-03-05T00:00:00Z",
                "doi": "10.5555/xyz",
                "tags": ["ML", "Transformers"],
            }
        ]
    }
    httpx_mock.add_callback(
        lambda request: httpx.Response(200, json=payload),
        url=str(
            httpx.URL(
                "https://huggingface.co/api/papers/search",
                params={"q": "neural", "limit": "1"},
            )
        ),
    )
    fetcher = HuggingFacePapersFetcher()
    results = fetcher.search("neural", limit=1)
    assert len(results) == 1
    metadata = results[0]
    assert metadata.title == "Neural Architectures"
    assert metadata.authors == ("Jane Doe", "John Smith")
    assert metadata.doi == "10.5555/xyz"
    assert metadata.subjects == ("ml", "transformers")


def test_huggingface_fetch_returns_document(httpx_mock) -> None:
    payload = {
        "paperId": "hf-paper-2",
        "title": "Transformer Advances",
        "abstract": "Highlights",
        "content": "Full content",
        "authors": ["A. Expert"],
        "url": "https://huggingface.co/papers/hf-paper-2",
        "references": ["https://doi.org/10.1/example"],
        "pdfUrl": "https://huggingface.co/papers/hf-paper-2.pdf",
        "supplementaryUrls": ["https://huggingface.co/papers/hf-paper-2-supplement.txt"],
        "embedding": [0.1, 0.2, 0.3],
    }
    httpx_mock.add_callback(
        lambda request: httpx.Response(200, json=payload),
        url=httpx.URL("https://huggingface.co/api/papers/hf-paper-2"),
    )
    httpx_mock.add_response(
        url="https://huggingface.co/papers/hf-paper-2.pdf",
        content=b"%PDF-1.7",
        headers={"Content-Type": "application/pdf"},
    )
    fetcher = HuggingFacePapersFetcher()
    document = fetcher.fetch("hf-paper-2")
    assert document.metadata.title == "Transformer Advances"
    assert document.body == "Full content"
    assert document.references == ("https://doi.org/10.1/example",)
    content_types = {variant.content_type for variant in document.contents}
    assert "application/pdf" in content_types
    assert document.embedding == (0.1, 0.2, 0.3)
    assert document.assets
