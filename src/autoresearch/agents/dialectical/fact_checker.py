"""FactChecker agent verifies claims against external sources."""

from typing import Any, Dict, Iterable, Mapping

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
from ...storage import ClaimAuditRecord, ClaimAuditStatus

log = get_logger(__name__)


class FactChecker(Agent):
    """Verifies claims against external knowledge sources."""

    role: AgentRole = AgentRole.FACT_CHECKER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Check existing claims for factual accuracy."""
        log.info(f"FactChecker executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Retrieve external references
        max_results = getattr(
            config, "max_results_per_query", 5
        )  # Default to 5 if not specified
        raw_sources = Search.external_lookup(state.query, max_results=max_results)
        sources: list[Dict[str, Any]] = []
        seen_sources: set[tuple[str | None, str | None, str | None]] = set()

        def _source_key(source: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
            snippet = source.get("snippet") or source.get("content") or ""
            key = (
                source.get("url"),
                source.get("title"),
                snippet[:200] if isinstance(snippet, str) else None,
            )
            return key

        def _register_sources(candidates: Iterable[Mapping[str, Any]]) -> list[Dict[str, Any]]:
            registered: list[Dict[str, Any]] = []
            for candidate in candidates:
                enriched = dict(candidate)
                enriched["checked_claims"] = [c["id"] for c in state.claims]
                enriched["agent"] = self.name
                key = _source_key(enriched)
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                sources.append(enriched)
                registered.append(enriched)
            return registered

        _register_sources(raw_sources)

        query_variations: list[str] = []
        for claim in state.claims:
            query_variations.extend(
                expand_retrieval_queries(
                    claim.get("content", ""), base_query=state.query, max_variations=2
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

            def _evaluate(source: Mapping[str, Any]) -> None:
                nonlocal best_score, best_source
                snippet = source.get("snippet") or source.get("content") or ""
                if not isinstance(snippet, str) or not snippet.strip():
                    return
                breakdown = score_entailment(claim_text, snippet)
                breakdowns.append(breakdown)
                if breakdown.score > best_score:
                    best_score = breakdown.score
                    best_source = dict(source)

            for source in sources:
                _evaluate(source)

            aggregate = aggregate_entailment_scores(breakdowns)
            if aggregate.disagreement:
                for paraphrase in sample_paraphrases(claim_text, max_samples=2):
                    new_candidates = Search.external_lookup(
                        paraphrase, max_results=max_results
                    )
                    registered = _register_sources(new_candidates)
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

            record = ClaimAuditRecord.from_score(
                claim["id"],
                score_value,
                sources=[best_source] if best_source else None,
                notes=note,
                status=status,
                variance=aggregate.variance if aggregate.sample_size else None,
                instability=aggregate.disagreement if aggregate.sample_size else None,
                sample_size=aggregate.sample_size or None,
            )
            audit_payload = record.to_payload()
            claim_audits.append(audit_payload)
            if best_source and best_source not in top_sources:
                top_sources.append(best_source)

        # Generate verification using the prompt template
        claims_text = "\n".join(c.get("content", "") for c in state.claims)
        prompt = self.generate_prompt("fact_checker.verification", claims=claims_text)
        verification = adapter.generate(prompt, model=model)

        # Create and return the result
        valid_scores = [
            audit.get("entailment_score")
            for audit in claim_audits
            if audit.get("entailment_score") is not None
        ]
        aggregate_score = (
            sum(valid_scores) / len(valid_scores) if valid_scores else None
        )
        aggregate_status = classify_entailment(aggregate_score or 0.0)

        variance_values = [
            audit.get("entailment_variance")
            for audit in claim_audits
            if audit.get("entailment_variance") is not None
        ]
        aggregate_variance = (
            sum(variance_values) / len(variance_values) if variance_values else None
        )
        total_samples = sum(int(audit.get("sample_size") or 0) for audit in claim_audits)
        instability_flags = [
            audit.get("instability_flag")
            for audit in claim_audits
            if audit.get("instability_flag") is not None
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
        )
        return self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.VERIFICATION,
                "source_count": len(sources),
                "query_variations": query_variations,
            },
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
