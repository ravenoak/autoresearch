"""Token budget utilities and budget-aware model routing helpers."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable, Mapping, Sequence

log = logging.getLogger(__name__)


def round_with_margin(usage: float, margin: float) -> int:
    """Return ``usage * (1 + margin)`` rounded half up."""

    scaled = Decimal(str(usage)) * (Decimal("1") + Decimal(str(margin)))
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def _percentile(values: Sequence[float], fraction: float) -> float:
    """Return the percentile for ``values`` at ``fraction`` in ``[0, 1]``."""

    if not values:
        return 0.0
    if fraction <= 0:
        return float(min(values))
    if fraction >= 1:
        return float(max(values))
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(ordered[int(index)])
    lower_val = float(ordered[lower])
    upper_val = float(ordered[upper])
    return lower_val + (upper_val - lower_val) * (index - lower)


@dataclass(frozen=True)
class ModelProfile:
    """Cost and latency profile for a single model option."""

    prompt_cost_per_1k: float
    completion_cost_per_1k: float
    latency_p95_ms: float
    quality_rank: int = 0

    def cost_per_token(self) -> float:
        """Return blended cost per token across prompt and completion."""

        return (self.prompt_cost_per_1k + self.completion_cost_per_1k) / 1000.0


@dataclass(frozen=True)
class AgentUsageStats:
    """Aggregate token and latency usage for an agent role."""

    avg_prompt_tokens: float
    avg_completion_tokens: float
    p95_latency_ms: float
    call_count: int

    @property
    def avg_total_tokens(self) -> float:
        """Return the average total tokens consumed per invocation."""

        return self.avg_prompt_tokens + self.avg_completion_tokens

    def estimated_cost(self, profile: ModelProfile) -> float:
        """Estimate currency cost using ``profile`` per-token pricing."""

        prompt_cost = (self.avg_prompt_tokens / 1000.0) * profile.prompt_cost_per_1k
        completion_cost = (
            self.avg_completion_tokens / 1000.0
        ) * profile.completion_cost_per_1k
        return prompt_cost + completion_cost

    @classmethod
    def from_samples(
        cls,
        token_samples: Sequence[tuple[int, int]],
        latencies_ms: Sequence[float],
    ) -> "AgentUsageStats" | None:
        """Build usage statistics from raw token and latency samples."""

        if not token_samples:
            return None
        prompt = sum(sample[0] for sample in token_samples) / len(token_samples)
        completion = sum(sample[1] for sample in token_samples) / len(token_samples)
        latency = _percentile(latencies_ms, 0.95) if latencies_ms else 0.0
        return cls(prompt, completion, latency, len(token_samples))


@dataclass(frozen=True)
class RoutingDecision:
    """Result of evaluating budget-aware routing for an agent."""

    agent: str
    selected_model: str | None
    previous_model: str
    reason: str
    usage: AgentUsageStats | None
    budget_tokens: float | None
    latency_cap_ms: float
    latency_slo_ms: float | None
    cost_before: float | None
    cost_after: float | None
    pressure_ratio: float
    metadata: dict[str, Any] | None = None

    def cost_savings(self) -> float | None:
        """Return the estimated currency saved by routing decisions."""

        if self.cost_before is None or self.cost_after is None:
            return None
        return self.cost_before - self.cost_after

    def as_log_extra(self) -> dict[str, Any]:
        """Return a flattened payload suitable for structured logging."""

        payload: dict[str, Any] = {
            "agent": self.agent,
            "selected_model": self.selected_model,
            "previous_model": self.previous_model,
            "reason": self.reason,
            "budget_tokens": self.budget_tokens,
            "latency_cap_ms": self.latency_cap_ms,
            "latency_slo_ms": self.latency_slo_ms,
            "cost_before": self.cost_before,
            "cost_after": self.cost_after,
            "cost_savings": self.cost_savings(),
            "pressure_ratio": self.pressure_ratio,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.usage is not None:
            payload.update(
                {
                    "avg_prompt_tokens": self.usage.avg_prompt_tokens,
                    "avg_completion_tokens": self.usage.avg_completion_tokens,
                    "avg_total_tokens": self.usage.avg_total_tokens,
                    "latency_p95_ms": self.usage.p95_latency_ms,
                    "call_count": self.usage.call_count,
                }
            )
        return payload

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the decision."""

        data = self.as_log_extra()
        data.pop("pressure_ratio", None)
        return data


