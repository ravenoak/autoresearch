from __future__ import annotations

from typing import Any


OWLRL_Semantics: object
RDFS_Semantics: object


class DeductiveClosure:
    def __init__(self, semantics: object, *args: Any, **kwargs: Any) -> None: ...

    def expand(self, graph: Any) -> None: ...


__all__ = ["DeductiveClosure", "OWLRL_Semantics", "RDFS_Semantics"]
