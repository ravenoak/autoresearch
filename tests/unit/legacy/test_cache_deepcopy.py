# mypy: ignore-errors
import autoresearch.cache as cache


def test_cache_results_are_deepcopied(tmp_path):
    db_path = tmp_path / "c.json"
    c = cache.SearchCache(str(db_path))
    original = [{"title": "t", "url": "u"}]
    cache.cache_results("q", "b", original)
    cached = cache.get_cached_results("q", "b")
    assert cached == original
    cached[0]["title"] = "changed"
    assert cache.get_cached_results("q", "b")[0]["title"] == "t"
    c.teardown(remove_file=True)


def test_get_cache_returns_singleton():
    c1 = cache.get_cache()
    c2 = cache.get_cache()
    assert c1 is c2
