# Dialectical Agents

## Overview

The dialectical agent family orchestrates thesis–antithesis–synthesis dialogue
between the synthesizer, contrarian, and fact checker roles. The cycle follows
the convergence guarantees derived in [Dialectical Agent Coordination][a1] and
updates shared claims stored on the query state.[m1][m2][m3]

## Algorithms

### SynthesizerAgent

1. Resolve the adapter and active model from configuration.[m1]
2. If the reasoning mode is direct, prompt ``synthesizer.direct`` and emit a
   synthesis claim with both ``final_answer`` and ``synthesis`` results.[m1]
3. On the first dialectical cycle, prompt ``synthesizer.thesis`` to seed the
   thesis claim and mark the phase as ``DialoguePhase.THESIS``.[m1]
4. On later cycles, concatenate prior claim content, apply the
   ``synthesizer.synthesis`` template, and record the combined answer under both
   ``final_answer`` and ``synthesis`` keys.[m1]

### ContrarianAgent

1. Acquire the adapter and model, then search the state for the most recent
   thesis claim.[m2]
2. Fall back to the user query when no thesis exists, keeping the dialogue
   grounded.[m2]
3. Populate the ``contrarian.antithesis`` prompt with that text, generate the
   antithesis, and wrap it as a claim tagged ``antithesis``.[m2]
4. Return a result whose metadata identifies the antithesis phase and exposes
   the generated rebuttal.[m2]

### FactChecker

1. Resolve the adapter and active model.[m3]
2. Derive the maximum search fan-out from configuration (defaulting to five)
   and call ``Search.external_lookup`` to gather supporting sources.[m3]
3. Annotate each source with the claims examined and the agent name so that
   downstream synthesizers can audit provenance.[m3]
4. Feed the assembled claims into ``fact_checker.verification`` and emit a
   verification claim alongside the structured sources and source counts.[m3]

### Execution gating

- ``SynthesizerAgent`` always executes when enabled.
- ``ContrarianAgent`` and ``FactChecker`` require dialectical reasoning mode and
  at least one existing claim (thesis for the contrarian, any claim for the fact
  checker) before delegating to ``Agent.can_execute``.[m2][m3]

## Invariants

- Each agent returns at least one claim bearing the expected ``type`` value:
  ``thesis`` or ``synthesis`` for the synthesizer, ``antithesis`` for the
  contrarian, and ``verification`` for the fact checker.[m1][m2][m3]
- ``metadata["phase"]`` reflects the dialogue stage asserted by the agent,
  aligning with ``DialoguePhase`` enumerations.[m1][m2][m3]
- Fact-checker sources always include ``checked_claims`` and ``agent`` fields so
  later agents can attribute evidence.[m3]
- Synthesizer synthesis results duplicate the final answer string to guarantee
  downstream consumers can access the conclusion under consistent keys.[m1]

## Edge Cases

- Direct reasoning mode bypasses dialectical phases and returns a final answer
  in a single execution.[m1]
- The contrarian falls back to the query text if no thesis is present, but its
  ``can_execute`` guard prevents execution until a thesis exists.[m2]
- The fact checker short-circuits when the configuration disables dialectical
  mode or no claims are available.[m3]
- Empty search responses degrade gracefully to zero sources while keeping the
  verification claim intact.[m3]

## Complexity

- Synthesizer work scales linearly with the number of existing claims because it
  concatenates their text before a single generation call.[m1]
- Contrarian and fact checker work is ``O(c + r)`` where ``c`` counts scanned
  claims and ``r`` counts retrieved sources; they each perform one generation.

## Proof Sketch

Execution guards ensure each role runs in a context that satisfies its
preconditions. Prompted generations rely on shared mixins, so results always
follow the base agent schema. Property-based tests confirm that the dialectical
update never increases error and that higher fact-checker weights improve the
mean outcome.[t1][t2] Unit tests inject adapters to verify each agent emits the
expected claim types, metadata, and sources.[t3][t4]

## Simulation Expectations

Running ``uv run scripts/dialectical_coordination_demo.py --loops 3 --trials 10``
produces convergence statistics such as ``mean=0.976 stdev=0.333`` that match
the linear update analysis.[a1][s1] The analysis harness samples random
initializations and writes ``dialectical_metrics.json`` with comparable means
and deviations, supplying reproducible evidence for the convergence claim.[s2]

## Traceability

- Modules
  - [SynthesizerAgent][m1]
  - [ContrarianAgent][m2]
  - [FactChecker][m3]
- Algorithms
  - [Dialectical Agent Coordination][a1]
- Scripts
  - [dialectical_coordination_demo.py][s1]
  - [dialectical_cycle_analysis.py][s2]
- Tests
  - [test_synthesizer_agent_modes.py][t3]
  - [test_agents_llm.py][t4]
  - [test_property_dialectical_coordination.py][t1]
  - [test_dialectical_cycle_property.py][t2]

[a1]: ../algorithms/dialectical_coordination.md
[m1]: ../../src/autoresearch/agents/dialectical/synthesizer.py
[m2]: ../../src/autoresearch/agents/dialectical/contrarian.py
[m3]: ../../src/autoresearch/agents/dialectical/fact_checker.py
[s1]: ../../scripts/dialectical_coordination_demo.py
[s2]: ../../tests/analysis/dialectical_cycle_analysis.py
[t1]: ../../tests/unit/legacy/test_property_dialectical_coordination.py
[t2]: ../../tests/analysis/test_dialectical_cycle_property.py
[t3]: ../../tests/unit/legacy/test_synthesizer_agent_modes.py
[t4]: ../../tests/unit/legacy/test_agents_llm.py
