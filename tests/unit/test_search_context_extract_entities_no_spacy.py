from types import SimpleNamespace
from unittest.mock import patch

import pytest

from autoresearch.search.context import SearchContext


pytestmark = pytest.mark.requires_nlp


def make_config():
    return SimpleNamespace(
        search=SimpleNamespace(
            context_aware=SimpleNamespace(
                max_history_items=10,
                enabled=True,
                use_search_history=True,
                use_query_expansion=True,
                expansion_factor=0.5,
            )
        )
    )


@patch("autoresearch.search.context.get_config", make_config)
@patch("autoresearch.search.context.SPACY_AVAILABLE", False)
def test_extract_entities_without_spacy():
    with SearchContext.temporary_instance() as ctx:
        ctx.nlp = None
        ctx._extract_entities("Hello World")
        assert ctx.entities["hello"] == 1
        assert ctx.entities["world"] == 1
