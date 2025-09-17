# Release Notes

Autoresearch is a local-first research assistant that coordinates multiple
agents to produce evidence-backed answers and stores data on the user's
machine.

## 0.1.0a1 (unreleased)

Planned for **2026-09-15**. Dependency pins: `fastapi>=0.116.1` and
`slowapi==0.1.9`.

### Capabilities

- Coordinates dialectical, contrarian, and fact-checking agents to synthesize
  answers.
- Provides a command-line interface and HTTP API.
- Uses local databases for searches and knowledge graphs.
- Manages dependencies with uv and supports optional extras for features like
  rate limiting.
- Supports direct, dialectical, and chain-of-thought modes for queries (see
  [agent system](agent_system.md)).
- Pluggable search and storage backends enable local-first workflows (see
  [search backends](search_backends.md) and [storage](storage.md)).
- Quickstart and advanced guides help explore features (see [quickstart
  guides](quickstart_guides.md) and [advanced usage](advanced_usage.md)).
- HTTP API authenticates using configured API keys or bearer tokens. Any
  provided credential must be valid or the request receives a 401 response.

### Known Limitations

- Fresh environments omit the Go Task CLI, so `task --version` reports
  `command not found` until Task is installed (for example via
  `scripts/setup.sh`).
- `uv run mkdocs build` fails with `No such file or directory` until the docs
  extras install `mkdocs`; run `task docs` or `uv run --extra docs`
  `mkdocs build` beforehand.
- `uv run pytest tests/unit -q` aborts when monitor metrics tests patch
  `ConfigLoader.load_config` to objects without `storage`; the autouse
  `cleanup_storage` fixture raises `AttributeError` during teardown.

For installation and usage instructions see the README.

### Open issues

- handle-config-loader-patches-in-storage-teardown
- prepare-first-alpha-release
- resolve-deprecation-warnings-in-tests
- resolve-resource-tracker-errors-in-verify
- restore-distributed-coordination-simulation-exports

## Packaging Logs

### Build

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for wheel...
* Building wheel...
Successfully built autoresearch-0.1.0a1.tar.gz and autoresearch-0.1.0a1-py3-none-any.whl
```

### Test Publishing

Dry-run upload using ``scripts/publish_dev.py --dry-run --repository testpypi``
on 2025-08-29 produced:

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for wheel...
* Building wheel...
Successfully built autoresearch-0.1.0a1.tar.gz and autoresearch-0.1.0a1-py3-none-any.whl
Dry run selected; skipping upload
```
The build completed and, as expected for a dry run, the upload was skipped.
