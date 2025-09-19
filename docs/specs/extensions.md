# Extensions

## Overview

DuckDB extension management helpers that load and verify the vector similarity
search (VSS) extension. `VSSExtensionLoader` orchestrates offline-first path
resolution, optional network installs, Python package fallbacks, repository
stubs, and stub markers. Strict mode (`AUTORESEARCH_STRICT_EXTENSIONS=true`)
raises `StorageError` when no strategy succeeds, and unexpected exceptions
propagate so operators see actionable traces.

## Algorithms

### Offline Ladder

1. Use `ConfigLoader().config.storage.vector_extension_path` when it is set.
2. Otherwise call `_env_extension_path()` to read `VECTOR_EXTENSION_PATH` from
   the environment or `.env.offline`.
3. Resolve the candidate path, warning when the suffix is not
   `.duckdb_extension` or the file is missing so operators can correct
   provisioning issues.
4. Attempt `LOAD '<path>'` when the file exists and invoke `verify_extension`
   before returning. DuckDB-specific errors fall through to the remaining
   strategies while unexpected exceptions bubble up for visibility.
5. When the load is skipped or raises `duckdb.Error`, walk the fallback ladder:
   - `_load_from_package` imports `duckdb_extension_vss`, preferring its
     `load()` helper before trying a bundled `vss.duckdb_extension`, and calls
     `verify_extension` after each attempt.
   - `_load_local_stub` loads `extensions/vss/vss.duckdb_extension` populated by
     the repository or provisioning scripts, again verifying the result.
   - `_create_stub_marker` creates a temporary `vss_stub` table so downstream
     code can detect stubbed mode via `verify_extension`.
6. After all attempts fail, strict mode raises `StorageError`; relaxed mode
   returns `False` so callers can continue with stubbed reads and degrade
   gracefully.

### Network Ladder

1. Evaluate `ENABLE_ONLINE_EXTENSION_INSTALL` (default `true`).
2. If enabled, execute `INSTALL vss` then `LOAD vss`, propagating non-DuckDB
   errors to preserve diagnostics while `duckdb.Error` triggers the offline
   ladder.
3. Verify the extension. A passing probe sets `extension_loaded`; a failure
   returns `False` but leaves strict-versus-relaxed handling to the offline
   ladder.
4. When disabled, skip network calls entirely so air-gapped environments enter
   the offline ladder immediately.

## Verification

- `verify_extension` queries `duckdb_extensions()` for a `vss` row and logs
  the outcome. When the probe raises it checks for the `vss_stub` marker via
  `information_schema.tables`.
- Callers can disable verbose logging to silence normal success messages.
- `tests/unit/test_vss_extension_loader.py` exercises filesystem loads,
  install fallbacks, stub creation, strict mode, and non-DuckDB propagation to
  ensure the verification contract stays intact.[t3]

## Invariants

- Strict mode (`AUTORESEARCH_STRICT_EXTENSIONS=true`) raises `StorageError`
  after every ladder fails, preventing the application from continuing without
  a verified extension.
- Relaxed mode records stub markers and returns `False`, signalling downstream
  callers to operate in degraded read-only mode without masking missing
  extensions.
- Verification always follows a load attempt, so neither ladder can report a
  success without confirming the DuckDB extension or the stub marker.

## Offline Determinism

- `.env.offline` caches `VECTOR_EXTENSION_PATH`, letting the loader reuse
  binaries without network access between runs.
- `scripts/download_duckdb_extensions.py` records that path and mirrors the
  stub shipped in `extensions/vss/`, aligning developer machines with CI
  caches.[s2]
- `scripts/smoke_test.py` exercises the offline ladder during
  `check_storage()` to confirm stub creation, stub marker detection, and
  logging when the real extension is absent.[s1]

## Proof Sketch

The loader enumerates a finite sequence of fallbacks guarded by
`verify_extension`. Because verification only succeeds after loading a real
extension or recording the stub marker, downstream callers never observe a
false positive. Unit tests simulate filesystem paths, online installs,
DuckDB-only error swallowing, strict mode, and stub creation to cover the
decision tree.[t3] Storage backend tests propagate failures to user-facing
APIs, confirming strict mode raises early and non-strict mode preserves stub
access.[t1][t2]

## Simulation Expectations

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
