from autoresearch.orchestration.state import QueryState


def test_get_dialectical_structure() -> None:
    state = QueryState(
        query="q",
        claims=[
            {"id": "1", "type": "thesis", "content": "t"},
            {"id": "2", "type": "antithesis", "content": "a"},
            {"id": "3", "type": "verification", "content": "v"},
            {"id": "4", "type": "synthesis", "content": "s"},
        ],
    )
    struct = state.get_dialectical_structure()
    assert struct["thesis"]["id"] == "1"
    assert struct["antithesis"][0]["id"] == "2"
    assert struct["verification"][0]["id"] == "3"
    assert struct["synthesis"]["id"] == "4"
