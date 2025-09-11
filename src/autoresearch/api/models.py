"""Versioned API request and response models.

The API exposes stable, versioned schemas so clients can rely on a
consistent contract even as internal representations evolve. Each model
declares an explicit ``version`` field which currently defaults to
``"1"``.
"""

from typing import ClassVar, List

from pydantic import BaseModel, Field

from ..models import BatchQueryRequest, QueryRequest, QueryResponse
from ..orchestration.reasoning import ReasoningMode
from .utils import DEPRECATED_VERSIONS, SUPPORTED_VERSIONS


class VersionedModel(BaseModel):
    """Base class for versioned API schemas.

    The ``version`` field is unrestricted at validation time so the router
    can return custom HTTP errors for deprecated or unknown versions. The
    OpenAPI schema enumerates supported versions and marks deprecated
    models accordingly.
    """

    __version__: ClassVar[str | None] = None
    version: str = Field(description="API version identifier")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):  # type: ignore[override]
        schema = handler(core_schema)
        enum = sorted(SUPPORTED_VERSIONS | DEPRECATED_VERSIONS)
        schema["properties"]["version"]["enum"] = enum
        if cls.__version__ in DEPRECATED_VERSIONS:
            schema["deprecated"] = True
        return schema


class QueryRequestV1(VersionedModel, QueryRequest):
    """API request model for version 1."""

    __version__ = "1"
    version: str = Field(default="1", description="API version for the request")


class QueryResponseV1(VersionedModel, QueryResponse):
    """API response model for version 1."""

    __version__ = "1"
    version: str = Field(default="1", description="API version for the response")


class BatchQueryRequestV1(VersionedModel, BatchQueryRequest):
    """Batch query request model for version 1."""

    __version__ = "1"
    version: str = Field(default="1", description="API version for the request")
    queries: List[QueryRequestV1]


class BatchQueryResponseV1(VersionedModel):
    """Batch query response model for version 1."""

    __version__ = "1"
    version: str = Field(default="1", description="API version for the response")
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
