from autoresearch.llm import get_llm_adapter, DummyAdapter


def test_dummy_adapter_generation():
    adapter = get_llm_adapter("dummy")
    assert isinstance(adapter, DummyAdapter)
    result = adapter.generate("test prompt")
    assert "Dummy response" in result
