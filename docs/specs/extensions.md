# Extensions

## Overview

DuckDB extension management helpers that load and verify the vector similarity
search (VSS) extension. `VSSExtensionLoader` orchestrates offline-first path
resolution, optional network installs, Python package fallbacks, repository
stubs, and stub markers. Strict mode raises `StorageError` when no strategy
succeeds.

## Loader strategy

### Offline path discovery

1. Use `ConfigLoader().config.storage.vector_extension_path` when set.
2. Otherwise call `_env_extension_path()` to read `VECTOR_EXTENSION_PATH` from
   the environment or `.env.offline`.
3. Resolve the candidate path, warn when the suffix is not
   `.duckdb_extension` or when the file is missing, and attempt
   `LOAD '<path>'`.
4. Invoke `verify_extension` to confirm success before returning; failures
   fall through to the remaining strategies.

### Controlled network install

1. Evaluate `ENABLE_ONLINE_EXTENSION_INSTALL` (default `true`).
2. If enabled, execute `INSTALL vss` then `LOAD vss`.
3. Verify the extension; errors log the failure and trigger the offline
   fallback ladder.
4. When disabled, skip network calls entirely so air-gapped environments do
   not block on retries.

### Offline fallback ladder

1. `_load_from_package` imports `duckdb_extension_vss`, preferring its
   `load()` helper before trying a bundled `vss.duckdb_extension`.
2. `_load_local_stub` loads `extensions/vss/vss.duckdb_extension` that the
   repository or provisioning scripts populate.
3. `_create_stub_marker` creates a temporary `vss_stub` table so downstream
   code can detect stubbed mode.
4. Each step calls `verify_extension`; strict mode raises `StorageError`
   after the ladder reports failure so CI surfaces misconfiguration quickly.

## Verification

- `verify_extension` queries `duckdb_extensions()` for a `vss` row and logs
  the outcome. When the probe raises it checks for the `vss_stub` marker.
- Callers can disable verbose logging to silence normal success messages.
- `tests/unit/test_vss_extension_loader.py` mocks each branch to assert the
  correct return value and strict-mode behaviour, ensuring the verification
  contract is enforced.[t3]

## Offline determinism

- `.env.offline` caches `VECTOR_EXTENSION_PATH`, letting the loader reuse
  binaries without network access between runs.
- `scripts/download_duckdb_extensions.py` records that path and mirrors the
  stub shipped in `extensions/vss/`, aligning developer machines with CI
  caches.[s2]
- `scripts/smoke_test.py` exercises the offline ladder during
  `check_storage()` to confirm stub creation and logging when the real
  extension is absent.[s1]

## Proof sketch

The loader enumerates a finite sequence of fallbacks guarded by
`verify_extension`. Because verification only succeeds after loading a real
extension or recording the stub marker, downstream callers never observe a
false positive. Unit tests simulate filesystem paths, online installs, strict
mode, and stub creation to cover the decision tree.[t3] Storage backend tests
propagate failures to user-facing APIs, confirming strict mode raises early
and non-strict mode preserves stub access.[t1][t2]

## Simulation expectations

- Rebuilds that pre-run `scripts/download_duckdb_extensions.py` should record
  a deterministic offline path so CI and local runs agree on binaries.[s2]
- `scripts/smoke_test.py` validates offline startup by triggering the loader
  through `StorageManager.setup()` and reporting whether stub mode engaged.[s1]

## Traceability

- Modules
  - [src/autoresearch/extensions.py][m1]
- Tests
  - [tests/unit/test_duckdb_storage_backend.py][t1]
  - [tests/unit/test_duckdb_storage_backend_extended.py][t2]
  - [tests/unit/test_vss_extension_loader.py][t3]
- Simulations
  - [scripts/smoke_test.py][s1]
  - [scripts/download_duckdb_extensions.py][s2]

[m1]: ../../src/autoresearch/extensions.py
[t1]: ../../tests/unit/test_duckdb_storage_backend.py
[t2]: ../../tests/unit/test_duckdb_storage_backend_extended.py
[t3]: ../../tests/unit/test_vss_extension_loader.py
[s1]: ../../scripts/smoke_test.py
[s2]: ../../scripts/download_duckdb_extensions.py
