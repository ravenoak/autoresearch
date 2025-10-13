# Getting Started

This primer walks through the essential moves required to bring
Autoresearch online. It keeps the dialectical and Socratic habits front
and centre so you continually question assumptions, inspect evidence,
and adapt the workflow to your context. Each persona receives a focused
journey; skim the others to stay aware of adjacent responsibilities.

## Orienting prompts

- *What problem do you need Autoresearch to solve first?*
- *Which surface—CLI, UI, API, or FastMCP—best fits that workflow?*
- *How will you validate that results are trustworthy and reproducible?*
- *Which guardrails or observability signals prove the system behaves as
  intended?*

Keep these questions in mind as you move through the checklists. They
anchor a dialectical practice: state assumptions, surface counterpoints,
and integrate lessons.

## Shared prerequisites

- Python 3.12 or newer.
- [uv](https://github.com/astral-sh/uv) for environment and dependency
  management.
- Git, `make`, and build tools required for native extensions such as
  `hdbscan`.
- Optional: Docker if you prefer containerised execution.

On Debian or Ubuntu install core build tooling with:

```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

If you anticipate GPU workloads, review `docs/installation.md` for CUDA
extras before continuing.

## Environment setup snapshot

- **Researchers.** Prioritise CLI and UI surfaces plus provenance exports;
  validate with a sample search and debate trace review.
- **Contributors.** Install full extras and agent scaffolding; validate
  with `task check` and targeted tests.
- **Operators.** Enable API, monitoring, and FastMCP surfaces; validate
  with metrics endpoints and authentication smoke tests.

Use the persona sections below to expand these summaries into actionable
steps.

## Research practitioner quickstart

### Install and bootstrap

1. **Clone the repository** and enter the project directory.
2. **Create the virtual environment**:

   ```bash
   uv venv
   ```

3. **Install recommended extras** for day-one research:

   ```bash
   uv pip install -e '.[full,parsers,git,llm,ui]'
   ```

   - Set `HDBSCAN_NO_OPENMP=1` if OpenMP support causes build issues.
   - Prefer `uv` over `pip` for repeatable resolution, though `pip
     install -e .` works when tooling is constrained.

4. **Run the bootstrap task** to wire auxiliary tooling and Git hooks:

   ```bash
   task install
   ```

5. **Capture secrets** (API keys, Serper tokens) in `.env.local` or your
   secrets manager rather than committing them.

### Configure your first profile

Autoresearch reads configuration from `autoresearch.toml`. Start with the
sample generated during `task install` or copy
`examples/autoresearch.toml` into the project root. Review key sections:

- `[llm]` – model provider, API base URL, authentication.
- `[search]` – web, local file, and Git backends; ensure data access fits
  compliance boundaries.
- `[orchestrator]` – agent roster, retry policies, guardrails.
- `[monitor]` – telemetry endpoints for real-time observation.

Ask: *Which defaults reinforce or undermine research quality?* Adjust
values incrementally and keep a copy of the baseline for future
comparisons.

### Launch your first search

Use the CLI to validate end-to-end orchestration:

```bash
autoresearch search "What are the latest breakthroughs in battery density?"
```

Control verbosity with `--depth` presets:

- `tldr` – final synthesis plus key citations.
- `concise` – adds primary findings and confidence metrics.
- `standard` – includes claim audits and resource usage snapshots.
- `trace` – surfaces the reasoning graph and raw tool responses.

Combine depth with structured outputs when you need machine-readable
artefacts:

```bash
autoresearch search "Outline quantum error correction" \
  --depth trace --output json
```

After each run, inspect the timeline, agent notes, and source
attributions. Ask whether the synthesis matches expectations, then rerun
with alternate prompts or agents to explore counterfactuals.

### Explore other surfaces

- **Streamlit UI:** `autoresearch ui`. Toggle contrarian analysis, watch
  token usage, and compare the UI summary against CLI traces for gaps.
- **Monitor dashboard:** `autoresearch monitor`. When a chart looks off,
  ask *which subsystem needs attention* before proceeding.
- **FastMCP interface:** `autoresearch serve`. Use the exported tool in
  automation frameworks and compare its answers with direct CLI output.
- **HTTP API:** `autoresearch api --host 0.0.0.0 --port 8080`. Test with
  `curl` and plan how you will persist artefacts or attach them to
  downstream workflows.

### Blend your own data

Enable hybrid retrieval:

```toml
[search]
backends = ["serper", "local_file", "local_git"]

[search.local_file]
path = "/path/to/docs"
file_types = ["md", "pdf", "docx", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 50
```

Compare runs with and without internal artefacts. Note how internal
sources support or challenge public evidence and adjust relevance
weights accordingly.

## Contributor developer onboarding

### Extend the installation

1. Create a virtual environment with `uv venv` if not already done.
2. Install development extras:

   ```bash
   uv pip install -e '.[dev,full,parsers,git,llm,analysis]'
   ```

3. Run `task install` to configure hooks and shared tooling.
4. Execute `task check` to run formatting, linting, and targeted tests.
5. Execute `task verify` before opening a pull request to include the
   full suite with coverage.

Document assumptions in `issues/` when you encounter blockers so the
team can respond.

### Map the codebase

- Start with [Architecture](architecture/overview.md) and the diagrams in
  `docs/diagrams/` to understand planner, agents, and knowledge storage.
- Explore `src/autoresearch/agents/` for agent scaffolding and contract
  definitions (see [Agents overview](agents_overview.md)).
- Review `tests/` to see behaviour-driven CLI scenarios and unit tests
  that protect reasoning utilities (see
  [Testing guidelines](testing_guidelines.md)).
- Study [Configuration](configuration.md) to grasp how profiles and
  environment overrides merge.

Ask during review: *What failure modes did we miss? Which dependencies
need pinning?* Capture answers in documentation or follow-up issues.

### Develop changes safely

- Mirror the dialectical contract in new agents: articulate a thesis,
  invite counterpoints, cite evidence, and log provenance.
- Add tests alongside features. Use Socratic prompts in docstrings to
  explain design intent and expected counterarguments.
- Update relevant docs whenever CLI flags, API schemas, or UI behaviour
  changes; contributors rely on accurate guidance to avoid regressions.

## Operations and integration preparation

### Harden deployment surfaces

- **Streamlit UI:** ensure the `ui` extra is installed, then run
  `autoresearch ui`. Add authentication if shared beyond a single
  workstation.
- **HTTP API:** launch with `autoresearch api --host 0.0.0.0 --port 8080`
  and secure using `api.api_key` or per-user entries in `api.api_keys`
  (see [API authentication](api_authentication.md)).
- **FastMCP server:** expose Autoresearch to other agents with
  `autoresearch serve`; scope tool permissions and track usage.

### Establish observability

- Set `api.monitoring_enabled = true` in `autoresearch.toml` or export the
  corresponding environment variable.
- Scrape `/metrics` with Prometheus to track system health, Redis or Ray
  connectivity, loop counts, token usage, and latency buckets.
- Use CLI watch modes to stream CPU, memory, and token counters during
  long investigations.
- Centralise logs; each agent turn, planner update, and knowledge graph
  mutation carries timestamps to simplify audits (see [Monitoring](monitor.md)).

### Safeguard data and compliance

- Keep the default local-first posture: secrets remain in `.env`, cached
  sources stay on disk, and nothing leaves the workstation unless you
  configure external sinks (see [README](../README.md#accessibility)).
- Catalogue graph exports and retention policies so auditors can
  reconstruct claim provenance.
- Run incident response drills: *What happens if a backend fails? How do
  we replay or resume a run?* Update runbooks with findings.

### Automate integrations

- Embed the HTTP API in notebooks, dashboards, or CI pipelines. Streaming
  responses make partial progress visible.
- Combine FastMCP with other agent frameworks to schedule recurring
  investigations.
- Use Task or cron jobs to trigger batch analyses and publish outputs to
  knowledge bases or ticketing systems.

## Next steps

- Study `docs/introduction_to_autoresearch.md` for a systems view of
  philosophy, architecture, and persona journeys.
- Review `docs/advanced_usage.md` to layer on batching, scheduling, and
  custom agent development once the basics feel solid.
- Capture lessons learned in issues or runbooks so your team can iterate
  with the same clarity you applied while onboarding.

By continually questioning the setup and experimenting across surfaces
you will develop a resilient research practice that scales smoothly from
v0.1.0a1 into the forthcoming v0.1.0 release.
