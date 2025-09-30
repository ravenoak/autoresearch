from unittest.mock import patch

import pytest

from autoresearch.search.context import SearchContext
from tests.helpers import ConfigModelStub, make_config_model


pytestmark = pytest.mark.requires_nlp


def make_config(max_history: int) -> ConfigModelStub:
    return make_config_model(
        context_overrides={
            "max_history_items": max_history,
            "enabled": True,
            "use_search_history": True,
            "use_query_expansion": True,
            "expansion_factor": 0.5,
        }
    )


@patch("autoresearch.search.context.get_config", lambda: make_config(3))
def test_add_to_history_trims_old_entries() -> None:
    with SearchContext.temporary_instance() as ctx:
        for i in range(4):
            ctx.add_to_history(f"q{i}", [])
        assert len(ctx.search_history) == 3
        # should keep last 3 queries q1,q2,q3
        assert [item["query"] for item in ctx.search_history] == ["q1", "q2", "q3"]
