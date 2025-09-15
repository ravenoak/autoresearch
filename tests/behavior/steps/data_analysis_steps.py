import pytest
from pytest_bdd import given, then, when

from autoresearch.data_analysis import metrics_dataframe
from tests.optional_imports import import_or_skip

pl = import_or_skip("polars")


@given("sample metrics")
def sample_metrics(bdd_context) -> None:
    bdd_context["metrics"] = {"agent_timings": {"A": [1.0, 2.0]}}


# Spec: docs/specs/data-analysis.md#polars-enabled
@when("I generate metrics dataframe with Polars enabled")
def generate_df_enabled(bdd_context) -> None:
    metrics = bdd_context["metrics"]
    bdd_context["result"] = metrics_dataframe(metrics, polars_enabled=True)
    bdd_context["error"] = None


# Spec: docs/specs/data-analysis.md#polars-disabled
@when("I generate metrics dataframe with Polars disabled")
def generate_df_disabled(bdd_context) -> None:
    metrics = bdd_context["metrics"]
    try:
        metrics_dataframe(metrics, polars_enabled=False)
        bdd_context["result"] = None
        bdd_context["error"] = None
    except Exception as e:
        bdd_context["result"] = None
        bdd_context["error"] = e


# Spec: docs/specs/data-analysis.md#polars-enabled
@then("a Polars dataframe should be returned")
def assert_polars_dataframe(bdd_context) -> None:
    assert isinstance(bdd_context["result"], pl.DataFrame)


# Spec: docs/specs/data-analysis.md#polars-disabled
@then("the operation should fail with polars disabled error")
def assert_polars_disabled_error(bdd_context) -> None:
    assert bdd_context["result"] is None
    err = bdd_context.get("error")
    assert err is not None
    assert "Polars analysis is disabled" in str(err)
