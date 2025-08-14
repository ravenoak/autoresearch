# Storage

The storage system is responsible for persisting claims and supporting vector search. It uses a hybrid approach with multiple backends:

1. **NetworkX Graph** - For storing the knowledge graph structure
2. **DuckDB** - For efficient vector storage and similarity search
3. **RDFLib** - For semantic storage and querying

## Architecture

The storage component consists of several key classes:

- **StorageManager** - Main class for interacting with the storage system
- **Global Storage State** - Maintains the state of the storage system
- **StorageConfig** - Configuration for the storage system
- **StorageError** - Error hierarchy for storage-related errors

The relationships between these classes and their external dependencies are documented in `docs/diagrams/storage.puml`.

## Storage Flow

1. The `setup()` method initializes the storage backends
2. The `persist_claim()` method validates and stores claims in all backends
3. The `vector_search()` method finds similar claims using vector similarity
4. The `teardown()` method closes connections and cleans up resources

## Incremental Updates

`StorageManager.persist_claim()` supports partial updates. When a claim with an
existing ID is persisted with `partial_update=True`, only the provided fields are
merged into the stored record. Vector embeddings are inserted into DuckDB and
the HNSW index is refreshed using `StorageManager.refresh_vector_index()`. RDF
triples are updated with `StorageManager.update_rdf_claim()` so that semantic
queries remain consistent. The update operation now also triggers ontology
reasoning so inferred relationships are immediately available for queries.

### Updating Existing Claims

Existing claims can be modified directly using `StorageManager.update_claim()`.
Set `partial_update=True` to merge only the supplied fields or `False` to
replace the stored record entirely. The method automatically refreshes the
vector index and updates RDF triples so all search modalities remain in sync.

## Local Data Persistence

Search backends that operate on the filesystem or Git repositories generate
claims from extracted text. Each snippet from a file becomes a claim node with a
`file_path` attribute pointing to its location on disk. Git backends additionally
record the `commit_hash` so that claims reference the exact revision. This
metadata is stored alongside the claim `content` and is available through the
regular storage APIs.

## Eviction Policies

The storage system supports automatic eviction of claims when the memory usage exceeds the configured budget:

1. **LRU (Least Recently Used)** - Evicts the least recently accessed claims
2. **Score** - Evicts claims with the lowest relevance scores
3. **Hybrid** - Combines recency and confidence score for balanced eviction
4. **Adaptive** - Dynamically chooses the best policy based on usage patterns
5. **Priority** - Evicts nodes using configurable priority tiers

The eviction process is triggered automatically by the `_enforce_ram_budget()` method when the memory usage exceeds the configured budget.

## Adding Custom Storage Backends

To add a custom storage backend:

1. Extend the `StorageManager` class with methods for your backend
2. Add initialization in `setup()`
3. Add cleanup in `teardown()`
4. Add persistence in `persist_claim()`
5. Update the configuration schema in `ConfigModel`

## Vector Search Tuning

The `StorageConfig` section of `autoresearch.toml` exposes parameters to
control vector search performance.  Adjust these to trade off recall and
speed:

```toml
[storage]
hnsw_m = 16               # Higher improves recall but uses more memory
hnsw_ef_construction = 200  # Controls index build quality
hnsw_metric = "l2sq"        # Distance metric ("ip", "cosine", or "l2sq")
hnsw_ef_search = 32         # Number of neighbors explored during search
hnsw_auto_tune = true       # Automatically adjust ef_search for large indexes
```

After changing these values run:

```python
from autoresearch.storage import StorageManager
StorageManager.create_hnsw_index()
```

to rebuild the index with the new parameters. The index is also automatically
refreshed whenever a claim with an embedding is persisted or updated, so in
most workflows no manual step is required.

The `vector_search_performance.feature` BDD scenario demonstrates how these
settings impact search latency.

## RDF Storage Backends

RDFLib provides two supported backends: `sqlite` (the default) and `berkeleydb`.
When using the `sqlite` backend the **SQLAlchemy** plugin is required. The
storage manager constructs a connection string in the format:

