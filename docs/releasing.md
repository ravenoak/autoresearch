# Releasing

Follow these steps to publish a new version of Autoresearch.

- Update the version in `pyproject.toml` and
  `src/autoresearch/__init__.py`. Commit the change and tag the release.
- Validate the package builds.

  ```bash
  uv run python -m build
  uv run scripts/publish_dev.py --dry-run
  ```

- Upload the validated build to TestPyPI.

  ```bash
  uv run scripts/publish_dev.py
  ```

- Release to PyPI once the TestPyPI upload is verified.

  ```bash
  uv run twine upload dist/*
  ```

- If DuckDB extensions fail to download during packaging, the build
  continues with a warning. The download script falls back to
  `VECTOR_EXTENSION_PATH` defined in `.env.offline` and copies the
  referenced file into `extensions/vss/`. When no offline copy is
  available, it creates a stub `vss.duckdb_extension` so packaging and
  tests proceed without vector search. Run the script manually when
  needed:

  ```bash
  uv run python scripts/download_duckdb_extensions.py --output-dir ./extensions
  ```

  At runtime, if the extension remains unavailable, the storage backend
  reads `.env.offline` for a `VECTOR_EXTENSION_PATH` fallback before
  continuing without vector search. `scripts/setup.sh` mirrors this
  behavior by writing a stub file when no extension is present.

