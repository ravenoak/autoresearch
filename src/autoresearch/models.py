from pydantic import BaseModel
from typing import Any, Dict, List


class QueryResponse(BaseModel):
    answer: str
    citations: List[Any]
    reasoning: List[Any]
    metrics: Dict[str, Any]
