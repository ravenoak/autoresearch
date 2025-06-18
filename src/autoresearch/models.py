"""
This module provides data models for Autoresearch.

It contains Pydantic models that define the structure of data used throughout the application,
particularly for query requests, responses, and related data structures.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


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


class QueryResponse(BaseModel):
    """
    Represents a structured response to a user query.

    This class defines the standard format for responses returned by the orchestration system.
    It includes the final answer, supporting citations, reasoning steps, and execution metrics.

    Attributes:
        answer (str): The final answer to the user's query.
        citations (List[Any]): A list of citations or sources that support the answer.
        reasoning (List[Any]): A list of reasoning steps or explanations that led to the answer.
        metrics (Dict[str, Any]): Performance and execution metrics for the query processing.
    """

    answer: str
    citations: List[Any]
    reasoning: List[Any]
    metrics: Dict[str, Any]
