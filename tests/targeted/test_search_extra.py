from autoresearch.search import Search


def test_preprocess_text_simple():
    text = "Hello, World! 123"
    tokens = Search.preprocess_text(text)
    assert tokens == ["hello", "world"]
