import responses
from autoresearch.llm import get_llm_adapter, DummyAdapter


def test_dummy_adapter_generation():
    adapter = get_llm_adapter("dummy")
    assert isinstance(adapter, DummyAdapter)
    result = adapter.generate("test prompt")
    assert "Dummy response" in result


@responses.activate
def test_lmstudio_adapter(monkeypatch):
    endpoint = "http://testserver/v1/chat/completions"
    monkeypatch.setenv("LMSTUDIO_ENDPOINT", endpoint)
    adapter = get_llm_adapter("lmstudio")
    responses.add(
        responses.POST,
        endpoint,
        json={"choices": [{"message": {"content": "hi"}}]},
    )
    text = adapter.generate("hello")
    assert text == "hi"
    assert responses.calls[0].request.url == endpoint


@responses.activate
def test_openai_adapter(monkeypatch):
    endpoint = "https://api.openai.com/v1/chat/completions"
    monkeypatch.setenv("OPENAI_ENDPOINT", endpoint)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    adapter = get_llm_adapter("openai")
    responses.add(
        responses.POST,
        endpoint,
        json={"choices": [{"message": {"content": "ok"}}]},
    )
    text = adapter.generate("hi")
    assert text == "ok"
    headers = responses.calls[0].request.headers
    assert headers.get("Authorization") == "Bearer test"