```text
sqlite:///path/to/rdf_store
```

Make sure the `rdflib-sqlalchemy` package is installed so that RDFLib can load
the SQLAlchemy plugin and open the SQLite store correctly.

## Troubleshooting

### HNSW Index Creation Error

If you encounter an error like:

```
Failed to create HNSW index: Binder Error: HNSW indexes can only be created in in-memory databases, or when the configuration option 'hnsw_enable_experimental_persistence' is set to true.
```

This occurs because HNSW indexes in DuckDB require special handling for persistent databases. The system now automatically enables experimental persistence for HNSW indexes, but if you're using an older version or a custom implementation, you may need to:

1. Ensure you're using the latest version of the code
2. Manually set the configuration option before creating the index:
   ```python
   conn.execute("SET hnsw_enable_experimental_persistence=true")
   ```

### RDF Store Plugin Error

If you encounter an error like:

```
Failed to open RDF store: No plugin registered for (SQLAlchemy, <class 'rdflib.store.Store'>)
```

This indicates that the RDFLib SQLAlchemy plugin is not properly registered. To fix this:

1. Ensure the `rdflib-sqlalchemy` package is installed:
   ```bash
   pip install rdflib-sqlalchemy
   ```

2. Ensure it appears in your `pyproject.toml` dependencies:
   ```toml
   [project.dependencies]
   rdflib-sqlalchemy = "^0.5.0"
   ```

3. If the error persists, try installing additional dependencies:
   ```bash
   pip install sqlalchemy
   ```

4. For development environments, you can also use the in-memory store by setting:
   ```toml
   [storage]
   rdf_backend = "memory"
   ```

## Ontology Reasoning and Visualization

The RDF store supports optional ontology-based reasoning using the
`owlrl` package, the lightweight `rdfs` reasoner, or a custom engine.
Configure the desired reasoner and timeout with

```toml
[storage]
# Use "rdfs" in tests for faster execution
ontology_reasoner = "rdfs"
ontology_reasoner_timeout = 5          # seconds

# In production switch to OWL-RL and raise the timeout
# ontology_reasoner = "owlrl"
# ontology_reasoner_timeout = 30

ontology_reasoner_max_triples = 100000 # skip reasoning for larger graphs
```

Behavior tests use the lightweight `rdfs` reasoner by default to keep test
execution fast. Production deployments can select the more expressive `owlrl`
engine (or another custom reasoner) and increase
`ontology_reasoner_timeout` when full OWL‑RL reasoning is required.

The following tutorial walks through a typical ontology workflow.

1. **Load an ontology file** to add schema triples:

   ```python
   from autoresearch.storage import StorageManager

   StorageManager.load_ontology("ontology.ttl")
   ```

2. **Infer relations** to materialize OWL‑RL inferences:

   ```python
   StorageManager.infer_relations()
   ```

3. **Query the ontology** using SPARQL:

   ```python
   results = StorageManager.query_ontology(
       "SELECT ?s WHERE { ?s a <http://example.com/B> }"
   )
   ```

4. **Run SPARQL queries with reasoning** directly from the CLI:

   ```bash
   autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"
   ```

5. **Query with reasoning programmatically** using a custom engine:

   ```python
   results = StorageManager.query_with_reasoning(
       "SELECT ?s WHERE { ?s a <http://example.com/B> }",
       engine="owlrl"
   )
   ```

6. **Visualize the graph** as a PNG image:

   ```bash
   autoresearch visualize-rdf graph.png
   ```

The command writes `graph.png` containing a simple diagram of all triples.

## Kuzu Graph Storage

Autoresearch can optionally persist claims to a [Kuzu](https://kuzudb.com/) database. Enable this backend with:

```toml
[storage]
use_kuzu = true
kuzu_path = "knowledge.kuzu"
```

When enabled each claim is inserted into a `Claim` node table. Basic metrics track query counts and execution time via Prometheus. The Kuzu database is created automatically at the configured path.

