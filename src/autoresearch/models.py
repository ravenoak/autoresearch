"""Autoresearch data models.

This module defines the Pydantic types that structure requests and responses
shared across the orchestration stack. See ``docs/algorithms/models.md`` for
the canonical schema definitions, hot-reload behaviour, and validation rules.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReasoningMode(str, Enum):
    """Enumeration of available reasoning modes.

    Attributes:
        DIRECT: Execute with the Synthesizer agent alone.
        DIALECTICAL: Rotate through thesis→antithesis→synthesis roles.
        CHAIN_OF_THOUGHT: Loop the Synthesizer agent for iterative reasoning.
    """

    DIRECT = "direct"
    DIALECTICAL = "dialectical"
    CHAIN_OF_THOUGHT = "chain-of-thought"


class QueryRequest(BaseModel):
    """Represent a query request delivered to the orchestration system.

    Attributes:
        query: Natural-language question to investigate.
        reasoning_mode: Optional reasoning strategy for the session.
        loops: Optional number of reasoning loops to perform.
        llm_backend: Optional large language model backend override.
        webhook_url: Optional HTTP endpoint for asynchronous callbacks.
    """

    query: str = Field(..., description="The natural language query to process")
    reasoning_mode: Optional[ReasoningMode] = Field(
        None,
        description="The reasoning mode to use (direct, dialectical, chain-of-thought)",
    )
    loops: Optional[int] = Field(
        None, description="The number of reasoning loops to perform", ge=1, le=10
    )
    llm_backend: Optional[str] = Field(
        None, description="The LLM backend to use (e.g., 'openai', 'lmstudio')"
    )
    webhook_url: Optional[str] = Field(
        None,
        description="Optional HTTP URL that will receive the final QueryResponse",
    )


class QueryResponse(BaseModel):
    """Represents a structured response returned by the orchestration system.

    The response captures the synthesized answer alongside audit trails that
    clients can interrogate for provenance.

    Attributes:
        query: Original query that initiated the session, when available.
        answer: Final answer synthesized by the agent cohort.
        citations: Retrieval references associated with the answer.
        reasoning: Ordered reasoning steps exchanged between agents.
        metrics: Execution metrics such as latency and token usage.
        warnings: Structured warnings captured during orchestration runs.
        claim_audits: Verification metadata mirroring
            :class:`~autoresearch.storage.ClaimAuditRecord` entries, including
            per-claim provenance namespaces (``retrieval``, ``backoff``, and
            ``evidence``) plus audit statistics.
        task_graph: Optional planner output describing sub-questions and tool
            routing metadata.
        react_traces: Sequenced ReAct traces captured during execution.
        state_id: Optional identifier for retrieving the QueryState snapshot.
    """

    query: Optional[str] = Field(
        None, description="The original query that produced this response"
    )
    answer: str
    citations: List[Any]
    reasoning: List[Any]
    metrics: Dict[str, Any]
    warnings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Structured warnings captured during orchestration, including "
            "claim-level remediation hints"
        ),
    )
    claim_audits: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "FEVER-style verification metadata for individual claims, including "
            "structured provenance with retrieval queries, backoff counters, "
            "and evidence identifiers"
        ),
    )
    task_graph: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured planner output describing sub-questions and tool routing",
    )
    react_traces: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sequenced ReAct traces captured during task execution",
    )
    state_id: Optional[str] = Field(
        default=None,
        description="Identifier for retrieving the underlying QueryState snapshot",
    )


class BatchQueryRequest(BaseModel):
    """Request model for executing multiple queries."""

    queries: tuple[QueryRequest, ...] = Field(
        ...,
        description="Tuple of queries to execute sequentially",
    )
