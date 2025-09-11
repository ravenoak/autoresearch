"""Versioned API request and response models.

The API exposes stable, versioned schemas so clients can rely on a
consistent contract even as internal representations evolve. Each model
declares an explicit ``version`` field. Older versions can be marked as
deprecated to provide a migration window for clients.
"""

import warnings
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, model_validator

from ..models import BatchQueryRequest, QueryRequest, QueryResponse
from ..orchestration.reasoning import ReasoningMode

DEPRECATED_VERSIONS: Dict[str, str] = {
    "1": "Version 1 will be removed after two minor releases.",
}


class VersionedModel(BaseModel):
    """Mixin that emits warnings for deprecated API versions."""

    version: str

    @model_validator(mode="after")
    def _warn_deprecated(cls, m):  # type: ignore[override]
        message = DEPRECATED_VERSIONS.get(m.version)
        if message:
            warnings.warn(
                f"API version {m.version} is deprecated: {message}",
                DeprecationWarning,
            )
        return m


class QueryRequestV1(VersionedModel, QueryRequest):
    """API request model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1",
        description="API version for the request",
        deprecated=True,
    )


class QueryResponseV1(VersionedModel, QueryResponse):
    """API response model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1",
        description="API version for the response",
        deprecated=True,
    )


class BatchQueryRequestV1(VersionedModel, BatchQueryRequest):
    """Batch query request model for version 1."""

    version: Literal["1"] = Field(
        default="1",
        description="API version for the request",
        deprecated=True,
    )
    queries: List[QueryRequestV1]


class BatchQueryResponseV1(VersionedModel):
    """Batch query response model for version 1.

    Args:
        version: API version identifier.
    """

    version: Literal["1"] = Field(
        default="1",
        description="API version for the response",
        deprecated=True,
    )
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of results per page")
    results: List[QueryResponseV1]


class QueryRequestV2(VersionedModel, QueryRequest):
    """API request model for version 2."""

    version: Literal["2"] = Field(default="2", description="API version for the request")


class QueryResponseV2(VersionedModel, QueryResponse):
    """API response model for version 2."""

    version: Literal["2"] = Field(default="2", description="API version for the response")


class BatchQueryRequestV2(VersionedModel, BatchQueryRequest):
    """Batch query request model for version 2."""

    version: Literal["2"] = Field(default="2", description="API version for the request")
    queries: List[QueryRequestV2]


class BatchQueryResponseV2(VersionedModel):
    """Batch query response model for version 2."""

    version: Literal["2"] = Field(default="2", description="API version for the response")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of results per page")
    results: List[QueryResponseV2]


__all__ = [
    "ReasoningMode",
    "QueryRequestV1",
    "QueryResponseV1",
    "BatchQueryRequestV1",
    "BatchQueryResponseV1",
    "QueryRequestV2",
    "QueryResponseV2",
    "BatchQueryRequestV2",
    "BatchQueryResponseV2",
    "DEPRECATED_VERSIONS",
]
