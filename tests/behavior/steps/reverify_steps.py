from __future__ import annotations
from tests.behavior.utils import as_payload
from tests.behavior.context import BehaviorContext

from pytest_bdd import given, then, when

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.reverify import ReverifyOptions, run_reverification
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.state_registry import QueryStateRegistry


@given("a stored query state with claim audits")
def stored_query_state(bdd_context: BehaviorContext, monkeypatch):
    """Create and register a query state with baseline claim audits."""

    state = QueryState(query="Reverify scenario")
    state.claims = [
        {"id": "c1", "content": "Claim one"},
        {"id": "c2", "content": "Claim two"},
    ]
    state.claim_audits = [
        {
            "claim_id": "c1",
            "status": "needs_review",
            "notes": "Initial audit",
            "sources": [],
        }
    ]
    config = ConfigModel()
    state_id = QueryStateRegistry.register(state, config)
    bdd_context["state_id"] = state_id

    def fake_execute(self, run_state, run_config):
        overrides = run_state.metadata.get("_reverify_options", {})
        bdd_context["captured_options"] = dict(overrides)
        return as_payload({
            "claims": [],
            "metadata": {},
            "results": {},
            "sources": [
                {
                    "title": "Expanded source",
                    "snippet": "Evidence snippet",
                    "source_id": "src-1",
                }
            ],
            "claim_audits": [
                {
                    "claim_id": "c1",
                    "status": "supported",
                    "notes": "Broadened verification",
                    "sources": [
                        {
                            "title": "Expanded source",
                            "snippet": "Evidence snippet",
                            "source_id": "src-1",
                        }
                    ],
                    "provenance": {
                        "retrieval": {
                            "events": [],
                            "options": dict(overrides),
                            "max_variations": overrides.get("max_variations", 2),
                        },
                        "backoff": {
                            "retry_count": 0,
                            "paraphrases": [],
                            "max_results": overrides.get("max_results", 5),
                        },
                        "evidence": {"claim_id": "c1"},
                    },
                }
            ],
        })

    monkeypatch.setattr(
        "autoresearch.orchestration.reverify.FactChecker.execute",
        fake_execute,
        raising=False,
    )


@when("I request claim re-verification with broadened sources")
def request_reverification(bdd_context: BehaviorContext):
    """Trigger the re-verification workflow with broader retrieval."""

    response = run_reverification(
        bdd_context["state_id"],
        options=ReverifyOptions(broaden_sources=True, max_results=8, max_variations=4),
    )
    bdd_context["reverify_response"] = response
    bdd_context["snapshot"] = QueryStateRegistry.get_snapshot(bdd_context["state_id"])


@then("the refreshed audits should replace the previous results")
def refreshed_audits_replace_previous(bdd_context: BehaviorContext):
    """Ensure that refreshed audits override the baseline ones."""

    response = bdd_context["reverify_response"]
    assert response.claim_audits, "Expected refreshed audits"
    assert response.claim_audits[0]["status"] == "supported"
    assert response.state_id == bdd_context["state_id"]
    snapshot = bdd_context["snapshot"]
    assert snapshot is not None
    assert snapshot.state.claim_audits[0]["status"] == "supported"


@then("the registry snapshot should include the broadened provenance")
def registry_snapshot_includes_broadened_metadata(bdd_context: BehaviorContext):
    """Validate that provenance captures broadened retrieval parameters."""

    options = bdd_context.get("captured_options", {})
    assert options.get("broaden_sources") is True
    assert options.get("max_results") == 8
    snapshot = bdd_context["snapshot"]
    audit = snapshot.state.claim_audits[0]
    provenance = audit.get("provenance", {})
    retrieval_meta = provenance.get("retrieval", {})
    backoff_meta = provenance.get("backoff", {})
    assert retrieval_meta.get("options", {}).get("broaden_sources") is True
    assert backoff_meta.get("max_results") == 8
