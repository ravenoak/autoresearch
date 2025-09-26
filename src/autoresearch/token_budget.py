"""Token budget utilities and budget-aware routing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Mapping

from .logging_utils import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class ModelBudget:
    """Cost and latency metadata used when ranking model candidates."""

    name: str
    prompt_cost_per_1k: float
    completion_cost_per_1k: float
    latency_ms: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class RoleUsageSnapshot:
    """Aggregate token and latency statistics for an agent role."""

    role: str
    call_count: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_prompt_tokens: float
    avg_completion_tokens: float
    avg_latency_ms: float | None
    model_counts: Mapping[str, int]


@dataclass(frozen=True)
class RoutingDecision:
    """Decision returned by :func:`select_model_for_role`."""

    role: str
    model: str
    estimated_cost: float
    estimated_latency_ms: float | None
    meets_budget: bool
    rationale: str


def round_with_margin(usage: float, margin: float) -> int:
    """Return ``usage * (1 + margin)`` rounded half up.

    Args:
        usage: Baseline token usage.
        margin: Additional fractional margin to apply.

    Returns:
        int: Rounded token budget.
    """
    scaled = Decimal(str(usage)) * (Decimal("1") + Decimal(str(margin)))
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def _estimate_call_cost(snapshot: RoleUsageSnapshot, budget: ModelBudget) -> float:
    """Return the estimated per-call cost for ``budget`` given ``snapshot``.

    Args:
        snapshot: Aggregated usage metrics for the role.
        budget: Model cost profile.

    Returns:
        Estimated monetary cost for a single invocation.
    """

    prompt_tokens = snapshot.avg_prompt_tokens
    completion_tokens = snapshot.avg_completion_tokens
    prompt_component = (prompt_tokens / 1000.0) * budget.prompt_cost_per_1k
    completion_component = (completion_tokens / 1000.0) * budget.completion_cost_per_1k
    return prompt_component + completion_component


def select_model_for_role(
    snapshot: RoleUsageSnapshot,
    candidates: Mapping[str, ModelBudget],
    *,
    default_model: str,
    cost_budget: float | None = None,
    latency_budget_ms: float | None = None,
) -> RoutingDecision:
    """Return the most appropriate model for ``snapshot.role``.

    The ranking process balances latency and token cost. Models that violate
    explicit ``cost_budget`` or ``latency_budget_ms`` constraints are
    deprioritised but can still win when no candidate satisfies both limits.

    Args:
        snapshot: Usage statistics for a specific role.
        candidates: Mapping of model name to budget metadata.
        default_model: Fallback model when no candidate improves upon it.
        cost_budget: Optional per-call cost ceiling. ``None`` disables the
            constraint.
        latency_budget_ms: Optional latency ceiling in milliseconds. ``None``
            disables the constraint.

    Returns:
        A :class:`RoutingDecision` describing the chosen model and rationale.
    """

    if not candidates:
        log.debug("No candidate models provided; retaining default %s", default_model)
        return RoutingDecision(
            role=snapshot.role,
            model=default_model,
            estimated_cost=0.0,
            estimated_latency_ms=snapshot.avg_latency_ms,
            meets_budget=True,
            rationale="No candidates supplied",
        )

    def _score(budget: ModelBudget) -> tuple[bool, float, float]:
        cost = _estimate_call_cost(snapshot, budget)
        latency = budget.latency_ms if budget.latency_ms is not None else (
            snapshot.avg_latency_ms or 0.0
        )
        within_cost = cost_budget is None or cost <= cost_budget
        within_latency = latency_budget_ms is None or (
            latency is not None and latency <= latency_budget_ms
        )
        hard_fail = not within_cost or not within_latency
        # Prefer lower cost and latency; normalise by using the raw values.
        return hard_fail, cost, latency or float("inf")

    ranked = sorted(candidates.values(), key=_score)
    chosen = ranked[0]
    estimated_cost = _estimate_call_cost(snapshot, chosen)
    estimated_latency = (
        chosen.latency_ms if chosen.latency_ms is not None else snapshot.avg_latency_ms
    )
    meets_budget = True
    reasons: list[str] = []

    if cost_budget is not None:
        if estimated_cost <= cost_budget:
            reasons.append(f"cost {estimated_cost:.4f} within {cost_budget:.4f}")
        else:
            reasons.append(
                f"cost {estimated_cost:.4f} exceeds {cost_budget:.4f}"  # pragma: no cover - text only
            )
            meets_budget = False
    else:
        reasons.append(f"cost {estimated_cost:.4f} (no ceiling)")

    if latency_budget_ms is not None:
        if estimated_latency is not None and estimated_latency <= latency_budget_ms:
            reasons.append(
                f"latency {estimated_latency:.1f}ms within {latency_budget_ms:.1f}ms"
            )
        else:
            reasons.append(
                f"latency {estimated_latency if estimated_latency is not None else float('nan'):.1f}ms exceeds {latency_budget_ms:.1f}ms"
            )
            meets_budget = False
    else:
        reasons.append(
            f"latency {estimated_latency:.1f}ms (no ceiling)"
            if estimated_latency is not None
            else "latency unknown"
        )

    rationale = "; ".join(reasons)

    if chosen.max_tokens is not None and snapshot.avg_prompt_tokens > chosen.max_tokens:
        meets_budget = False
        rationale += f"; prompt average {snapshot.avg_prompt_tokens:.1f} exceeds cap {chosen.max_tokens}"

    return RoutingDecision(
        role=snapshot.role,
        model=chosen.name,
        estimated_cost=estimated_cost,
        estimated_latency_ms=estimated_latency,
        meets_budget=meets_budget,
        rationale=rationale,
    )
