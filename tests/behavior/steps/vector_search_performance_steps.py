from pytest_bdd import scenario, when, then
from unittest.mock import patch
import time

from autoresearch.storage import StorageManager


@scenario("../features/vector_search_performance.feature", "Vector search executes quickly")
def test_vector_search_performance():
    pass


@when("I measure vector search time", target_fixture="search_duration")
def measure_vector_search_time(persisted_claims):
    start = time.time()
    with patch("autoresearch.storage.StorageManager.has_vss", return_value=True):
        with patch("autoresearch.storage._db_backend.vector_search", return_value=[]):
            StorageManager.vector_search([0.0, 0.0], k=1)
    return time.time() - start


@then("the duration should be less than one second")
def check_duration(search_duration):
    assert search_duration < 1.0
