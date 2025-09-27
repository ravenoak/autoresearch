"""This module provides data models for Autoresearch.

See ``docs/algorithms/models.md`` for validation, hot reload, and schema
guarantees.

It contains Pydantic models that define the structure of data used throughout
the application, particularly for query requests, responses, and related data
structures.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReasoningMode(str, Enum):
    """
    Enumeration of available reasoning modes.

    Attributes:
        DIRECT: Uses only the Synthesizer agent
        DIALECTICAL: Rotates through agents in a thesis→antithesis→synthesis cycle
        CHAIN_OF_THOUGHT: Loops the Synthesizer agent
    """

    DIRECT = "direct"
    DIALECTICAL = "dialectical"
    CHAIN_OF_THOUGHT = "chain-of-thought"


class QueryRequest(BaseModel):
    """
    Represents a query request to the Autoresearch system.

    This class defines the standard format for requests sent to the orchestration system.
    It includes the query string and optional configuration parameters.

    Attributes:
        query (str): The natural language query to process.
        reasoning_mode (Optional[ReasoningMode]): The reasoning mode to use for this query.
        loops (Optional[int]): The number of reasoning loops to perform.
        llm_backend (Optional[str]): The LLM backend to use for this query.
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
    """Structured response returned by the orchestration system.

    The response captures the synthesized answer along with traceability
    artefacts that downstream clients can audit. Claim verification metadata
    is represented by the ``claim_audits`` field which mirrors the
    :class:`~autoresearch.storage.ClaimAuditRecord` payload structure.

    Attributes:
        query: The original query that produced this response, if available.
        answer: The final answer synthesized by the agent cohort.
        citations: References surfaced during retrieval.
        reasoning: Ordered reasoning steps exchanged between agents.
        metrics: Execution metrics describing latency, token usage, etc.
        claim_audits: Verification metadata for each evaluated claim. Each
            entry is a mapping containing ``claim_id``, ``status``,
            ``entailment_score``, ``entailment_variance``, ``instability_flag``,
            ``sample_size``, ``sources``, ``notes``, and ``created_at``.
    """

    query: Optional[str] = Field(
        None, description="The original query that produced this response"
    )
    answer: str
    citations: List[Any]
    reasoning: List[Any]
    metrics: Dict[str, Any]
    claim_audits: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="FEVER-style verification metadata for individual claims",
    )
    task_graph: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured planner output describing sub-questions and tool routing",
    )
    react_traces: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sequenced ReAct traces captured during task execution",
    )


class BatchQueryRequest(BaseModel):
    """Request model for executing multiple queries."""

    queries: List[QueryRequest] = Field(..., description="List of queries to execute sequentially")
