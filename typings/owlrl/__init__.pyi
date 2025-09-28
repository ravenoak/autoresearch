from typing import Any


class OWLRL_Semantics: ...


class RDFS_Semantics: ...


class DeductiveClosure:
    def __init__(self, semantics: type[Any]) -> None: ...

    def expand(self, graph: Any) -> None: ...


__all__ = ["DeductiveClosure", "OWLRL_Semantics", "RDFS_Semantics"]
