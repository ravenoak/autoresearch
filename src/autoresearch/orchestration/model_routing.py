from __future__ import annotations

"""Utilities for applying role-aware model routing policies."""

from dataclasses import dataclass, field
import time
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence

from ..config.models import AgentConfig, ConfigModel, ModelRoutingConfig
from ..logging_utils import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from .metrics import OrchestrationMetrics


log = get_logger(__name__)


@dataclass
class RoutingOverrideRequest:
    """Explicit override applied by the gate, planner, or user."""

    agent: str
    requested_model: str | None
    source: str
    reason: str
    confidence: float | None = None
    threshold: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of the override."""

        payload: dict[str, Any] = {
            "agent": self.agent,
            "requested_model": self.requested_model,
            "source": self.source,
            "reason": self.reason,
            "created_at": self.created_at,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.threshold is not None:
            payload["threshold"] = self.threshold
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    def as_log_extra(self) -> dict[str, Any]:
        """Return structured logging metadata."""

        extra = self.to_dict()
        extra["kind"] = "routing_override"
        return extra

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> list["RoutingOverrideRequest"]:
        """Build override requests from a serialisable mapping."""

        if not isinstance(payload, Mapping):
            return []
        agents: list[str] = []
        agent = payload.get("agent")
        if agent:
            agents = [str(agent)]
        else:
            agents_raw = payload.get("agents")
            if isinstance(agents_raw, Sequence) and not isinstance(agents_raw, (str, bytes)):
                agents = [str(item) for item in agents_raw if str(item).strip()]
        model_map = payload.get("model_map")
        if not agents:
            return []
        requested_model = payload.get("model")
        confidence = payload.get("confidence")
        threshold = payload.get("threshold")
        metadata_raw = payload.get("metadata")
        heuristics_raw = payload.get("heuristics")
        metadata: dict[str, Any] = {}
        if isinstance(metadata_raw, Mapping):
            metadata.update({str(k): v for k, v in metadata_raw.items()})
        if isinstance(heuristics_raw, Mapping):
            metadata.setdefault("heuristics", dict(heuristics_raw))
        reason = str(payload.get("reason") or "override").strip() or "override"
        source = str(payload.get("source") or "unknown").strip() or "unknown"
        requests: list[RoutingOverrideRequest] = []
        for name in agents:
            model = requested_model
            if isinstance(model_map, Mapping):
                mapped = model_map.get(name)
                if mapped:
                    model = mapped
            try:
                confidence_val = float(confidence) if confidence is not None else None
            except (TypeError, ValueError):  # pragma: no cover - defensive guard
                confidence_val = None
            try:
                threshold_val = float(threshold) if threshold is not None else None
            except (TypeError, ValueError):  # pragma: no cover - defensive guard
                threshold_val = None
            requests.append(
                cls(
                    agent=str(name),
                    requested_model=str(model) if model else None,
                    source=source,
                    reason=reason,
                    confidence=confidence_val,
                    threshold=threshold_val,
                    metadata=dict(metadata),
                )
            )
        return requests


@dataclass
class AgentRoutingDirectives:
    """Resolved routing configuration for a specific agent."""

    allowed_models: list[str] | None
    preferred_models: list[str] | None
    latency_slo_ms: float | None
    token_share: float | None
    budget_tokens: float | None
    policy_name: str | None
    strategy_name: str | None
    override: RoutingOverrideRequest | None
    default_model: str


def _clamp_token_share(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        return None


def _normalize_models(models: Iterable[str] | None) -> list[str]:
    if not models:
        return []
    seen: set[str] = set()
    ordered: list[str] = []
    for model in models:
        key = str(model).strip()
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def _latest_override(
    agent_name: str,
    overrides: Sequence[RoutingOverrideRequest],
) -> RoutingOverrideRequest | None:
    lowered = agent_name.lower()
    for override in reversed(list(overrides)):
        if override.agent.lower() == lowered:
            return override
    return None


def resolve_agent_directives(
    agent_name: str,
    config: ConfigModel,
    routing_cfg: ModelRoutingConfig,
    agent_cfg: AgentConfig | None,
    overrides: Sequence[RoutingOverrideRequest],
) -> AgentRoutingDirectives:
    """Merge routing configuration, role policy, and overrides."""

    policy_key, policy = routing_cfg.policy_for(agent_name)
    preferred = None
    allowed = None
    latency_slo = None
    token_share = None
    budget_tokens = None
    if policy:
        preferred = _normalize_models(policy.preferred_models)
        allowed = _normalize_models(policy.allowed_models)
        latency_slo = policy.latency_slo_ms
        token_share = policy.token_share
        budget_tokens = float(policy.token_budget) if policy.token_budget is not None else None
    if agent_cfg:
        if agent_cfg.preferred_models:
            preferred = _normalize_models(agent_cfg.preferred_models)
        if agent_cfg.allowed_models:
            allowed = _normalize_models(agent_cfg.allowed_models)
        if agent_cfg.latency_slo_ms is not None:
            latency_slo = agent_cfg.latency_slo_ms
        if agent_cfg.token_share is not None:
            token_share = agent_cfg.token_share
    preferred = preferred or None
    allowed = allowed or None
    latency_slo = latency_slo if latency_slo is not None else None
    token_share = _clamp_token_share(token_share)
    override = _latest_override(agent_name, overrides)
    if override and override.requested_model:
        override_model = override.requested_model
        preferred = [override_model] + [
            model for model in (preferred or []) if model != override_model
        ]
        if allowed is None:
            allowed = [override_model]
        elif override_model not in allowed:
            allowed = [override_model, *[m for m in allowed if m != override_model]]
    default_model = (
        (policy.default_model if policy and policy.default_model else None)
        or config.default_model
    )
    return AgentRoutingDirectives(
        allowed_models=allowed,
        preferred_models=preferred,
        latency_slo_ms=latency_slo,
        token_share=token_share,
        budget_tokens=budget_tokens,
        policy_name=policy_key,
        strategy_name=routing_cfg.strategy_name,
        override=override,
        default_model=default_model,
    )


def evaluate_gate_confidence_escalations(
    config: ConfigModel,
    metrics: "OrchestrationMetrics",
    heuristics: Mapping[str, float],
    *,
    source: str = "scout_gate",
) -> list[RoutingOverrideRequest]:
    """Escalate routing when gate confidence drops below policy thresholds."""

    routing_cfg = getattr(config, "model_routing", None)
    if not routing_cfg or not routing_cfg.enabled or not routing_cfg.role_policies:
        return []
    confidence = heuristics.get("retrieval_confidence")
    if confidence is None:
        return []
    overrides: list[RoutingOverrideRequest] = []
    for agent_name, policy in routing_cfg.role_policies.items():
        threshold = getattr(policy, "confidence_threshold", None)
        if threshold is None:
            continue
        if confidence < threshold:
            target_model = policy.escalation_model or policy.default_model
            reason = policy.escalation_reason or "low_confidence"
            override = metrics.request_model_escalation(
                agent_name,
                model=target_model,
                source=source,
                reason=reason,
                confidence=confidence,
                threshold=threshold,
                metadata={"heuristics": dict(heuristics)},
            )
            overrides.append(override)
    return overrides


def ingest_state_overrides(payload: Any) -> list[RoutingOverrideRequest]:
    """Convert planner/state-provided overrides into request objects."""

    requests: list[RoutingOverrideRequest] = []
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for entry in payload:
            if isinstance(entry, Mapping):
                requests.extend(RoutingOverrideRequest.from_payload(entry))
    return requests
