import pytest
from autoresearch.search.context import SearchContext


@pytest.mark.requires_nlp
def test_extract_entities_without_spacy():
    """Fallback tokenization should count entities without spaCy."""
    with SearchContext.temporary_instance() as ctx:
        ctx._extract_entities("Alice and Bob")
        assert ctx.entities["alice"] == 1
        assert ctx.entities["bob"] == 1
