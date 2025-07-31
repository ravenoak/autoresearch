"""
Mixins for agent functionality.

This module provides mixins that can be used to add common functionality to agents.
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4

from ..config.models import ConfigModel
from ..logging_utils import get_logger
from .prompts import render_prompt

log = get_logger(__name__)


class PromptGeneratorMixin:
    """Mixin for generating prompts using the prompt template system."""

    def generate_prompt(self, template_name: str, **kwargs) -> str:
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
        model_cfg = config.agent_config.get(agent_name)
        return (
            model_cfg.model if model_cfg and model_cfg.model else config.default_model
        )


class ClaimGeneratorMixin:
    """Mixin for generating claims."""

    def create_claim(
        self, content: str, claim_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a claim with the given content and type.

        Args:
            content: The content of the claim.
            claim_type: The type of the claim (e.g., "thesis", "antithesis").
            metadata: Optional metadata to include with the claim.

        Returns:
            A dictionary representing the claim.
        """
        claim = {
            "id": str(uuid4()),
            "type": claim_type,
            "content": content,
        }
        if metadata:
            claim.update(metadata)
        return claim


class ResultGeneratorMixin:
    """Mixin for generating results."""

    def create_result(
        self,
        claims: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        results: Dict[str, Any],
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a result with the given claims, metadata, and results.

        Args:
            claims: The claims to include in the result.
            metadata: Metadata to include with the result.
            results: Results to include with the result.
            sources: Optional sources to include with the result.

        Returns:
            A dictionary representing the result.
        """
        result = {
            "claims": claims,
            "metadata": metadata,
            "results": results,
        }
        if sources:
            result["sources"] = sources
        return result
