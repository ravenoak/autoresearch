"""
Mixins for agent functionality.

This module provides mixins that can be used to add common functionality to agents.
"""

from typing import Any, Dict, List, Mapping, Optional, Sequence, TypeAlias
from uuid import uuid4

from ..config.models import AgentConfig, ConfigModel
from ..logging_utils import get_logger
from ..storage import ClaimAuditRecord, ClaimAuditStatus
from .prompts import render_prompt

log = get_logger(__name__)

ClaimPayload: TypeAlias = Dict[str, Any]
MetadataPayload: TypeAlias = Dict[str, Any]
ResultPayload: TypeAlias = Dict[str, Any]
SourcePayload: TypeAlias = Dict[str, Any]


class PromptGeneratorMixin:
    """Mixin for generating prompts using the prompt template system."""

    def generate_prompt(self, template_name: str, **kwargs: Any) -> str:
        """Generate a prompt using a template.

        Args:
            template_name: The name of the template to use.
            **kwargs: Variables to substitute in the template.

        Returns:
            The generated prompt as a string.
        """
        return render_prompt(template_name, **kwargs)


class ModelConfigMixin:
    """Mixin for handling model configuration."""

    def get_model_config(self, config: ConfigModel, agent_name: str) -> str:
        """Get the model configuration for this agent.

        Args:
            config: The configuration model.
            agent_name: The name of the agent.

        Returns:
            The model name to use.
        """
        model_cfg: AgentConfig | None = config.agent_config.get(agent_name)
        if model_cfg and model_cfg.model:
            return model_cfg.model
        return config.default_model


class ClaimGeneratorMixin:
    """Mixin for generating claims."""

    def create_claim(
        self,
        content: str,
        claim_type: str,
        metadata: Optional[MetadataPayload] = None,
        *,
        audit: ClaimAuditRecord | Mapping[str, Any] | None = None,
        verification_status: ClaimAuditStatus | str | None = None,
        verification_sources: Optional[Sequence[SourcePayload]] = None,
        entailment_score: float | None = None,
        notes: str | None = None,
    ) -> ClaimPayload:
        """Create a claim with the given content and type.

        Args:
            content: The content of the claim.
            claim_type: The type of the claim (e.g., "thesis", "antithesis").
            metadata: Optional metadata to include with the claim.
            audit: Optional pre-built :class:`ClaimAuditRecord` or mapping.
            verification_status: Convenience shortcut to derive an audit payload
                without constructing a :class:`ClaimAuditRecord` manually.
            verification_sources: Evidence payloads that informed the
                verification decision.
            entailment_score: Normalised entailment score in ``[0, 1]``.
            notes: Optional reviewer notes to attach to the audit payload.

        Returns:
            A dictionary representing the claim.
        """
        claim: ClaimPayload = {
            "id": str(uuid4()),
            "type": claim_type,
            "content": content,
        }
        if metadata:
            claim.update(metadata)

        audit_payload: dict[str, Any] | None = None
        if audit is not None:
            audit_payload = (
                audit.to_payload() if isinstance(audit, ClaimAuditRecord) else dict(audit)
            )
        elif any(
            value is not None
            for value in (verification_status, verification_sources, entailment_score)
        ):
            status_enum: ClaimAuditStatus
            if verification_status is None:
                status_enum = ClaimAuditStatus.from_entailment(entailment_score)
            elif isinstance(verification_status, ClaimAuditStatus):
                status_enum = verification_status
            else:
                status_enum = ClaimAuditStatus(str(verification_status))
            sources_payload: list[dict[str, Any]] = []
            if verification_sources:
                for src in verification_sources:
                    if isinstance(src, Mapping):
                        sources_payload.append(dict(src))
                    else:
                        raise TypeError("verification_sources must contain mappings")
            record = ClaimAuditRecord(
                claim_id=claim["id"],
                status=status_enum,
                entailment_score=entailment_score,
                sources=sources_payload,
                notes=notes,
            )
            audit_payload = record.to_payload()

        if audit_payload is not None:
            audit_payload["claim_id"] = claim["id"]
            claim["audit"] = audit_payload
        return claim


class ResultGeneratorMixin:
    """Mixin for generating results."""

    def create_result(
        self,
        claims: List[ClaimPayload],
        metadata: MetadataPayload,
        results: ResultPayload,
        sources: Optional[List[SourcePayload]] = None,
        claim_audits: Optional[List[Dict[str, Any]]] = None,
    ) -> ResultPayload:
        """Create a result with the given claims, metadata, and results.

        Args:
            claims: The claims to include in the result.
            metadata: Metadata to include with the result.
            results: Results to include with the result.
            sources: Optional sources to include with the result.
            claim_audits: Optional list of audit payloads for downstream
                consumers. Each entry should match the schema emitted by
                :class:`ClaimAuditRecord`.

        Returns:
            A dictionary representing the result.
        """
        result: ResultPayload = {
            "claims": claims,
            "metadata": metadata,
            "results": results,
        }
        if sources:
            result["sources"] = sources
        if claim_audits:
            result["claim_audits"] = claim_audits
        return result
