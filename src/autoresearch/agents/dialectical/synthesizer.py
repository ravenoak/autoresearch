"""SynthesizerAgent creates the thesis and final synthesis."""

from typing import Any, Dict, List, Mapping, Sequence

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...evidence import (
    EntailmentBreakdown,
    aggregate_entailment_scores,
    classify_entailment,
    expand_retrieval_queries,
    sample_paraphrases,
    score_entailment,
)
from ...orchestration.phases import DialoguePhase
from ...orchestration.reasoning import ReasoningMode
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...storage import ClaimAuditRecord, ClaimAuditStatus, ensure_source_id
from ...errors import LLMError

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
        lm_errors: list[dict[str, Any]] = []

        def guarded_generate(prompt_name: str, prompt_text: str, fallback: str) -> tuple[str, LLMError | None]:
            """Invoke the LLM adapter while capturing recoverable failures."""

            try:
                # Validate and adjust prompt for context size
                adjusted_prompt = self._validate_and_adjust_prompt(prompt_text, model, config)
                return adapter.generate(adjusted_prompt, model=model), None
            except LLMError as exc:
                log.warning(
                    "Synthesizer %s generation failed with LLM error: %s",
                    prompt_name,
                    exc,
                )
                lm_errors.append(
                    {
                        "phase": prompt_name,
                        "message": str(exc),
                        "metadata": getattr(exc, "metadata", None),
                    }
                )
                return fallback, exc

        # Record context utilization for metrics
        from ..orchestration.metrics import get_orchestration_metrics
        metrics = get_orchestration_metrics()

        # Record context utilization for the model used
        if model and hasattr(metrics, 'record_context_utilization'):
            from ..llm.context_management import get_context_manager
            context_mgr = get_context_manager()
            context_size = context_mgr.get_context_size(model)
            # Estimate tokens used (rough approximation)
            estimated_prompt_tokens = len(prompt_text) // 4
            metrics.record_context_utilization(model, estimated_prompt_tokens, context_size)

        if mode == ReasoningMode.DIRECT:
            # Direct reasoning mode: Answer the query directly
            prompt = self.generate_prompt("synthesizer.direct", query=state.query)
            answer, error = guarded_generate(
                "direct_answer",
                prompt,
                "No answer synthesized due to upstream LM error.",
            )

            metadata_extra, audit_kwargs, support_audits = self._build_verification_context(
                answer, state
            )
            if error:
                metadata_extra = metadata_extra or {}
                metadata_extra["lm_errors"] = lm_errors
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
            thesis_text, error = guarded_generate(
                "thesis",
                prompt,
                "Thesis unavailable due to LM error.",
            )

            claim = self.create_claim(thesis_text, "thesis")
            metadata_payload: dict[str, Any] = {"phase": DialoguePhase.THESIS}
            if error:
                metadata_payload["lm_errors"] = lm_errors
            return self.create_result(
                claims=[claim],
                metadata=metadata_payload,
                results={"thesis": thesis_text},
            )

        else:
            # Later cycles: Synthesize from claims
            claims_text = "\n".join(c.get("content", "") for c in state.claims)
            prompt = self.generate_prompt("synthesizer.synthesis", claims=claims_text)
            synthesis_text, error = guarded_generate(
                "synthesis",
                prompt,
                "Synthesis unavailable due to LM error.",
            )

            metadata_extra, audit_kwargs, support_audits = self._build_verification_context(
                synthesis_text, state
            )
            if error:
                metadata_extra = metadata_extra or {}
                metadata_extra["lm_errors"] = lm_errors
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
        planner_snapshot = self._planner_provenance(state)
        if planner_snapshot:
            metadata["planner_provenance"] = dict(planner_snapshot)
        query_variations = expand_retrieval_queries(
            hypothesis, base_query=state.query, max_variations=3
        )
        if query_variations:
            metadata["query_variations"] = query_variations

        support_audits: list[dict[str, Any]] = []
        support_breakdowns: list[EntailmentBreakdown] = []
        best_source: Mapping[str, Any] | None = None
        best_score = -1.0
        synthesis_source = ensure_source_id(
            {"title": "Synthesizer synthesis", "snippet": hypothesis}
        )
        for claim in state.claims:
            claim_id = claim.get("id")
            content = str(claim.get("content", "")).strip()
            if not claim_id or not content:
                continue
            breakdown = score_entailment(hypothesis, content)
            support_breakdowns.append(breakdown)
            peer_source = ensure_source_id(
                {
                    "claim_id": claim_id,
                    "title": f"{claim.get('type', 'claim').title()} claim",
                    "snippet": content,
                }
            )
            if breakdown.score > best_score:
                best_source = peer_source
                best_score = breakdown.score
            provenance = {
                "retrieval": {
                    "mode": "hypothesis_vs_claim",
                    "hypothesis": hypothesis,
                    "claim_id": claim_id,
                },
                "backoff": {"retry_count": 0},
                "evidence": {
                    "source_ids": [synthesis_source["source_id"]],
                    "peer_claim_id": claim_id,
                },
            }
            if planner_snapshot:
                provenance["planner"] = dict(planner_snapshot)
            record = ClaimAuditRecord.from_score(
                claim_id,
                breakdown.score,
                sources=[synthesis_source],
                provenance=provenance,
            )
            support_audits.append(record.to_payload())

        aggregate = aggregate_entailment_scores(support_breakdowns)
        if aggregate.disagreement:
            for paraphrase in sample_paraphrases(hypothesis, max_samples=2):
                for claim in state.claims:
                    claim_id = claim.get("id")
                    content = str(claim.get("content", "")).strip()
                    if not claim_id or not content:
                        continue
                    support_breakdowns.append(score_entailment(paraphrase, content))
                aggregate = aggregate_entailment_scores(support_breakdowns)
                if not aggregate.disagreement:
                    break

        audit_kwargs: dict[str, Any] = {}
        if aggregate.sample_size:
            audit_kwargs["entailment_score"] = aggregate.mean
            status = classify_entailment(aggregate.mean)
            if aggregate.disagreement:
                status = ClaimAuditStatus.NEEDS_REVIEW
            audit_kwargs["verification_status"] = status
            audit_kwargs["entailment_variance"] = (
                aggregate.variance if aggregate.sample_size else None
            )
            audit_kwargs["instability_flag"] = (
                aggregate.disagreement if aggregate.sample_size else None
            )
            audit_kwargs["sample_size"] = aggregate.sample_size
            note = (
                f"Derived from {aggregate.sample_size} upstream signal(s); "
                f"variance={aggregate.variance:.3f}."
            )
            if aggregate.disagreement:
                note += " Disagreement detected; manual review advised."
            audit_kwargs["notes"] = note
        else:
            audit_kwargs["verification_status"] = ClaimAuditStatus.NEEDS_REVIEW
            audit_kwargs["notes"] = "No upstream claims were available for verification."
        if best_source:
            audit_kwargs["verification_sources"] = [best_source]
        provenance_payload = {
            "retrieval": {
                "mode": "peer_consensus",
                "related_claim_ids": [c.get("id") for c in state.claims if c.get("id")],
            },
            "backoff": {"retry_count": 0},
            "evidence": {
                "support_audit_ids": [audit.get("audit_id") for audit in support_audits],
                "best_source_id": best_source.get("source_id") if best_source else None,
            },
        }
        if planner_snapshot:
            provenance_payload["planner"] = dict(planner_snapshot)
        audit_kwargs["provenance"] = provenance_payload

        metadata["audit_provenance_synthesizer"] = {
            "summary": dict(audit_kwargs.get("provenance", {})),
            "supporting_audits": [
                dict(audit.get("provenance", {}))
                for audit in support_audits
                if isinstance(audit, Mapping) and audit.get("provenance")
            ],
        }

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

    @staticmethod
    def _planner_provenance(state: QueryState) -> dict[str, Any]:
        """Extract planner telemetry relevant for audit provenance."""

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
