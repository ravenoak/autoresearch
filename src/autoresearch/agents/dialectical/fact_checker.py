"""FactChecker agent verifies claims against external sources."""

from typing import Any, Dict, Iterable, Mapping, Sequence

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...evidence import (
    aggregate_entailment_scores,
    EntailmentBreakdown,
    classify_entailment,
    expand_retrieval_queries,
    sample_paraphrases,
    score_entailment,
)
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search
from ...storage import ClaimAuditRecord, ClaimAuditStatus, ensure_source_id

log = get_logger(__name__)


class FactChecker(Agent):
    """Verifies claims against external knowledge sources."""

    role: AgentRole = AgentRole.FACT_CHECKER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Check existing claims for factual accuracy."""
        log.info(f"FactChecker executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)
        planner_snapshot = self._planner_provenance(state)

        # Retrieve external references
        overrides = state.metadata.get("_reverify_options")
        override_map: dict[str, Any] = {}
        if isinstance(overrides, Mapping):
            override_map = {str(key): value for key, value in overrides.items()}
        broaden_sources = bool(override_map.get("broaden_sources"))
        max_results = getattr(
            config, "max_results_per_query", 5
        )  # Default to 5 if not specified
        override_max_results = override_map.get("max_results")
        if override_max_results is not None:
            try:
                max_results = max(1, int(override_max_results))
            except (TypeError, ValueError):
                log.warning(
                    "Invalid max_results override provided during reverify",
                    extra={"override": override_max_results},
                )
        elif broaden_sources:
            broaden_target = override_map.get("broaden_max_results")
            if broaden_target is not None:
                try:
                    max_results = max(1, int(broaden_target))
                except (TypeError, ValueError):
                    log.warning(
                        "Invalid broaden_max_results override provided during reverify",
                        extra={"override": broaden_target},
                    )
                    max_results = max(max_results, max_results * 2)
            else:
                max_results = max(max_results, max_results * 2)
        max_variations = 2
        override_variations = override_map.get("max_variations")
        if override_variations is not None:
            try:
                max_variations = max(1, int(override_variations))
            except (TypeError, ValueError):
                log.warning(
                    "Invalid max_variations override provided during reverify",
                    extra={"override": override_variations},
                )
        elif broaden_sources:
            max_variations = max(4, max_variations)
        prompt_variant = override_map.get("prompt_variant")
        lookup_bundle = Search.external_lookup(
            state.query, max_results=max_results, return_handles=True
        )
        if isinstance(lookup_bundle, list):
            base_candidates = list(lookup_bundle)
            retrieval_handle: dict[str, Any] | None = None
            by_backend: Mapping[str, Any] | None = None
        else:
            base_candidates = list(getattr(lookup_bundle, "results", []))
            retrieval_handle = {
                "cache_namespace": getattr(getattr(lookup_bundle, "cache", None), "namespace", None),
            }
            by_backend = getattr(lookup_bundle, "by_backend", None)

        sources: list[Dict[str, Any]] = []
        seen_sources: set[tuple[str | None, str | None, str | None]] = set()
        retrieval_log: list[dict[str, Any]] = []
        claim_retry_stats: dict[str, dict[str, Any]] = {}

        def _source_key(source: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
            snippet = source.get("snippet") or source.get("content") or ""
            key = (
                source.get("url"),
                source.get("title"),
                snippet[:200] if isinstance(snippet, str) else None,
            )
            return key

        def _register_sources(
            candidates: Iterable[Mapping[str, Any]],
            *,
            query_text: str,
            variant_label: str,
            claim_id: str | None = None,
            retry_index: int | None = None,
            backend: str | None = None,
        ) -> list[Dict[str, Any]]:
            registered: list[Dict[str, Any]] = []
            serialised = [dict(candidate) for candidate in candidates]
            retrieval_log.append(
                {
                    "query": query_text,
                    "variant": variant_label,
                    "claim_id": claim_id,
                    "retry": retry_index,
                    "backend": backend,
                    "result_count": len(serialised),
                }
            )
            for candidate in serialised:
                enriched = dict(candidate)
                enriched["checked_claims"] = [c["id"] for c in state.claims]
                enriched["agent"] = self.name
                enriched["retrieval_query"] = query_text
                enriched["query_variant"] = variant_label
                if claim_id:
                    enriched["claim_context"] = claim_id
                if backend:
                    enriched.setdefault("backend", backend)
                enriched = ensure_source_id(enriched)
                key = _source_key(enriched)
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                sources.append(enriched)
                registered.append(enriched)
            return registered

        if by_backend:
            for backend_name, backend_results in by_backend.items():
                _register_sources(
                    backend_results,
                    query_text=state.query,
                    variant_label="base",
                    backend=str(backend_name),
                )
        else:
            _register_sources(
                base_candidates,
                query_text=state.query,
                variant_label="base",
            )

        query_variations: list[str] = []
        for claim in state.claims:
            query_variations.extend(
                expand_retrieval_queries(
                    claim.get("content", ""),
                    base_query=state.query,
                    max_variations=max_variations,
                )
            )

        claim_audits: list[dict[str, Any]] = []
        top_sources: list[Dict[str, Any]] = []
        for claim in state.claims:
            claim_text = str(claim.get("content", "")).strip()
            if not claim_text:
                continue

            breakdowns: list[EntailmentBreakdown] = []
            best_score = -1.0
            best_source: Dict[str, Any] | None = None
            considered_ids: set[str] = set()
            paraphrases_used: list[str] = []
            retry_count = 0

            def _evaluate(source: Mapping[str, Any]) -> None:
                nonlocal best_score, best_source
                snippet = source.get("snippet") or source.get("content") or ""
                if not isinstance(snippet, str) or not snippet.strip():
                    return
                breakdown = score_entailment(claim_text, snippet)
                breakdowns.append(breakdown)
                source_id = str(source.get("source_id") or "")
                if source_id:
                    considered_ids.add(source_id)
                if breakdown.score > best_score:
                    best_score = breakdown.score
                    best_source = dict(source)

            for source in sources:
                _evaluate(source)

            aggregate = aggregate_entailment_scores(breakdowns)
            if aggregate.disagreement:
                for paraphrase in sample_paraphrases(claim_text, max_samples=2):
                    retry_count += 1
                    paraphrases_used.append(paraphrase)
                    new_candidates = Search.external_lookup(
                        paraphrase, max_results=max_results
                    )
                    registered = _register_sources(
                        new_candidates,
                        query_text=paraphrase,
                        variant_label="paraphrase",
                        claim_id=str(claim.get("id", "")) or None,
                        retry_index=retry_count,
                    )
                    for source in registered:
                        _evaluate(source)
                    aggregate = aggregate_entailment_scores(breakdowns)
                    if not aggregate.disagreement or aggregate.sample_size >= max_results * 2:
                        break

            score_value = aggregate.mean if aggregate.sample_size else None
            status = classify_entailment(score_value or 0.0)
            if aggregate.disagreement or aggregate.sample_size == 0:
                status = ClaimAuditStatus.NEEDS_REVIEW

            note: str | None = None
            if aggregate.sample_size:
                note = (
                    f"Self-check over {aggregate.sample_size} snippet(s); "
                    f"variance={aggregate.variance:.3f}."
                )
                if aggregate.disagreement:
                    note += " Disagreement detected; manual review recommended."
            else:
                note = "No retrieval snippets matched the claim."

            claim_id = str(claim.get("id", "")) or None
            relevant_events = [
                dict(event)
                for event in retrieval_log
                if event.get("claim_id") in {claim_id, None}
            ]
            provenance = {
                "retrieval": {
                    "base_query": state.query,
                    "claim_text": claim_text,
                    "query_variations": list(query_variations),
                    "events": relevant_events,
                    "options": override_map or None,
                    "max_variations": max_variations,
                },
                "backoff": {
                    "retry_count": retry_count,
                    "paraphrases": paraphrases_used,
                    "max_results": max_results,
                },
                "evidence": {
                    "best_source_id": best_source.get("source_id") if best_source else None,
                    "considered_source_ids": sorted(considered_ids),
                    "claim_id": claim_id,
                },
            }
            if planner_snapshot:
                provenance["planner"] = dict(planner_snapshot)
            if claim_id:
                claim_retry_stats[claim_id] = {
                    "retry_count": retry_count,
                    "paraphrases": paraphrases_used,
                }

            record = ClaimAuditRecord.from_score(
                claim["id"],
                score_value,
                sources=[best_source] if best_source else None,
                notes=note,
                status=status,
                variance=aggregate.variance if aggregate.sample_size else None,
                instability=aggregate.disagreement if aggregate.sample_size else None,
                sample_size=aggregate.sample_size or None,
                provenance=provenance,
            )
            audit_payload = record.to_payload()
            claim_audits.append(audit_payload)
            if best_source and best_source not in top_sources:
                top_sources.append(best_source)

        # Generate verification using the prompt template
        claims_text = "\n".join(c.get("content", "") for c in state.claims)
        template_name = "fact_checker.verification"
        if prompt_variant:
            candidate = f"{template_name}.{prompt_variant}"
            try:
                prompt = self.generate_prompt(candidate, claims=claims_text)
            except KeyError:
                log.warning(
                    "Prompt variant %s not found; falling back to default",
                    prompt_variant,
                )
                prompt = self.generate_prompt(template_name, claims=claims_text)
        else:
            prompt = self.generate_prompt(template_name, claims=claims_text)
        verification = adapter.generate(prompt, model=model)

        # Create and return the result
        valid_scores = [
            float(score)
            for audit in claim_audits
            for score in [audit.get("entailment_score")]
            if isinstance(score, (int, float))
        ]
        aggregate_score = (
            sum(valid_scores) / len(valid_scores) if valid_scores else None
        )
        aggregate_status = classify_entailment(aggregate_score or 0.0)

        variance_values = [
            float(variance)
            for audit in claim_audits
            for variance in [audit.get("entailment_variance")]
            if isinstance(variance, (int, float))
        ]
        aggregate_variance = (
            sum(variance_values) / len(variance_values) if variance_values else None
        )
        total_samples = sum(
            int(sample)
            for audit in claim_audits
            for sample in [audit.get("sample_size")]
            if isinstance(sample, (int, float))
        )
        instability_flags = [
            bool(flag)
            for audit in claim_audits
            for flag in [audit.get("instability_flag")]
            if isinstance(flag, bool)
        ]
        instability_state: bool | None
        if instability_flags:
            instability_state = any(bool(flag) for flag in instability_flags)
        elif claim_audits:
            instability_state = False
        else:
            instability_state = None

        if instability_state or not valid_scores:
            aggregate_status = ClaimAuditStatus.NEEDS_REVIEW

        summary_note: str | None = None
        if claim_audits:
            if total_samples:
                summary_note = f"Aggregated over {total_samples} snippet(s)."
                if aggregate_variance is not None:
                    summary_note += f" Mean variance={aggregate_variance:.3f}."
            else:
                summary_note = "No snippet-level audits were available."
            if instability_state:
                summary_note = (summary_note or "") + " Instability detected across claims."

        handle_payload = (
            retrieval_handle if retrieval_handle and any(retrieval_handle.values()) else None
        )
        aggregate_provenance = {
            "retrieval": {
                "base_query": state.query,
                "query_variations": list(query_variations),
                "events": retrieval_log,
                "handle": handle_payload,
                "options": override_map or None,
            },
            "backoff": {
                "per_claim": claim_retry_stats,
                "total_retries": sum(
                    int(retry)
                    for stats in claim_retry_stats.values()
                    for retry in [stats.get("retry_count")]
                    if isinstance(retry, (int, float))
                ),
                "max_results": max_results,
            },
            "evidence": {
                "top_source_ids": [src.get("source_id") for src in top_sources if src.get("source_id")],
                "claim_audit_ids": [payload.get("audit_id") for payload in claim_audits],
            },
            "prompt": {
                "template": template_name,
                "variant": prompt_variant,
            },
        }
        if planner_snapshot:
            aggregate_provenance["planner"] = dict(planner_snapshot)

        claim = self.create_claim(
            verification,
            "verification",
            metadata={"query_variations": query_variations},
            verification_status=aggregate_status,
            verification_sources=top_sources,
            entailment_score=aggregate_score,
            entailment_variance=aggregate_variance,
            instability_flag=instability_state,
            sample_size=total_samples or None,
            notes=summary_note,
            provenance=aggregate_provenance,
        )
        metadata_payload = {
            "phase": DialoguePhase.VERIFICATION,
            "source_count": len(sources),
            "query_variations": query_variations,
            "audit_provenance_fact_checker": aggregate_provenance,
        }
        if planner_snapshot:
            metadata_payload["planner_provenance"] = dict(planner_snapshot)

        return self.create_result(
            claims=[claim],
            metadata=metadata_payload,
            results={"verification": verification},
            sources=sources,
            claim_audits=claim_audits,
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Only execute in dialectical mode if there are claims."""
        if config.reasoning_mode != ReasoningMode.DIALECTICAL:
            return False
        has_claims = len(state.claims) > 0
        return super().can_execute(state, config) and has_claims

    @staticmethod
    def _planner_provenance(state: QueryState) -> dict[str, Any]:
        """Capture planner telemetry for verification provenance."""

        snapshot: dict[str, Any] = {}
        planner_meta = state.metadata.get("planner")
        if isinstance(planner_meta, Mapping):
            stats = planner_meta.get("task_graph")
            if isinstance(stats, Mapping):
                snapshot["task_graph_stats"] = dict(stats)
            telemetry = planner_meta.get("telemetry")
            if isinstance(telemetry, Mapping):
                snapshot["telemetry"] = dict(telemetry)
        tasks = state.task_graph.get("tasks") if isinstance(state.task_graph, Mapping) else None
        if isinstance(tasks, Sequence):
            task_ids = [
                str(task.get("id"))
                for task in tasks
                if isinstance(task, Mapping) and task.get("id")
            ]
            if task_ids:
                snapshot["task_ids"] = task_ids
        return snapshot
