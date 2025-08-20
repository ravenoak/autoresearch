# Release Notes

Autoresearch is a local-first research assistant that coordinates multiple agents
to produce evidence-backed answers and stores data on the user's machine.

## Capabilities

- Coordinates dialectical, contrarian, and fact-checking agents to synthesize
  answers.
- Provides a command-line interface and HTTP API.
- Uses local databases for searches and knowledge graphs.
- Manages dependencies with uv and supports optional extras for features like
  rate limiting.

## Known Limitations

- The project is pre-release (0.1.0a1) and has not been published on PyPI.
- Installation with all extras pulls large machine learning packages and may be
  slow.
- The CLI requires optional packages such as `python-docx`, `pdfminer.six`, and
  `streamlit`.
- Quick start commands expect an LLM backend like LM Studio; without one,
  searches fail.
- Loading the VSS extension may require network access and can fail offline.

For installation and usage instructions see the [README](../README.md).
