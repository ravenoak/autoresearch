"""
This module provides data models for Autoresearch.

It contains Pydantic models that define the structure of data used throughout the application,
particularly for query responses and related data structures.
"""

from pydantic import BaseModel
from typing import Any, Dict, List


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
