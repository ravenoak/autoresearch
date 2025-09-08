"""Versioned API request and response models.

The API exposes stable, versioned schemas so clients can rely on a
consistent contract even as internal representations evolve. Each model
declares an explicit ``version`` field which currently defaults to
``"1"``.
"""

from typing import Literal, List

from pydantic import Field

from ..models import BatchQueryRequest, QueryRequest, QueryResponse
from ..orchestration.reasoning import ReasoningMode


class QueryRequestV1(QueryRequest):
    """API request model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1", description="API version for the request"
    )


class QueryResponseV1(QueryResponse):
    """API response model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1", description="API version for the response"
    )


class BatchQueryRequestV1(BatchQueryRequest):
    """Batch query request model for version 1."""

    version: Literal["1"] = Field(
        default="1", description="API version for the request"
    )
    queries: List[QueryRequestV1]


__all__ = [
    "ReasoningMode",
    "QueryRequestV1",
    "QueryResponseV1",
    "BatchQueryRequestV1",
]
