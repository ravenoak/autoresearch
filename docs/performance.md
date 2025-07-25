# Performance Monitoring

Autoresearch includes tools to inspect system performance and resource usage.

## CPU and Memory Tracking

Use the following command to record CPU and memory statistics:

```bash
autoresearch monitor resources --duration 10
```

This collects metrics for ten seconds and displays them in a table. The duration can be adjusted as needed.

You can also run `autoresearch monitor` to view a live stream of basic metrics.

## GPU Monitoring

If your system has NVIDIA GPUs, Autoresearch will attempt to collect GPU
utilization and memory usage. Metrics are gathered using `pynvml` when
available or by invoking `nvidia-smi`. When neither is present the GPU values
remain zero.

Running `autoresearch monitor resources` will therefore include ``GPU %`` and
``GPU MB`` columns when supported.

## Token Usage Heuristics

The orchestration metrics module provides helpers to automatically compress
prompts and adjust token budgets. After each cycle the orchestrator uses
`suggest_token_budget` to expand or shrink the configured budget. The heuristic
tracks both the overall token usage and per-agent historical averages so the
budget gradually converges toward typical usage without starving any agent.
`compress_prompt_if_needed` likewise tracks prompt lengths and lowers its
compression threshold when the average length exceeds the available budget. If
a prompt still exceeds the budget after compression, a summarization step can be
supplied to ``compress_prompt`` to further reduce the text. This adaptive
behaviour helps prevent runaway token consumption.

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

