# Releasing

Follow these steps to publish a new version of Autoresearch.

- Update the version in `pyproject.toml` and
  `src/autoresearch/__init__.py`. Commit the change and tag the release.
- Build the distribution files.

  ```bash
  uv run python -m build
  ```
- Upload the build to TestPyPI for validation.

  ```bash
  uv run python scripts/publish_dev.py --dry-run
  uv run python scripts/publish_dev.py
  ```
- Release to PyPI once the TestPyPI upload is verified.

  ```bash
  uv run twine upload dist/*
  ```
