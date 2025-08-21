# Ontology Reasoning

`run_ontology_reasoner` expands an RDF graph with inferred triples. The function
selects a reasoning engine via `storage.ontology_reasoner` and applies it to the
provided store. Plugins registered through `register_reasoner` or referenced as
`module:function` may implement OWL RL, RDFS, or custom semantics.

## Semantics

- Existing triples remain in the store; reasoners may only add new facts.
- If `storage.ontology_reasoner_max_triples` is set and the graph exceeds the
  limit, reasoning is skipped.
- The call logs the number of input triples and the engine used.

## Complexity

Let *n* denote the number of triples. OWL RL reasoning runs in `O(n^3)` time in
the worst case[^owlrl], while RDFS closure can be computed in `O(n^2)` under
typical assumptions[^rdfs]. Custom plugins may differ but must respect the
timeout described below.

## Timeout behavior

The reasoner executes in a worker thread. If it fails to finish within
`storage.ontology_reasoner_timeout` seconds, `run_ontology_reasoner` raises a
`StorageError` and leaves the graph unchanged. This prevents runaway plugins
from blocking the orchestration pipeline.

## Empirical performance

`tests/analysis/ontology_reasoning_bench.py` benchmarks reasoning time as the
triple count increases. The results show near-linear growth for small graphs:

| triples | seconds |
| ------- | ------- |
| 10      | 0.06    |
| 50      | 0.10    |
| 100     | 0.16    |
| 200     | 0.27    |

Reasoning time vs triple count:

```text
10   | ######
50   | ##########
100  | #################
200  | ###############################
```

## References

- rdflib `owlrl` implementation[^owlrl]
- RDF Schema reasoning complexity[^rdfs]

[^owlrl]: https://rdflib.github.io/OWL-RL/
[^rdfs]: https://www.w3.org/TR/rdf11-mt/
