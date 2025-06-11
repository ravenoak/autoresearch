"""Reasoning mode definitions and protocol interface."""
from __future__ import annotations

from enum import Enum
from typing import Protocol, TYPE_CHECKING

from ..models import QueryResponse

if TYPE_CHECKING:
    from ..config import ConfigModel


class ReasoningMode(str, Enum):
    """Supported reasoning modes."""

    DIRECT = "direct"
    DIALECTICAL = "dialectical"
    CHAIN_OF_THOUGHT = "chain-of-thought"


class ReasoningStrategy(Protocol):
    """Interface for reasoning strategies."""

    def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
        """Execute reasoning for a query."""
        raise NotImplementedError
