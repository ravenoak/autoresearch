# Caching

Autoresearch caches search results and text snippets using a TinyDB database. The cache is part of the storage layer shown in the architecture diagram and helps avoid repeated external lookups.

`src/autoresearch/cache.py` exposes helpers to store and retrieve cached data. `Search.external_lookup` checks this cache before contacting any backend.

## Local Indexes

When the `local_file` or `local_git` search backends are enabled,
Autoresearch builds a local index of the files it scans.  Each text
snippet is stored in DuckDB with vector embeddings for semantic search
and BM25 scores for lexical ranking.  The index allows queries to
reference the exact file path or commit when matching content from the
local machine.

Initial indexing happens automatically the first time these backends run.
You can refresh the index at any time by executing:

```bash
poetry run python scripts/smoke_test.py
```

This script calls `StorageManager.create_hnsw_index()` to rebuild the
vector index.  Running it after updating your repositories or document
directories ensures the stored embeddings remain in sync.
