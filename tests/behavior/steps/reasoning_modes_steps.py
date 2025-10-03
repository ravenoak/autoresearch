from pytest_bdd import scenarios, when, then, parsers

from autoresearch.orchestration import ReasoningMode
from tests.behavior.context import BehaviorContext

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/reasoning_modes.feature")


@when(parsers.parse('a reasoning mode "{mode}" is chosen'))
def choose_mode(bdd_context: BehaviorContext, mode):
    bdd_context["mode"] = ReasoningMode(mode)


@then(parsers.parse('bdd_context records mode "{mode}"'))
def record_mode(bdd_context: BehaviorContext, mode):
    assert bdd_context.get("mode") == ReasoningMode(mode)


@when(parsers.parse('an audit badge "{badge}" is produced'))
def record_badge(bdd_context: BehaviorContext, badge: str) -> None:
    badges = bdd_context.setdefault("audit_badges", [])
    badges.append(badge)


@when('the response payload is assembled')
def assemble_payload(bdd_context: BehaviorContext) -> None:
    badges = list(bdd_context.get("audit_badges", []))
    bdd_context["response_payload"] = {"metrics": {"audit": {"badges": badges}}}


@then(parsers.parse('the response payload lists the audit badge "{badge}"'))
def assert_badge_present(bdd_context: BehaviorContext, badge: str) -> None:
    payload = bdd_context.get("response_payload", {})
    metrics = payload.get("metrics", {})
    audit = metrics.get("audit", {})
    badges = audit.get("badges", [])
    assert badge in badges
