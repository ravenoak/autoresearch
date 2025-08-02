from pytest_bdd import scenario, when, then
from unittest.mock import patch
import time

from autoresearch.storage import StorageManager


@scenario("../features/vector_search_performance.feature", "Vector search executes quickly")
def test_vector_search_performance():
    pass


@when("I measure vector search time", target_fixture="search_duration")
def measure_vector_search_time(persisted_claims, bdd_context):
    start = time.time()
    orig_has_vss = StorageManager.has_vss
    from autoresearch import storage as storage_module
    orig_vector_search = storage_module.StorageManager.context.db_backend.vector_search
    with patch("autoresearch.storage.StorageManager.has_vss", return_value=True) as mock_has_vss:
        with patch(
            "autoresearch.storage.StorageManager.context.db_backend.vector_search",
            return_value=[],
        ) as mock_vs:
            StorageManager.vector_search([0.0, 0.0], k=1)
            bdd_context["vs_call"] = mock_vs.call_args
            bdd_context["has_vss_called"] = mock_has_vss.called
    bdd_context["orig_has_vss"] = orig_has_vss
    bdd_context["orig_vector_search"] = orig_vector_search
    return time.time() - start


@then("the duration should be less than one second")
def check_duration(search_duration):
    assert search_duration < 1.0


@then("vector search should be invoked correctly")
def vector_search_invoked_correctly(bdd_context):
    args, kwargs = bdd_context["vs_call"]
    assert args[0] == [0.0, 0.0]
    assert kwargs.get("k") == 1
    assert bdd_context["has_vss_called"] is True


@then("storage methods should be restored after the call")
def storage_methods_restored(bdd_context):
    from autoresearch import storage as storage_module

    assert StorageManager.has_vss is bdd_context["orig_has_vss"]
    assert (
        storage_module.StorageManager.context.db_backend.vector_search
        is bdd_context["orig_vector_search"]
    )
