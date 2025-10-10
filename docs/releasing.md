# Releasing

Follow these steps to publish a new version of Autoresearch.

## Preparing the environment

`task` commands require the Go Task CLI. Fresh shells may not expose the
binary on `PATH`; see [STATUS.md][status-cli] for the current availability
notes. Before running any release workflow, pick one of the supported helpers:

- **Source the PATH helper.** Run `./scripts/setup.sh` once; it now writes
  `.autoresearch/path.sh` with both `.venv/bin` and the detected Task
  installation directory so new shells expose the CLI automatically. Start
  new terminals with `eval "$(./scripts/setup.sh --print-path)"` to load
  Task without rerunning the installer.
- **Use `uv run task …` wrappers.** The `uv` launcher injects the packaged
  Task CLI, so commands like `uv run task release:alpha` work even when the
  helper is not sourced.

- Run `uv run task release:alpha` to automate the alpha readiness sweep before
  tagging. The default invocation now syncs only the `dev-minimal` and `test`
  extras before running lint, type checks, spec lint, `task verify`,
  `task coverage`, `python -m build`, `twine check`, and the TestPyPI dry run.
  The verify and coverage subtasks stay on the same baseline footprint, so
  suites that require optional extras are skipped unless you opt in. Pass
  `EXTRAS="full"` to add the optional extras set (`nlp`, `ui`, `vss`, `git`,
  `distributed`, `analysis`, `llm`, `parsers`, and `build`) and append values
  like `gpu` as needed (for example, `EXTRAS="full gpu"`).
- Update the version and release date in `pyproject.toml`
  (`project.version`, `tool.autoresearch.release_date`),
  `src/autoresearch/__init__.py` (`__version__`, `__release_date__`), and the
  top entry in `CHANGELOG.md`. Run `task check-release-metadata` to confirm the
  guard passes; it also runs as part of `task check`, `task verify`, and
  `task release:alpha`. Commit the change and tag the release.
- Validate the package builds if you need to re-run individual steps.

  ```bash
  uv run python -m build
  uv run scripts/publish_dev.py --dry-run
  ```

- Build the documentation with `task docs` (or `uv run --extra docs mkdocs
  build`) to ensure the site compiles with the docs extras.

- Upload the validated build to TestPyPI.

  ```bash
  uv run scripts/publish_dev.py
  ```

[status-cli]:
  https://github.com/autoresearch/autoresearch/blob/main/STATUS.md#status

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

