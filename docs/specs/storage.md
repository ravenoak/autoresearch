# Storage

The storage subsystem persists claims and enables hybrid retrieval across graph, vector, and RDF backends.

## Responsibilities
- Initialize and tear down storage backends.
- Persist claims with optional partial updates.
- Support vector similarity search.
- Maintain semantic consistency through ontology updates.

## Key APIs
- `StorageManager.setup()` – prepare graph, vector, and RDF stores.
- `StorageManager.persist_claim()` – validate and store claims across backends.
- `StorageManager.vector_search()` – return similar claims for a query embedding.
- `StorageManager.update_claim()` – modify existing claims and refresh indexes.
- `StorageManager.teardown()` – release resources and close connections.

## Traceability

- **Modules**
  - `src/autoresearch/storage.py`
- **Tests**
  - `../../tests/unit/test_storage*.py`
  - `../../tests/integration/test_*storage*.py`
  - `../../tests/behavior/features/storage_search_integration.feature`
