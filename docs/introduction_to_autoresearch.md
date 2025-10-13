# Autoresearch introduction

Autoresearch treats investigation as a living conversation. Each session
begins with Socratic prompts—*What are we trying to prove? Which
assumptions might fail?*—and proceeds through dialectical loops that pit
supportive and contrarian evidence against one another until a
synthesis emerges. The platform is intentionally local-first: your
search trails, knowledge graphs, telemetry, and credentials stay on your
workstation while a modular Python stack exposes CLI, API, Streamlit,
and FastMCP entry points you can compose into larger systems.

## How to navigate this introduction

Different teams meet Autoresearch with different intentions. Use the
following guideposts to focus on the sections that match your role while
staying aware of the wider system:

- **Research practitioners** need to orchestrate trustworthy
  investigations, compare evidence, and communicate synthesis. Start
  with [Research practitioner journey](#research-practitioner-journey).
- **Contributor developers** extend agents, improve orchestration, and
  keep quality gates green. Focus on [Contributor developer
  journey](#contributor-developer-journey).
- **Operations and integration leads** care about deployment,
  observability, and compliance. Jump to [Operations and integration
  journey](#operations-and-integration-journey).
- **Product and program stewards** want to understand where v0.1.0a1
  stands and how the roadmap shapes v0.1.0. Review [Roadmap toward
  v0.1.0](#roadmap-toward-v010).

Everyone should skim [Shared foundations](#shared-foundations) first; it
captures the mindset and architectural primitives common to every story.

## Shared foundations

### Orienting questions

Revisit these prompts before, during, and after each run. They keep the
practice dialectical and reflective.

- *What is Autoresearch's thesis?* Coordinated agents gather and weight
  evidence so the synthesised answer is grounded in cited sources rather
  than opaque intuition.
- *Where do antitheses appear?* Contrarian agents, provenance panels, and
  anomaly detectors surface contradictions, missing citations, or risky
  leaps in reasoning so you can interrogate them directly.
- *How do we reach synthesis?* Fact checkers, planner conditioning, and
  re-verification loops reconcile tensions, track provenance, and refine
  the final narrative without erasing dissenting evidence.

### System overview

Autoresearch coordinates retrieval, planning, agent debate, knowledge
updates, and output formatting. Key pillars include:

- **Interfaces.** CLI commands, a Streamlit UI, a FastMCP agent server,
  and an HTTP API expose the same orchestration core. Each surface can be
  scripted or used interactively (see
  [Getting Started](getting_started.md)).
- **Orchestration kernel.** The kernel schedules agents, enforces
  reasoning budgets, records metrics, and streams state changes to
  observers (see [Orchestration](orchestration.md)).
- **Knowledge substrates.** DuckDB tabular storage, RDF and GraphML
  exports, optional Kuzu persistence, and embedding indexes keep local
  evidence synchronised across runs (see
  [Knowledge graph safeguards](knowledge_graph.md)).
- **Tracing and monitoring.** Structured logs, OpenTelemetry spans, and
  Prometheus metrics capture execution details for audits or dashboards
  (see [Monitoring](monitor.md)).

The architecture diagram in `docs/diagrams/system_architecture.puml`
visualises how these elements collaborate.

### Research pipeline at a glance

1. **Framing.** Prompt templates adapt to reasoning mode and depth,
   seeding debates with explicit hypotheses.
2. **Retrieval.** Web backends (Serper, Brave, DuckDuckGo), local file
   readers (PDF, DOCX, Markdown, Git diffs), and embedding indexes feed
   evidence into the shared corpus (see
   [Configuration Guide](configuration.md)).
3. **Planning.** A planner graph orders tasks, threads provenance cues
   into prompts, and tracks claims needing confirmation.
4. **Agent debate.** Synthesiser, Contrarian, Fact Checker, and optional
   domain agents iterate in loops to weigh evidence and note
   disagreements.
5. **Verification.** Re-verification workflows rerun fact checks with
   alternate retrieval or prompts, logging provenance deltas.
6. **Synthesis and output.** Depth-aware formatting produces TL;DRs,
   tables, knowledge graph exports, and raw traces tailored to your
   integration targets (see [Output formats](output_formats.md)).

### Agent ecosystem and reasoning modes

Agents inherit a shared base that enforces role-aware prompts,
capabilities, and safety hooks. Default roles drive the
thesis→antithesis→synthesis loop, while specialised roles extend the
conversation:

- **Synthesiser.** Drafts candidate answers grounded in cited passages.
- **Contrarian.** Surfaces counter-arguments, missing sources, and
  alternative framings to stress-test drafts.
- **Fact Checker.** Scores claim support, requests additional retrieval,
  and annotates provenance gaps.
- **Researcher.** Runs deeper web and document sweeps.
- **Planner.** Adjusts the task graph when new evidence arrives.
- **Summariser and Moderator.** Translate debate output into concise,
  audience-specific packages and enforce tone constraints.
- **Domain specialists.** Optional profiles tuned for legal, medical, or
  technical corpora.
- **User agent.** Echoes operator feedback back into the loop, allowing
  interactive corrections.

Reasoning modes (`dialectical`, `direct`, `chain-of-thought`) change how
agents collaborate. Dialectical is the default; direct minimises debate
for quick checks; chain-of-thought emphasises transparent intermediate
reasoning. Configure the active mode per run or profile (see
[Configuration Guide](configuration.md)). Coalitions and parallel agent
groups let you schedule multiple debates in lockstep—useful for comparing
competing hypotheses or accelerating large reviews (see
[Agents Overview](agents_overview.md)).

## Research practitioner journey

### Set up the environment

Autoresearch targets Python 3.12+. Install
[uv](https://github.com/astral-sh/uv) and
[Task](https://taskfile.dev) for dependency and workflow management, then
run `./scripts/setup.sh` to create an editable install, sync the
`dev-minimal` and `test` extras, and record helper scripts. Add optional
extras for the surfaces you rely on:

- `ui` for the Streamlit interface
- `vss` for DuckDB vector search
- `parsers` for PDF and DOCX ingestion
- `git` for repository diff search

Use profiles inside `autoresearch.toml` to switch between offline and
online stacks without editing the base configuration.

### Run your first investigations

1. **Pose a question.** For example,
   `autoresearch search "Explain prompt reflection" --depth concise`
   yields the debate trace, provenance, and TL;DR in one run.
2. **Probe the debate.** Choose `--mode dialectical` for multi-agent
   dialogue, `--mode direct` for quick scans, or `--mode chain-of-thought`
   to emphasise transparent reasoning.
3. **Adjust scope.** Add
   `--agents Synthesiser,Contrarian,FactChecker,Researcher` to widen
   coverage, or `--loops 3 --token-budget 2000` to lengthen debates with
   explicit guardrails.
4. **Inspect artefacts.** Append `--output json` for downstream parsing,
   `--graphml graph.graphml` for knowledge graph exports, or `--visualise`
   to hand off results to the Streamlit UI (see
   [Quickstart guides](quickstart_guides.md)).
5. **Iterate.** Re-run with `--reverify` flags or the UI re-verification
   panel when provenance marks a claim as unsupported. Contrast runs to
   see how new evidence shifts the synthesis.

### Blend evidence sources

Keep provenance central by weaving internal and external data together:

- Enable hybrid retrieval in `autoresearch.toml` by combining web,
  document, and Git backends (see [Search backends](search_backends.md)).
- Use the knowledge graph exports (GraphML, JSON) to inspect claim
  networks visually and share findings with stakeholders.
- Apply dialectical reflection: compare how internal documents support or
  challenge public sources and record adjustments to relevance weights.

### Communicate results

Leverage depth presets to match the audience:

- `tldr` for executive snapshots with citations.
- `concise` for primary findings and confidence metrics.
- `standard` for claim audits, resource usage, and provenance tags.
- `trace` when peers need to audit reasoning paths and tool responses.

Export Markdown or JSON to attach to notebooks, issue trackers, or slide
ware. Capture open questions and contradictions so future runs revisit
unresolved threads.

## Contributor developer journey

### Inspect the architecture

Review the orchestration core (see
[Architecture](architecture/overview.md)) and study the sequence
diagrams in `docs/diagrams/` to understand how
planner, agents, and storage interact. Pay special attention to:

- **Configuration loading.** Settings merge from `autoresearch.toml`,
  environment variables, and CLI flags. Profiles encode reproducible
  research contexts (see [Configuration](configuration.md)).
- **Agent contracts.** Base classes enforce role capabilities, tool
  permissions, and safety affordances (see
  [Agents overview](agents_overview.md)).
- **Knowledge layers.** DuckDB, RDF exports, and embedding indexes share
  schema definitions and migration scripts (see
  [Knowledge graph](knowledge_graph.md)).

### Establish a development environment

1. Clone the repository and create a virtual environment with `uv venv`.
2. Install extras that match your focus, e.g.
   `uv pip install -e '.[dev,full,parsers,git,llm]'`.
3. Run `task install` to register pre-commit hooks and bootstrap shared
   tooling.
4. Validate with `task check`; follow with `task verify` before pushing
   changes or opening a pull request.

Document assumptions and surprises in `issues/` or design notes so peers
can replicate your environment.

### Extend or create agents

- Start with the scaffolding in `src/autoresearch/agents/` and mirror the
  dialectical contract: the new agent should articulate its thesis,
  invite counterpoints, and cite supporting passages.
- Add tests under `tests/` to capture behavioural expectations. Use
  behaviour-driven scenarios for CLI interactions and unit tests for
  reasoning utilities (see [Testing guidelines](testing_guidelines.md)).
- Reflect after each iteration: *Which failure modes remain? How does the
  new agent shift debate outcomes?* Use these insights to tune prompts or
  retrieval weights.

### Contribute safely

- Follow [CONTRIBUTING](../CONTRIBUTING.md) for branching, coding style,
  and review expectations.
- Record reasoning in commit messages and PR summaries so others can
  trace design decisions.
- Tag documentation updates when surface behaviour changes; onboarding is
  smoother when user stories remain current.

## Operations and integration journey

### Deploy surfaces

- **Streamlit UI.** Install the `ui` extra and run `autoresearch ui`.
  Configure authentication if the instance serves multiple analysts.
- **HTTP API.** Launch with `autoresearch api --host 0.0.0.0 --port 8080`
  and secure it using `api.api_key` or per-user entries in
  `api.api_keys`. Review [API authentication](api_authentication.md).
- **FastMCP server.** Expose Autoresearch to other agent swarms with
  `autoresearch serve`; scope permissions via tool manifests.

### Monitor and observe

Enable Prometheus metrics by setting `api.monitoring_enabled = true` in
`autoresearch.toml` or exporting the equivalent environment variable.
Collect `/metrics` to track system health, Redis or Ray connectivity,
loop counts, token usage, and latency buckets. Use CLI watch modes to
stream CPU, memory, and token counters so you know when to scale
resources or pause runs. Logs annotate each agent turn, planner update,
and knowledge graph mutation with timestamps to simplify audits (see
[Monitoring](monitor.md)).

### Safeguard data and compliance

- Maintain local-first defaults: API keys live in `.env`, retrieved
  sources stay on disk unless you configure external sinks, and optional
  redaction routines fence control characters (see
  [README](../README.md#accessibility)).
- Catalogue knowledge graph exports and retention policies so audits can
  reconstruct claim provenance.
- Document incident response drills: *What happens if a backend fails?
  How do we replay or resume a run?* Capture answers in runbooks.

### Automate and integrate

- Embed the HTTP API in notebooks, dashboards, or CI pipelines. Streaming
  responses let you monitor partial results.
- Use FastMCP to chain Autoresearch with other automation frameworks.
- Schedule recurring investigations with Task or cron, writing outputs to
  knowledge bases or ticketing systems for follow-up.

## Roadmap toward v0.1.0

Version 0.1.0a1 already delivers depth selectors, planner conditioning,
provenance panels, re-verification workflows, and adaptive Socratic
prompting. These capabilities make the alpha a laboratory for testing
transparent research flows today.

The path to v0.1.0 centres on production hardening (see
[Release plan](release_plan.md) and [Roadmap](../ROADMAP.md)):

- **Reliability.** Expand readiness sweeps that bundle linting, typing,
  behavioural verification, packaging, and TestPyPI dry runs before
  cutting tags.
- **Agent upgrades.** Deepen planner and coordinator intelligence, add
  coalition presets, and refine domain specialist libraries.
- **Knowledge graph evolution.** Ship graph-augmented retrieval for
  contradiction detection, export automation, and richer provenance
  narratives.
- **Distributed execution.** Harden Ray- and Redis-based scaling paths so
  teams can run large reviews in parallel.
- **API stabilisation.** Finalise HTTP contracts, FastMCP schemas, and
  monitoring stories for multi-tenant environments.

Upcoming previews (targeting September 15 2026 for 0.1.0a1 and
October 1 2026 for the 0.1.0 public preview) will stage these
improvements, aiming for a smooth upgrade path to 1.0.0 once distributed
and monitoring milestones land.

## Continuing the practice

Close every investigation with a retrospective: *What evidence persuaded
us? Which contradictions remain unresolved? How should agent rosters or
retrieval weights adapt next time?* Capture answers in configuration,
`issues/` tickets, or shared documentation so collective knowledge grows
with each run. Autoresearch thrives when every user acts as both
researcher and reflective practitioner.
