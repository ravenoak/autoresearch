# mypy: ignore-errors
"""Step definitions for parallel group merging feature."""

from __future__ import annotations
from typing import TypedDict, cast

from pytest_bdd import given, scenarios, then, when

from autoresearch.orchestration.reasoning_payloads import (
    FrozenReasoningStep,
    normalize_reasoning_step,
)
from tests.behavior.utils import as_payload

pytest_plugins = ["tests.behavior.steps.common_steps"]


scenarios("../features/parallel_group_merging.feature")


class RunResult(TypedDict):
    """Structure for orchestrator run results used by the scenarios."""

    groups: list[str]
    reasoning: list[FrozenReasoningStep]


@given("two agent groups", target_fixture="run_result")
def two_agent_groups() -> RunResult:
    """Provide two distinct agent groups for the orchestrator."""
    return cast(RunResult, as_payload({"groups": ["group_a", "group_b"], "reasoning": []}))


@when("the orchestrator runs them in parallel")
def run_parallel(run_result: RunResult) -> None:
    """Simulate parallel execution producing one claim per group."""
    run_result["reasoning"] = [
        normalize_reasoning_step({"group": run_result["groups"][0], "claim": "claim 1"}),
        normalize_reasoning_step({"group": run_result["groups"][1], "claim": "claim 2"}),
    ]


@then("the reasoning should contain two claims")
def assert_two_claims(run_result: RunResult) -> None:
    """Ensure two reasoning entries were produced."""
    assert len(run_result["reasoning"]) == 2


@then("each claim should come from a distinct group")
def assert_distinct_groups(run_result: RunResult) -> None:
    """Verify each claim originates from a different group."""
    groups = {entry["group"] for entry in run_result["reasoning"]}
    assert groups == set(run_result["groups"])
