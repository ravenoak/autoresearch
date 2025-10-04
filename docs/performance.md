# Performance Monitoring

Autoresearch includes tools to inspect system performance and resource usage.

## CPU and Memory Tracking

Use the following command to record CPU and memory statistics:

```bash
autoresearch monitor resources --duration 10
```

This collects metrics for ten seconds and displays them in a table. The
duration can be adjusted as needed.

You can also run `autoresearch monitor` to view a live stream of basic metrics.

## GPU Monitoring

If your system has NVIDIA GPUs, Autoresearch will attempt to collect GPU
utilization and memory usage. Metrics are gathered using `pynvml` when
available or by invoking `nvidia-smi`. When neither is present the GPU values
remain zero.

Running `autoresearch monitor resources` will therefore include ``GPU %`` and
``GPU MB`` columns when supported.

## Truthfulness evaluation harness stubs

Draft configuration files in `scripts/evaluate/` will declare shared knobs for
TruthfulQA, FEVER, and HotpotQA benchmarks so performance runs align with the
testing playbook. The stubs pin dataset slices, batch sizes, and output layer
defaults, ensuring layered UX controls (baseline, audit, narrative) stay
consistent between CLI invocations and automated schedules. When the harness
automation lands, point monitoring comparisons at the generated artifact
directories recorded in each stub.

## Budget-Aware Model Routing

The orchestration layer records per-agent token and latency samples so the
model router can steer high-usage roles toward cost-efficient backends without
violating service-level objectives. The router consults:

- the moving-average token spend for each agent,
- the 95th-percentile latency derived from recent executions, and
- model profiles that describe per-1K token pricing and latency targets.

When an agent consumes more than 80% of its allocated share of the global token
budget, the router recommends a cheaper profile that still satisfies the
agent's latency SLO. Every evaluation emits a `Budget router evaluated` log
record with the rolling token averages, percentile latency, projected cost
delta, and the calculated budget window for the agent. The orchestrator now
logs the recommendation via `Evaluated budget-aware model routing` without
switching models yet; the `applied: false` flag signals that routing remains in
observation mode until the dashboards confirm the new targets.

## Telemetry Dashboards

The metrics payload now includes latency percentiles per agent role alongside
aggregate cost estimates derived from the routing profiles. Dashboards should
plot the following series to track performance regressions:

- `agent_latency_p95_ms`: 95th-percentile latency per agent surfaced through the
  orchestration summary payload.
- `agent_avg_tokens`: moving-average token consumption stored alongside the
  latency summary for dashboards and structured logs.
- `model_routing_decisions`: structured records of each routing evaluation,
  including the baseline and selected models.
- `model_routing_cost_savings`: cumulative difference between baseline and
  routed cost estimates derived from the logged decisions.
- `model_routing_overrides`: the gate and planner escalation requests that
  forced more capable models into the debate.
- `model_routing_strategy`: the active routing profile (for example,
  `balanced`, `cost_saver`, or `premium`) recorded with each run.
- `model_routing_agent_constraints`: per-agent budget shares and latency
  ceilings captured during routing evaluation so operators can audit SLO
  coverage.
- `model_routing_recommendations`: the models suggested for each agent while
  routing operates in observation-only mode.

These signals make it easy to confirm that cost savings materialise without
raising the latency envelope for latency-sensitive agents.

The `OrchestrationMetrics.persist_model_routing_metrics` helper appends these
series as JSON Lines to ``AUTORESEARCH_ROUTING_METRICS`` (defaulting to
``tests/integration/baselines/model_routing.json``). Dashboards can tail this
file to display the chosen strategy, overrides, latency percentiles, and cost
deltas without re-running orchestrations.

## Role-Aware Routing Policies

`config.model_routing.role_policies` maps each agent to preferred and allowed
models, a token share or explicit budget, and a `confidence_threshold` that
triggers escalations. When the scout gate or planner reports confidence below
this threshold, the orchestrator registers a routing override that prioritises
the policy's `escalation_model` and records the override in telemetry. This
ensures expensive models are only invoked when evidence coverage looks weak or
the planner produces low-confidence plans.

## Routing Strategy Comparisons

`EvaluationHarness.compare_routing_strategies` summarises accuracy, latency,
token usage, and cost deltas between a baseline configuration and alternative
model routing strategies. The helper accepts two sets of
`EvaluationSummary` results—including planner depth, routing deltas, routing
strategy labels, and CSV artifact paths—and returns the difference in key
metrics so teams can quantify the trade-offs between aggressive cost-saving
strategies and premium accuracy-focused profiles before rolling them out
broadly.

## Retrieval Cache and Parallel Controls

Search now respects two new knobs in `config.search`:

- `shared_cache` and `cache_namespace` decide whether search instances share a
  TinyDB cache or work from a private file. Namespacing allows concurrent runs
  to avoid collisions while still reusing expensive retrievals when desired.
- `parallel_enabled` and `parallel_prefetch` control backend fan-out. Disabling
  parallelism forces sequential execution, while prefetching allows a subset of
  backends to warm their caches before the remaining requests run in a thread
  pool.

Combine these toggles to simulate customer environments, cap concurrency, or
quarantine experiments without reconfiguring global state.

## Distributed Coordination Benchmarks

ResourceMonitor captured CPU and memory usage while coordinating a simple
CPU-bound task across multiple processes. Average CPU rose from roughly 0%
with one node to about 30% with two nodes and 40% with four nodes. Memory
remained near 45–49 MB. These measurements were generated by
`tests/analysis/distributed_coordination_analysis.py`.

## Token Usage Heuristics

The orchestration metrics module provides helpers to automatically compress
prompts and adjust token budgets. After each cycle the orchestrator uses
`suggest_token_budget` to expand or shrink the configured budget. The heuristic
tracks both the overall token usage and per-agent historical averages so the
budget gradually converges toward typical usage without starving any agent. It
applies expansion when usage spikes and contracts when cycles run lean, never
allowing the budget to drop below one token. `compress_prompt_if_needed`
likewise tracks prompt lengths and lowers its compression threshold when the
average length exceeds the available budget. This causes later prompts to be
compressed earlier if recent prompts were long. If a prompt still exceeds the
budget after compression, a summarization step can be supplied to
``compress_prompt`` to further reduce the text. This adaptive behaviour helps
prevent runaway token consumption.

See the Token Budget Helpers specification for the precise expected
behaviour of these algorithms and the accompanying unit tests.

When a token budget is set, the orchestrator applies this compression step
inside ``_capture_token_usage`` before passing prompts to the LLM adapter.
Any remaining excess is trimmed by the adapter so prompts never exceed the
configured budget.

## Connection Pooling

HTTP requests to LLM and search backends reuse shared `requests.Session`
instances. The pool size for LLMs is controlled by `llm_pool_size` while search
backends use `http_pool_size`. When a session is created an `atexit` hook is
registered to close it automatically on program exit. Reusing sessions reduces
connection overhead during heavy query loads.

### Polars Metrics Analysis

When the `analysis` extra is installed you can transform collected metrics into
a Polars DataFrame:

```python
from autoresearch.data_analysis import metrics_dataframe
df = metrics_dataframe(metrics, polars_enabled=True)
print(df)
```

This provides convenient aggregation and export capabilities for further
analysis.

