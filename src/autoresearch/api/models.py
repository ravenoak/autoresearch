"""Versioned API request and response models.

The API exposes stable, versioned schemas so clients can rely on a
consistent contract even as internal representations evolve. Each model
declares an explicit ``version`` field which currently defaults to
``"1"``.
"""

from typing import List, Literal

from pydantic import BaseModel, Field

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


class BatchQueryResponseV1(BaseModel):
    """Batch query response model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1", description="API version for the response"
    )
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of results per page")
    results: List[QueryResponseV1]


__all__ = [
    "ReasoningMode",
    "QueryRequestV1",
    "QueryResponseV1",
    "BatchQueryRequestV1",
    "BatchQueryResponseV1",
]
