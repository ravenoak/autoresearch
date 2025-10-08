from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

VSS_AVAILABLE: bool
def reset_limiter_state() -> None: ...
def find_future_annotations_import_violations(
    paths: Iterable[Path] | None = ...,
) -> list[str]: ...
def enforce_future_annotations_import_order(paths: Iterable[Path] | None = ...) -> None: ...
