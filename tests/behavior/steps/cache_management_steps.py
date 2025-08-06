"""Step definitions for cache management feature."""

from pytest_bdd import scenario, given, when, then, parsers
import pytest

from autoresearch import cache


@pytest.fixture(autouse=True)
def temp_cache(tmp_path, monkeypatch):
    """Use a temporary TinyDB path for each scenario and reset cache."""
    db_path = tmp_path / "cache.json"
    monkeypatch.setenv("TINYDB_PATH", str(db_path))
    cache.teardown(remove_file=True)
    cache.setup(str(db_path))
    yield
    cache.teardown(remove_file=True)


# Scenarios
@scenario("../features/cache_management.feature", "Store results in cache")
def test_store_results():
    pass


@scenario("../features/cache_management.feature", "Retrieve cached results")
def test_retrieve_cached_results():
    pass


@scenario("../features/cache_management.feature", "Cache miss returns None")
def test_cache_miss():
    pass


@scenario("../features/cache_management.feature", "Clear cache removes stored results")
def test_clear_cache():
    pass


# Step definitions
@given("an empty cache")
def empty_cache():
    cache.clear()


@given(parsers.parse('cached results for query "{query}" and backend "{backend}"'))
def given_cached_results(query, backend, bdd_context):
    results = [{"title": "cached"}]
    cache.cache_results(query, backend, results)
    bdd_context["query"] = query
    bdd_context["backend"] = backend
    bdd_context["results"] = results


@when(parsers.parse('I store results for query "{query}" and backend "{backend}"'))
def store_results(query, backend, bdd_context):
    results = [{"title": "stored"}]
    cache.cache_results(query, backend, results)
    bdd_context["query"] = query
    bdd_context["backend"] = backend
    bdd_context["results"] = results


@when(parsers.parse('I retrieve results for query "{query}" and backend "{backend}"'))
def retrieve_results(query, backend, bdd_context):
    bdd_context["retrieved"] = cache.get_cached_results(query, backend)


@when("I clear the cache")
def clear_cache():
    cache.clear()


@then("the cached data is returned")
def cached_data_returned(bdd_context):
    assert bdd_context["retrieved"] == bdd_context["results"]


@then("no cached data is returned")
def no_cached_data_returned(bdd_context):
    assert bdd_context.get("retrieved") is None


@then(parsers.parse('retrieving results for query "{query}" and backend "{backend}" yields the stored data'))
def retrieval_yields_stored(query, backend, bdd_context):
    retrieved = cache.get_cached_results(query, backend)
    assert retrieved == bdd_context["results"]


@then(parsers.parse('retrieving results for query "{query}" and backend "{backend}" yields no data'))
def retrieval_yields_none(query, backend):
    assert cache.get_cached_results(query, backend) is None
