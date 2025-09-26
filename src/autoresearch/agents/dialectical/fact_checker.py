"""FactChecker agent verifies claims against external sources."""

from typing import Dict, Any

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...evidence import classify_entailment, expand_retrieval_queries, score_entailment
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search
from ...storage import ClaimAuditRecord

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
        sources = []
        for s in raw_sources:
            s = dict(s)
            s["checked_claims"] = [c["id"] for c in state.claims]
            s["agent"] = self.name
            sources.append(s)

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
            best_score = 0.0
            best_source: Dict[str, Any] | None = None
            for source in sources:
                snippet = source.get("snippet") or source.get("content") or ""
                breakdown = score_entailment(claim.get("content", ""), snippet)
                if breakdown.score > best_score:
                    best_score = breakdown.score
                    best_source = source
            status = classify_entailment(best_score)
            record = ClaimAuditRecord(
                claim_id=claim["id"],
                status=status,
                entailment_score=best_score,
                sources=[best_source] if best_source else [],
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
        aggregate_score = (
            sum(audit.get("entailment_score", 0.0) for audit in claim_audits) / len(claim_audits)
            if claim_audits
            else 0.0
        )
        aggregate_status = classify_entailment(aggregate_score)
        claim = self.create_claim(
            verification,
            "verification",
            metadata={"query_variations": query_variations},
            verification_status=aggregate_status,
            verification_sources=top_sources,
            entailment_score=aggregate_score,
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
