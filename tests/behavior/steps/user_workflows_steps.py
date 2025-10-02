from tests.behavior.context import BehaviorContext
import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputDepth, OutputFormatter
from autoresearch.ui.provenance import (
    generate_socratic_prompts,
    section_toggle_defaults,
)

pytest_plugins = [
    "tests.behavior.steps.common_steps",
    "tests.behavior.steps.streamlit_gui_steps",
]


@scenario("../features/user_workflows.feature", "CLI search completes successfully")
def test_cli_workflow(bdd_context: BehaviorContext):
    assert bdd_context["result"].exit_code == 0


@scenario(
    "../features/user_workflows.feature",
    "CLI search with invalid backend reports error",
)
def test_cli_workflow_invalid_backend(bdd_context: BehaviorContext):
    assert bdd_context["result"].exit_code != 0


@pytest.mark.requires_ui
@scenario(
    "../features/user_workflows.feature",
    "Streamlit interface displays results",
)
def test_streamlit_ui_workflow() -> None:
    """Ensure the Streamlit UI renders search results."""


@scenario(
    "../features/user_workflows.feature",
    "Layered UX exposes claim toggles and prompts",
)
def test_layered_ux_guidance() -> None:
    """Behavior scenario verifying layered UX guidance."""


@given("a layered depth payload with claim audits")
def layered_payload(bdd_context: BehaviorContext) -> None:
    """Build a standard-depth payload containing claim audits."""

    response = QueryResponse(
        answer="Autoresearch produces evidence-backed answers.\n\n- Item one",
        citations=[{"title": "Source A"}],
        reasoning=["Finding one", "Finding two"],
        metrics={
            "scout_gate": {
                "rationales": {
                    "coverage": {
                        "triggered": True,
                        "description": "coverage below policy",
                    }
                }
            }
        },
        claim_audits=[
            {
                "claim_id": "C1",
                "status": "supported",
                "sources": [{"title": "Evidence"}],
            }
        ],
    )
    payload = OutputFormatter.plan_response_depth(response, OutputDepth.STANDARD)
    bdd_context["depth_payload"] = payload


@when("I derive layered UX guidance")
def derive_guidance(bdd_context: BehaviorContext) -> None:
    """Derive toggle defaults and Socratic prompts."""

    payload = bdd_context["depth_payload"]
    bdd_context["toggle_defaults"] = section_toggle_defaults(payload)
    bdd_context["socratic_prompts"] = generate_socratic_prompts(payload)


@then("the layered payload exposes claim toggles")
def assert_claim_toggles(bdd_context: BehaviorContext) -> None:
    """Ensure the claim table toggle is available and enabled."""

    toggles = bdd_context["toggle_defaults"]
    assert toggles["claim_audits"]["available"] is True
    assert toggles["claim_audits"]["value"] is True


@then("Socratic prompts include claim follow-ups")
def assert_socratic_prompts(bdd_context: BehaviorContext) -> None:
    """Verify generated Socratic prompts reference the claim."""

    prompts = bdd_context["socratic_prompts"]
    assert any("claim" in prompt.lower() for prompt in prompts)
