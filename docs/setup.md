# Setup

- Run `uv venv` to create a local environment in `.venv`.
- Activate it with `source .venv/bin/activate`.
- Install development and test extras: `task install` or
  `uv sync --extra dev-minimal --extra test`.
- Add optional extras as needed, for example `task install EXTRAS="nlp ui"` or
  `uv sync --extra nlp --extra ui`.
