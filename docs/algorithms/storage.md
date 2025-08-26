# Storage

The storage layer maintains the project's hybrid persistence model.
It uses a helper called `initialize_storage()` to bootstrap the DuckDB
schema. The helper runs the normal setup routine and then creates the
`nodes`, `edges`, `embeddings`, and `metadata` tables if they are
missing.

This bootstrapping step is required when using an empty or in-memory
database. Tests call the helper from `tests/conftest.py` so each run starts
with a valid schema. Applications may invoke it on startup as well. The
creation statements use `IF NOT EXISTS`, making repeated calls safe.
