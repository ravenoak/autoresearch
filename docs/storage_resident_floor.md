# Deterministic storage resident floor

Autoresearch enforces a minimum number of knowledge-graph nodes when
storage runs in deterministic mode so eviction never removes every
artifact that downstream verifiers might need. The floor defaults to two
resident nodes when the release configuration omits an override. The
configuration loader restores the default whenever operators provide
`null` values through files or environment variables, ensuring command-
line overrides cannot accidentally disable the floor.
【F:src/autoresearch/config/loader.py†L300-L325】

During eviction, the storage manager computes the survivor floor and
halts deterministic sweeps as soon as the graph count reaches the
minimum. When a deterministic node budget is active, the manager
restricts the eviction batch size so survivor counts never drop below the
floor, and it records debug telemetry explaining why eviction stopped.
These guards apply equally to LRU, hybrid, and deterministic policies.
【F:src/autoresearch/storage.py†L1166-L1218】

Regression coverage exercises deterministic eviction paths and asserts
that overrides lower than the floor clamp back to the default. The unit
suite checks the survivor floor during vector-search persistence
failures, and the eviction property tests simulate deterministic runs to
prove the floor remains intact.
【F:tests/unit/test_storage_eviction.py†L173-L205】
【F:tests/unit/test_eviction.py†L213-L288】
