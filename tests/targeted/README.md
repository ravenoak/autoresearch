# Targeted tests

Temporary tests to reproduce specific issues live here. Execute them with:

```bash
uv run pytest tests/targeted -q
```

After the underlying problem is resolved, merge these tests into the
appropriate suite under `tests/unit`, `tests/integration`, or `tests/behavior`
so they run as part of `task coverage`.

