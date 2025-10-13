"""
Mixins for agent functionality.

This module provides mixins that can be used to add common functionality to agents.
"""

import os
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

    def get_model_config(self, config: ConfigModel, agent_name: str, adapter: "LLMAdapter | None" = None) -> str:
        """Get the model configuration for this agent with enhanced selection logic.

        Model selection priority (highest to lowest):
        1. Environment variable override (AUTORESEARCH_MODEL_<AGENT> or AUTORESEARCH_MODEL)
        2. Agent-specific model configuration
        3. Agent-specific preferred models (if adapter available for discovery)
        4. Global default model from config
        5. Intelligent fallback based on discovered models (if adapter available)

        Args:
            config: The configuration model.
            agent_name: The name of the agent.
            adapter: Optional LLM adapter for model discovery and validation.

        Returns:
            The model name to use.
        """
        from ..logging_utils import get_logger

        logger = get_logger(__name__)

        # 1. Check for environment variable overrides
        env_model = self._get_env_model_override(agent_name)
        if env_model:
            logger.debug(f"Using environment variable model override: {env_model}")
            return env_model

        # 2. Check agent-specific model configuration
        model_cfg: AgentConfig | None = config.agent_config.get(agent_name)
        if model_cfg and model_cfg.model:
            logger.debug(f"Using agent-specific model configuration: {model_cfg.model}")
            return model_cfg.model

        # 3. Try agent-specific preferred models if adapter is available
        if adapter and model_cfg and model_cfg.preferred_models:
            for preferred_model in model_cfg.preferred_models:
                if self._validate_model_with_adapter(preferred_model, adapter):
                    logger.debug(f"Using agent preferred model: {preferred_model}")
                    return preferred_model

        # 4. Use global default model from config
        if config.default_model:
            logger.debug(f"Using global default model: {config.default_model}")
            return config.default_model

        # 5. Intelligent fallback using adapter's discovered models
        if adapter:
            fallback_model = self._get_intelligent_fallback(adapter)
            if fallback_model:
                logger.debug(f"Using intelligent fallback model: {fallback_model}")
                return fallback_model

        # 6. Final fallback to a safe default
        fallback = "mistral"  # Conservative default
        logger.warning(f"No suitable model found, using fallback: {fallback}")
        return fallback

    @staticmethod
    def _get_env_model_override(agent_name: str) -> str | None:
        """Get model override from environment variables.

        Checks for agent-specific and global model overrides in this order:
        1. AUTORESEARCH_MODEL_<AGENT_UPPER> (e.g., AUTORESEARCH_MODEL_SYNTHESIZER)
        2. AUTORESEARCH_MODEL (global override)

        Args:
            agent_name: The name of the agent.

        Returns:
            Model name from environment or None if not set.
        """
        # Agent-specific environment variable
        agent_env_var = f"AUTORESEARCH_MODEL_{agent_name.upper()}"
        model = os.getenv(agent_env_var)
        if model:
            return model.strip()

        # Global environment variable
        model = os.getenv("AUTORESEARCH_MODEL")
        if model:
            return model.strip()

        return None

    @staticmethod
    def _validate_model_with_adapter(model: str, adapter: "LLMAdapter") -> bool:
        """Validate if a model is available through the adapter.

        Args:
            model: The model name to validate.
            adapter: The LLM adapter to check against.

        Returns:
            True if the model is available, False otherwise.
        """
        try:
            available_models = adapter.available_models
            return model in available_models
        except Exception:
            # If we can't get available models, assume the model is valid
            return True

    @staticmethod
    def _get_intelligent_fallback(adapter: "LLMAdapter") -> str | None:
        """Get an intelligent fallback model based on discovered models.

        Prefers models in this order:
        1. Models with larger context windows
        2. Models that appear to be well-known/popular
        3. First available model as last resort

        Args:
            adapter: The LLM adapter with model discovery capabilities.

        Returns:
            Best available fallback model or None.
        """
        try:
            available_models = adapter.available_models
            if not available_models:
                return None

            # If only one model available, use it
            if len(available_models) == 1:
                return available_models[0]

            # Try to find models with larger context windows first
            model_context_sizes = {}
            for model in available_models:
                try:
                    if hasattr(adapter, 'get_context_size'):
                        context_size = adapter.get_context_size(model)
                        model_context_sizes[model] = context_size
                except Exception:
                    # If we can't get context size, assume default
                    model_context_sizes[model] = 4096

            # Sort by context size (largest first)
            sorted_models = sorted(
                model_context_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Return the model with largest context size
            return sorted_models[0][0]

        except Exception:
            # If intelligent fallback fails, return first available model
            available_models = adapter.available_models
            return available_models[0] if available_models else None


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
        entailment_variance: float | None = None,
        instability_flag: bool | None = None,
        sample_size: int | None = None,
        notes: str | None = None,
        provenance: Mapping[str, Any] | None = None,
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
            entailment_variance: Sample variance of entailment scores where
                available.
            instability_flag: Boolean indicator that the self-check disagreed
                with retrieved snippets.
            sample_size: Number of snippets contributing to the entailment
                estimate.
            notes: Optional reviewer notes to attach to the audit payload.
            provenance: Optional structured provenance metadata describing
                retrieval queries, retry counts, or evidence identifiers.

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
            for value in (
                verification_status,
                verification_sources,
                entailment_score,
                entailment_variance,
                instability_flag,
                sample_size,
                notes,
            )
        ):
            try:
                record = ClaimAuditRecord.from_score(
                    claim["id"],
                    entailment_score,
                    sources=verification_sources,
                    notes=notes,
                    status=verification_status,
                    variance=entailment_variance,
                    instability=instability_flag,
                    sample_size=sample_size,
                    provenance=provenance,
                )
            except TypeError as exc:
                raise TypeError("verification_sources must contain mappings") from exc
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
