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

## TestPyPI authentication

Generate an API token from [TestPyPI](https://test.pypi.org/manage/account/)
and store it securely:

1. Sign in and open **Account settings → API tokens**.
2. Create a token scoped to the project or your entire account.
3. Export the token as ``TWINE_API_TOKEN`` or set
   ``TWINE_USERNAME=__token__`` and ``TWINE_PASSWORD=<token>``.

If the upload fails with a 403 response:

- Confirm you are using a TestPyPI token rather than a PyPI token.
- Ensure the token has permission to upload the project.
- Regenerate the token if it may be revoked or expired.

- Release to PyPI once the TestPyPI upload is verified.

  ```bash
  uv run twine upload dist/*
  ```

## Container images

Build and push multi-arch images with Buildx:

```bash
bash scripts/release_images.sh ghcr.io/OWNER v1.2.3
```

The script publishes Linux (amd64, arm64), macOS, and Windows images.

- Configure authentication in `config.yml` using `api.api_key`,
  `api.api_keys`, or `api.bearer_token`. Any supplied credential must be valid
  or the server returns a 401 error.

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

