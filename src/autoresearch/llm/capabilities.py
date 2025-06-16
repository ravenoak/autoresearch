"""LLM capability probing module for Autoresearch.

This module provides functionality to probe LLM capabilities, including:
- Available models for each provider
- Model capabilities (e.g., context length, supported features)
- Cost information
- Performance characteristics

It allows the system to dynamically discover and adapt to the capabilities
of different LLM providers and models.
"""

from __future__ import annotations

import json
import os
import requests
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from threading import Lock

from .registry import LLMFactory
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ModelCapabilities:
    """Data class representing the capabilities of an LLM model."""
    
    name: str
    provider: str
    context_length: int
    supports_function_calling: bool
    supports_vision: bool
    supports_streaming: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the capabilities to a dictionary."""
        return {
            "name": self.name,
            "provider": self.provider,
            "context_length": self.context_length,
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "supports_streaming": self.supports_streaming,
            "cost_per_1k_input_tokens": self.cost_per_1k_input_tokens,
            "cost_per_1k_output_tokens": self.cost_per_1k_output_tokens,
        }


class CapabilityProber:
    """Class for probing LLM capabilities."""
    
    _instance = None
    _lock = Lock()
    _capabilities_cache: Dict[str, Dict[str, ModelCapabilities]] = {}
    
    @classmethod
    def get_instance(cls) -> CapabilityProber:
        """Get the singleton instance of the CapabilityProber."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self) -> None:
        """Initialize the CapabilityProber."""
        self._providers_probed: Set[str] = set()
    
    def probe_provider(self, provider_name: str) -> Dict[str, ModelCapabilities]:
        """Probe the capabilities of a specific LLM provider.
        
        Args:
            provider_name: The name of the provider to probe
            
        Returns:
            A dictionary mapping model names to their capabilities
        """
        if provider_name in self._capabilities_cache:
            return self._capabilities_cache[provider_name]
        
        # Get the appropriate probe method based on the provider
        probe_method = getattr(self, f"_probe_{provider_name}", None)
        if probe_method is None:
            logger.warning(f"No probe method available for provider: {provider_name}")
            return {}
        
        # Probe the provider
        capabilities = probe_method()
        self._capabilities_cache[provider_name] = capabilities
        self._providers_probed.add(provider_name)
        
        return capabilities
    
    def probe_all_providers(self) -> Dict[str, Dict[str, ModelCapabilities]]:
        """Probe the capabilities of all registered LLM providers.
        
        Returns:
            A dictionary mapping provider names to dictionaries of model capabilities
        """
        # Get all registered providers
        providers = list(LLMFactory._registry.keys())
        
        # Probe each provider
        for provider in providers:
            if provider not in self._providers_probed:
                self.probe_provider(provider)
        
        return self._capabilities_cache
    
    def get_model_capabilities(self, model_name: str, provider_name: Optional[str] = None) -> Optional[ModelCapabilities]:
        """Get the capabilities of a specific model.
        
        Args:
            model_name: The name of the model
            provider_name: Optional provider name to narrow the search
            
        Returns:
            The model capabilities, or None if not found
        """
        if provider_name is not None:
            if provider_name in self._capabilities_cache:
                return self._capabilities_cache[provider_name].get(model_name)
            return None
        
        # Search across all providers
        for provider, models in self._capabilities_cache.items():
            if model_name in models:
                return models[model_name]
        
        return None
    
    def _probe_openai(self) -> Dict[str, ModelCapabilities]:
        """Probe the capabilities of the OpenAI provider.
        
        Returns:
            A dictionary mapping model names to their capabilities
        """
        capabilities = {}
        
        # Define known capabilities for OpenAI models
        capabilities["gpt-3.5-turbo"] = ModelCapabilities(
            name="gpt-3.5-turbo",
            provider="openai",
            context_length=16385,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0015,
            cost_per_1k_output_tokens=0.002
        )
        
        capabilities["gpt-4"] = ModelCapabilities(
            name="gpt-4",
            provider="openai",
            context_length=8192,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.03,
            cost_per_1k_output_tokens=0.06
        )
        
        capabilities["gpt-4-turbo"] = ModelCapabilities(
            name="gpt-4-turbo",
            provider="openai",
            context_length=128000,
            supports_function_calling=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03
        )
        
        return capabilities
    
    def _probe_openrouter(self) -> Dict[str, ModelCapabilities]:
        """Probe the capabilities of the OpenRouter provider.
        
        Returns:
            A dictionary mapping model names to their capabilities
        """
        capabilities = {}
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        if not api_key:
            logger.warning("OpenRouter API key not found, using default capabilities")
            return self._get_default_openrouter_capabilities()
        
        try:
            # Query the OpenRouter models endpoint
            url = "https://openrouter.ai/api/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/ravenoak/autoresearch",
                "X-Title": "Autoresearch"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Process the models data
            for model in data.get("data", []):
                model_id = model.get("id", "")
                context_length = model.get("context_length", 4096)
                pricing = model.get("pricing", {})
                
                capabilities[model_id] = ModelCapabilities(
                    name=model_id,
                    provider="openrouter",
                    context_length=context_length,
                    supports_function_calling=model.get("supports_function_calling", False),
                    supports_vision=model.get("supports_vision", False),
                    supports_streaming=model.get("supports_streaming", True),
                    cost_per_1k_input_tokens=pricing.get("input", 0.0),
                    cost_per_1k_output_tokens=pricing.get("output", 0.0)
                )
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Error probing OpenRouter capabilities: {e}")
            return self._get_default_openrouter_capabilities()
    
    def _get_default_openrouter_capabilities(self) -> Dict[str, ModelCapabilities]:
        """Get default capabilities for OpenRouter models when API probing fails.
        
        Returns:
            A dictionary mapping model names to their capabilities
        """
        capabilities = {}
        
        # Define known capabilities for some popular OpenRouter models
        capabilities["anthropic/claude-3-opus"] = ModelCapabilities(
            name="anthropic/claude-3-opus",
            provider="openrouter",
            context_length=200000,
            supports_function_calling=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.015,
            cost_per_1k_output_tokens=0.075
        )
        
        capabilities["anthropic/claude-3-sonnet"] = ModelCapabilities(
            name="anthropic/claude-3-sonnet",
            provider="openrouter",
            context_length=200000,
            supports_function_calling=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015
        )
        
        capabilities["mistralai/mistral-large"] = ModelCapabilities(
            name="mistralai/mistral-large",
            provider="openrouter",
            context_length=32768,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.008,
            cost_per_1k_output_tokens=0.024
        )
        
        return capabilities
    
    def _probe_lmstudio(self) -> Dict[str, ModelCapabilities]:
        """Probe the capabilities of the LM Studio provider.
        
        Returns:
            A dictionary mapping model names to their capabilities
        """
        capabilities = {}
        
        # LM Studio capabilities depend on the locally running model
        # We'll provide generic capabilities based on common models
        capabilities["lmstudio"] = ModelCapabilities(
            name="lmstudio",
            provider="lmstudio",
            context_length=4096,  # Depends on the model
            supports_function_calling=False,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0,  # Local models have no API costs
            cost_per_1k_output_tokens=0.0
        )
        
        return capabilities
    
    def _probe_dummy(self) -> Dict[str, ModelCapabilities]:
        """Probe the capabilities of the dummy provider.
        
        Returns:
            A dictionary mapping model names to their capabilities
        """
        capabilities = {}
        
        capabilities["dummy"] = ModelCapabilities(
            name="dummy",
            provider="dummy",
            context_length=1000,
            supports_function_calling=False,
            supports_vision=False,
            supports_streaming=False,
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0
        )
        
        return capabilities


def get_capability_prober() -> CapabilityProber:
    """Get the singleton instance of the CapabilityProber."""
    return CapabilityProber.get_instance()


def probe_all_providers() -> Dict[str, Dict[str, ModelCapabilities]]:
    """Probe the capabilities of all registered LLM providers.
    
    Returns:
        A dictionary mapping provider names to dictionaries of model capabilities
    """
    return get_capability_prober().probe_all_providers()


def get_model_capabilities(model_name: str, provider_name: Optional[str] = None) -> Optional[ModelCapabilities]:
    """Get the capabilities of a specific model.
    
    Args:
        model_name: The name of the model
        provider_name: Optional provider name to narrow the search
        
    Returns:
        The model capabilities, or None if not found
    """
    return get_capability_prober().get_model_capabilities(model_name, provider_name)