# Release Notes

Autoresearch is a local-first research assistant that coordinates multiple
agents to produce evidence-backed answers and stores data on the user's
machine.

## 0.1.0a1 (unreleased)

Planned for **2026-06-15**. Dependency pins: `fastapi>=0.115.12` and
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

- The project is pre-release (0.1.0a1) and has not been published on PyPI.
- Installation with all extras pulls large machine learning packages and may be
  slow.
- The CLI requires optional packages such as `python-docx`, `pdfminer.six`, and
  `streamlit`.
- Quick start commands expect an LLM backend like LM Studio; without one,
  searches fail.
- Loading the VSS extension may require network access and can fail offline.
- `task` commands need Go Task; install it as noted in
  [installation](installation.md).
- CLI operations error without `python-docx` or `pdfminer.six`; see
  [installation](installation.md).
- VSS search and some tests require network access; see
  [DuckDB compatibility](duckdb_compatibility.md).
- `task coverage` fails with an ImportError (`InMemorySpanExporter`), so
  coverage is treated as 0%.
- Some dependencies still emit `pkg_resources` deprecation warnings; these
  are suppressed until upstream packages resolve the issue.

For installation and usage instructions see the README.

### Open issues

- add-orchestration-proofs-and-tests
- add-storage-proofs-and-simulations
- configure-redis-service-for-tests

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
