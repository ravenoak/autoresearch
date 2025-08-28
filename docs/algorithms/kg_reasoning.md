# KG Reasoning

`run_ontology_reasoner` expands a knowledge graph using pluggable engines.
The function selects an engine from configuration or the `engine` argument and
applies it to the graph. Built in plugins include `owlrl` and `rdfs`, while
external handlers may be registered via `register_reasoner` or referenced as
`module:function` paths.

## Correctness

Let *G* be the input graph and *R* the rules supplied by the chosen engine. The
procedure is correct when every triple added to *G* is derivable from repeated
application of rules in *R* and no further rule can be applied. Because the
implementation never deletes triples and stops only after reaching a fixpoint,
the resulting graph represents the closure of *G* under *R*.

## Timeout safety

Reasoning runs in a worker thread when `storage.ontology_reasoner_timeout` is
set. If the thread fails to finish within the limit the function raises a
`StorageError`, leaving the graph unchanged. This prevents runaway plugins from
blocking orchestration.

## Simulation

The script [`scripts/visualize_rdf.py`](../../scripts/visualize_rdf.py) builds a
small graph and confirms that `run_ontology_reasoner` augments it with inferred
triples. Empirically the closure for ten triples completes in under 0.1 seconds
on a commodity CPU.

## References

- [`kg_reasoning.py`](../../src/autoresearch/kg_reasoning.py)
- OWL RL reasoning tutorial[^owl]

[^owl]: https://rdflib.github.io/OWL-RL/
