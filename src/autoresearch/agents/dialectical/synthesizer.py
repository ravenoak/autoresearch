"""SynthesizerAgent creates the thesis and final synthesis."""

from typing import Any, Dict, List, Mapping

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...evidence import (
    classify_entailment,
    expand_retrieval_queries,
    score_entailment,
)
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...storage import ClaimAuditRecord

log = get_logger(__name__)


class SynthesizerAgent(Agent):
    """Creates initial thesis and final synthesis."""

    role: AgentRole = AgentRole.SYNTHESIZER

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Synthesize claims and sources into coherent thesis or synthesis."""
        log.info(f"SynthesizerAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)
        mode = config.reasoning_mode
        is_first_cycle = state.cycle == 0

        if mode == ReasoningMode.DIRECT:
            # Direct reasoning mode: Answer the query directly
            prompt = self.generate_prompt("synthesizer.direct", query=state.query)
            answer = adapter.generate(prompt, model=model)

            metadata_extra, audit_kwargs, support_audits = self._build_verification_context(
                answer, state
            )
            claim = self.create_claim(
                answer,
                "synthesis",
                metadata=metadata_extra or None,
                **audit_kwargs,
            )
            claim_audits = self._assemble_claim_audits(claim, support_audits)
            return self.create_result(
                claims=[claim],
                metadata=self._augment_metadata(
                    {"phase": DialoguePhase.SYNTHESIS}, metadata_extra
                ),
                results={"final_answer": answer, "synthesis": answer},
                claim_audits=claim_audits,
            )

        elif is_first_cycle:
            # First cycle: Generate a thesis
            prompt = self.generate_prompt("synthesizer.thesis", query=state.query)
            thesis_text = adapter.generate(prompt, model=model)

            claim = self.create_claim(thesis_text, "thesis")
            return self.create_result(
                claims=[claim],
                metadata={"phase": DialoguePhase.THESIS},
                results={"thesis": thesis_text},
            )

        else:
            # Later cycles: Synthesize from claims
            claims_text = "\n".join(c.get("content", "") for c in state.claims)
            prompt = self.generate_prompt("synthesizer.synthesis", claims=claims_text)
            synthesis_text = adapter.generate(prompt, model=model)

            metadata_extra, audit_kwargs, support_audits = self._build_verification_context(
                synthesis_text, state
            )
            claim = self.create_claim(
                synthesis_text,
                "synthesis",
                metadata=metadata_extra or None,
                **audit_kwargs,
            )
            claim_audits = self._assemble_claim_audits(claim, support_audits)
            return self.create_result(
                claims=[claim],
                metadata=self._augment_metadata(
                    {"phase": DialoguePhase.SYNTHESIS}, metadata_extra
                ),
                results={"final_answer": synthesis_text, "synthesis": synthesis_text},
                claim_audits=claim_audits,
            )

    def _build_verification_context(
        self, hypothesis: str, state: QueryState
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        """Derive verification hints for a synthesized hypothesis."""

        metadata: dict[str, Any] = {}
        query_variations = expand_retrieval_queries(
            hypothesis, base_query=state.query, max_variations=3
        )
        if query_variations:
            metadata["query_variations"] = query_variations

        support_audits: list[dict[str, Any]] = []
        support_scores: list[float] = []
        best_source: Mapping[str, Any] | None = None
        best_score = -1.0
        synthesis_source = {"title": "Synthesizer synthesis", "snippet": hypothesis}
        for claim in state.claims:
            claim_id = claim.get("id")
            content = str(claim.get("content", "")).strip()
            if not claim_id or not content:
                continue
            breakdown = score_entailment(hypothesis, content)
            support_scores.append(breakdown.score)
            peer_source = {
                "claim_id": claim_id,
                "title": f"{claim.get('type', 'claim').title()} claim",
                "snippet": content,
            }
            if breakdown.score > best_score:
                best_source = peer_source
                best_score = breakdown.score
            record = ClaimAuditRecord.from_score(
                claim_id,
                breakdown.score,
                sources=[synthesis_source],
            )
            support_audits.append(record.to_payload())

        audit_kwargs: dict[str, Any] = {}
        if support_scores:
            aggregate_score = sum(support_scores) / len(support_scores)
            audit_kwargs["entailment_score"] = aggregate_score
            audit_kwargs["verification_status"] = classify_entailment(aggregate_score)
            audit_kwargs["notes"] = (
                f"Derived from {len(support_scores)} upstream claim(s)."
            )
        if best_source:
            audit_kwargs["verification_sources"] = [best_source]

        return metadata, audit_kwargs, support_audits

    @staticmethod
    def _augment_metadata(
        base: dict[str, Any], extras: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Merge optional metadata dictionaries."""

        merged = dict(base)
        if extras:
            merged.update(extras)
        return merged

    @staticmethod
    def _assemble_claim_audits(
        claim: Mapping[str, Any], support_audits: List[dict[str, Any]]
    ) -> List[dict[str, Any]] | None:
        """Combine claim-level audit payloads for downstream consumers."""

        payloads = list(support_audits)
        audit_payload = claim.get("audit")
        if isinstance(audit_payload, Mapping):
            payloads.append(dict(audit_payload))
        return payloads or None
