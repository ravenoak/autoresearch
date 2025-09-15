# Extensions

## Overview

DuckDB extension management helpers that load and verify the vector similarity
search (VSS) extension. `VSSExtensionLoader` supports offline paths, optional
network installs, Python package fallbacks, repository stubs, and stub markers.
Strict mode raises `StorageError` when no strategy succeeds.

## Algorithms

### load_extension

1. Resolve the preferred path using `ConfigLoader().config.storage`,
   falling back to `VECTOR_EXTENSION_PATH` from the environment or
   `.env.offline`.
2. Attempt to load a `.duckdb_extension` file from the resolved path and verify
   success via `verify_extension`.
3. If the filesystem load fails, inspect `ENABLE_ONLINE_EXTENSION_INSTALL`.
   - When true, run `INSTALL vss` followed by `LOAD vss` and verify the result.
   - On failure, fall back to `_load_from_package`, `_load_local_stub`, then
     `_create_stub_marker`.
   - When false, skip the network attempt and immediately evaluate the fallback
     chain.
4. If every attempt fails and `AUTORESEARCH_STRICT_EXTENSIONS=true`, raise
   `StorageError`; otherwise return `False` to indicate stub mode.

### _load_from_package

1. Import `duckdb_extension_vss` when available.
2. Prefer the package's `load()` helper; otherwise load a bundled
   `vss.duckdb_extension` file.
3. Verify extension availability before returning success.

### _load_local_stub

1. Load `extensions/vss/vss.duckdb_extension` from the repository when present.
2. Verify via `verify_extension`; warn and return `False` on failure.

### _create_stub_marker

1. Create a temporary `vss_stub` table to signal stub mode.
2. Return `True` when creation succeeds.

### verify_extension

1. Query `duckdb_extensions()` for the `vss` extension.
2. When the extension is absent, log the result and return `False` immediately
   without probing stub markers.
3. If the probe raises, log the exception and fall back to checking the
   `vss_stub` marker table before reporting success.

## Invariants

- Verification follows every load attempt to ensure a consistent success signal.
- Offline paths are resolved before attempting network downloads, preserving
  deterministic behaviour in air-gapped environments.
- Stub creation occurs only when no real extension loads, preventing accidental
  downgrades.
- Strict mode raises `StorageError` after all strategies fail, surfacing
  configuration issues early.

## Proof Sketch

The loader enumerates a finite sequence of fallbacks, each guarded by
`verify_extension`. Because verification requires either `duckdb_extensions()`
listing or the stub marker, clients never observe a "success" state without a
working extension or explicit stub. Tests inject failures for each step,
confirming that strict mode raises and that stub markers appear only when
necessary.

## Simulation Expectations

Unit tests cover filesystem paths, `.env.offline` values, package-based loads,
network failures, and stub creation. Offline setup scripts mimic these flows and
record the chosen strategy, demonstrating reproducible behaviour across
environments.

## Traceability

- Modules
  - [src/autoresearch/extensions.py][m1]
- Tests
  - [tests/unit/test_duckdb_storage_backend.py][t1]
  - [tests/unit/test_duckdb_storage_backend_extended.py][t2]
  - [tests/unit/test_vss_extension_loader.py][t3]

[m1]: ../../src/autoresearch/extensions.py
[t1]: ../../tests/unit/test_duckdb_storage_backend.py
[t2]: ../../tests/unit/test_duckdb_storage_backend_extended.py
[t3]: ../../tests/unit/test_vss_extension_loader.py