class BudgetRouter:
    """Select an appropriate model when token budgets become constrained."""

    def __init__(
        self,
        profiles: Mapping[str, ModelProfile],
        *,
        default_model: str,
        pressure_ratio: float,
        default_latency_slo_ms: float,
    ) -> None:
        self._profiles = dict(profiles)
        self._default_model = default_model
        self._pressure_ratio = max(0.0, min(pressure_ratio, 1.0))
        self._default_latency_slo_ms = max(default_latency_slo_ms, 0.0)

    def _candidate_names(self, allowed: Sequence[str] | None) -> list[str]:
        if allowed:
            return [name for name in allowed if name in self._profiles]
        return list(self._profiles.keys())

    def _choose_preferred(
        self,
        candidates: Sequence[str],
        preferred: Sequence[str] | None,
    ) -> str | None:
        if not candidates:
            return None
        if preferred:
            for name in preferred:
                if name in candidates:
                    return name
        return max(
            candidates,
            key=lambda name: (
                self._profiles[name].quality_rank,
                -self._profiles[name].cost_per_token(),
            ),
        )

    def select_model_decision(
        self,
        agent_name: str,
        usage: AgentUsageStats | None,
        *,
        agent_budget_tokens: float | None,
        agent_latency_slo_ms: float | None,
        allowed_models: Sequence[str] | None,
        preferred_models: Sequence[str] | None,
        current_model: str,
    ) -> RoutingDecision:
        """Return routing metadata honouring token and latency constraints."""

        candidates = self._candidate_names(allowed_models)
        latency_cap = (
            agent_latency_slo_ms
            if agent_latency_slo_ms is not None
            else self._default_latency_slo_ms
        )
        if not candidates:
            decision = RoutingDecision(
                agent=agent_name,
                selected_model=None,
                previous_model=current_model,
                reason="no_candidates",
                usage=usage,
                budget_tokens=agent_budget_tokens,
                latency_cap_ms=latency_cap,
                latency_slo_ms=agent_latency_slo_ms,
                cost_before=None,
                cost_after=None,
                pressure_ratio=self._pressure_ratio,
            )
            log.info("Budget router evaluated", extra=decision.as_log_extra())
            return decision

        latency_constrained = [
            name
            for name in candidates
            if self._profiles[name].latency_p95_ms <= latency_cap
        ]
        if not latency_constrained:
            latency_constrained = list(candidates)

        baseline = self._choose_preferred(latency_constrained, preferred_models)
        if baseline is None:
            baseline = (
                current_model
                if current_model in latency_constrained
                else latency_constrained[0]
            )

        reason = "preferred"
        selected = baseline
        cost_before = None
        cost_after = None
        baseline_profile = self._profiles.get(baseline)
        if usage is not None and baseline_profile is not None:
            cost_before = usage.estimated_cost(baseline_profile)

        if usage is None:
            reason = "no_usage"
        elif agent_budget_tokens is None:
            reason = "no_budget"
        else:
            expected_tokens = max(usage.avg_total_tokens, 0.0)
            if expected_tokens <= 0:
                reason = "no_usage"
            else:
                budget_threshold = agent_budget_tokens * self._pressure_ratio
                if budget_threshold <= 0:
                    budget_threshold = agent_budget_tokens

                if expected_tokens > budget_threshold:
                    cheapest = min(
                        latency_constrained,
                        key=lambda name: self._profiles[name].cost_per_token(),
                    )
                    if cheapest != baseline:
                        selected = cheapest
                        reason = "budget_pressure"
                    else:
                        reason = "budget_pressure"
                else:
                    reason = "within_budget"

        selected_profile = self._profiles.get(selected)
        if usage is not None and selected_profile is not None:
            cost_after = usage.estimated_cost(selected_profile)

        decision = RoutingDecision(
            agent=agent_name,
            selected_model=selected,
            previous_model=current_model,
            reason=reason,
            usage=usage,
            budget_tokens=agent_budget_tokens,
            latency_cap_ms=latency_cap,
            latency_slo_ms=agent_latency_slo_ms,
            cost_before=cost_before,
            cost_after=cost_after,
            pressure_ratio=self._pressure_ratio,
        )
        log.info("Budget router evaluated", extra=decision.as_log_extra())
        return decision

    def select_model(
        self,
        agent_name: str,
        usage: AgentUsageStats | None,
        *,
        agent_budget_tokens: float | None,
        agent_latency_slo_ms: float | None,
        allowed_models: Sequence[str] | None,
        preferred_models: Sequence[str] | None,
        current_model: str,
    ) -> str | None:
        """Return the selected model name for compatibility callers."""

        decision = self.select_model_decision(
            agent_name,
            usage,
            agent_budget_tokens=agent_budget_tokens,
            agent_latency_slo_ms=agent_latency_slo_ms,
            allowed_models=allowed_models,
            preferred_models=preferred_models,
            current_model=current_model,
        )
        return decision.selected_model

    def iter_profiles(self) -> Iterable[tuple[str, ModelProfile]]:
        """Return an iterator over configured model profiles."""

        return self._profiles.items()
