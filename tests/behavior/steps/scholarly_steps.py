from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, parsers, then, when

from autoresearch.resources.scholarly.cache import ScholarlyCache
from autoresearch.resources.scholarly.models import (
    PaperContentVariant,
    PaperDocument,
    PaperIdentifier,
    PaperMetadata,
)
from autoresearch.storage import StorageManager
from tests.behavior.context import BehaviorContext, get_required, set_value


def _ensure_namespace() -> str:
    default_namespace, _, _ = StorageManager._namespace_settings()
    return default_namespace


@given(parsers.parse('I fetch the paper "{title}" from Hugging Face Papers'))
def fetch_paper_fixture(
    title: str,
    bdd_context: BehaviorContext,
    tmp_path: Path,
) -> None:
    namespace = _ensure_namespace()
    cache = ScholarlyCache(base_dir=tmp_path / "scholarly_cache")
    identifier = PaperIdentifier(provider="huggingface", value=title.lower().replace(" ", "-"), namespace=namespace)
    metadata = PaperMetadata(
        identifier=identifier,
        title=title,
        abstract="Cached abstract",
        authors=("Research Assistant",),
    )
    text_variant = PaperContentVariant.from_text(
        "Cached abstract",
        content_type="text/markdown",
    )
    pdf_variant = PaperContentVariant(
        content_type="application/pdf",
        data=b"%PDF-1.7",
        filename="self-query-retrieval.pdf",
        source_url="https://huggingface.co/papers/self-query-retrieval.pdf",
    )
    document = PaperDocument(
        metadata=metadata,
        body="Cached abstract",
        contents=(text_variant, pdf_variant),
        provider_version="behavioral-test",
        retrieval_latency_ms=3.2,
    )
    cached = cache.cache_document(document, namespace=namespace)
    set_value(bdd_context, "cached_paper", cached)
    set_value(bdd_context, "scholarly_cache", cache)
    set_value(bdd_context, "workspace_namespace", namespace)


@given('the fetch is cached locally with checksum metadata')
def assert_cache_metadata(bdd_context: BehaviorContext) -> None:
    cached = get_required(bdd_context, "cached_paper")
    assert cached.cache_path.exists()
    provenance = cached.provenance
    assert provenance.checksum
    assert provenance.retrieved_at > 0
    assert provenance.provider_version == "behavioral-test"


@when('I disconnect from the network')
def simulate_offline(bdd_context: BehaviorContext) -> None:
    set_value(bdd_context, "offline_mode", True)


@when(parsers.parse('I ask "{question}" within the same workspace'))
def load_cached_content(question: str, bdd_context: BehaviorContext) -> None:
    cache = get_required(bdd_context, "scholarly_cache")
    namespace = get_required(bdd_context, "workspace_namespace", str)
    results = cache.list_cached(namespace=namespace)
    set_value(bdd_context, "cached_results", results)
    set_value(bdd_context, "offline_question", question)


@then('the agent cites the cached paper content with preserved provenance')
def verify_cached_result(bdd_context: BehaviorContext) -> None:
    results = get_required(bdd_context, "cached_results")
    assert results, "Expected cached results to be available"
    cached = results[0]
    original = get_required(bdd_context, "cached_paper")
    assert cached.metadata.title == original.metadata.title
    assert cached.provenance.checksum == original.provenance.checksum
    assert {item.content_type for item in cached.contents} == {"text/markdown", "application/pdf"}


@then('the cache metadata reports the last sync timestamp')
def verify_cache_timestamp(bdd_context: BehaviorContext) -> None:
    cached = get_required(bdd_context, "cached_paper")
    assert cached.provenance.retrieved_at > 0
    assert cached.provenance.latency_ms == 3.2
