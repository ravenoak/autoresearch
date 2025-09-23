# Task coverage – 2025-09-23

- **Command:**
  ```bash
  task coverage \
    EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"
  ```
- **Targeted extras:** analysis, distributed, git, gpu, llm, nlp, parsers, ui,
  vss.
- **Unit tests:** 908 passed, 15 skipped, 25 deselected; 9 xfailed, 5 xpassed.
- **Integration tests:** 331 passed, 11 skipped, 107 deselected.
- **Behavior tests:** 29 passed, 208 skipped, 49 deselected.
- **Coverage:** 100% line rate (57/57) with the ≥90% gate satisfied.

## Environment and caching notes

- Hydrated `wheels/gpu` with bertopic, pynndescent, scipy, and lmstudio wheels
  so `task verify:preflight` recognized the GPU cache before syncing extras.
- Reused `AR_EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`
  during `./scripts/setup.sh` to install the optional suites prior to running
  coverage.

## Reproduction steps

1. `eval "$(./scripts/setup.sh --print-path)"` to expose `.venv/bin` on
   `PATH`.
2. `AR_EXTRAS="nlp ui vss git distributed analysis llm parsers gpu" \
   ./scripts/setup.sh`.
3. `task verify:preflight`.
4. `task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`.
5. Copy the XML: `cp coverage.xml baseline/coverage.xml`.
