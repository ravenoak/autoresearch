# Package Initialization

Central package entry that wires version metadata and optional distributed
features.

## Invariants

- `__version__` reflects the installed package version.
- `pydantic.root_model` is registered to avoid import errors in SDKs.
- Distributed attributes load lazily through `__getattr__`.

## References

- [`__init__.py`](../../src/autoresearch/__init__.py)
