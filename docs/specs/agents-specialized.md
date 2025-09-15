# Specialized Agents

## Overview

Specialized agents extend the shared agent mixins to cover research planning,
evidence gathering, critique, summarization, moderation, domain expertise, and
user alignment. Each class tailors ``execute`` to its role while reusing the
base claim and result helpers.[m1][m2][m3][m4][m5][m6][m7]

## Algorithms

### ResearcherAgent

1. Resolve the adapter and model, then double the configured search fan-out to
   collect expanded evidence.[m1]
2. Convert external lookup results into structured sources tagged with the agent
   name.[m1]
3. Format the sources into a prompt for ``researcher.findings`` and generate a
   ``research_findings`` claim with attached sources and ``source_count``
   metadata.[m1]

### DomainSpecialistAgent

1. Determine the operating domain, inferring it from the query when none is
   preset.[m5]
2. Retrieve targeted context via ``Search.external_lookup`` and augment it with
   heuristic fallbacks when the search layer fails.[m5]
3. Filter claims whose content matches domain keywords, defaulting to recent
   entries when nothing matches.[m5]
4. Generate ``domain_analysis`` and ``domain_recommendations`` claims using
   prompts that optionally incorporate peer feedback.[m5]

### CriticAgent

1. Gather thesis, synthesis, and research finding claims to evaluate, or fall
   back to all claims when no targeted evidence exists.[m2]
2. Feed the formatted claims into ``critic.evaluation`` to produce a
   ``critique`` claim plus phase and evaluated-claim metadata.[m2]
3. When feedback is enabled, send critique summaries to downstream agents via
   coalition broadcasts or targeted feedback events.[m2]

### SummarizerAgent

1. Collect every claim from the state and serialize them into prompt context.[m3]
2. Invoke ``summarizer.concise`` to create a ``summary`` claim and count the
   summarized items for metadata.[m3]
3. Broadcast availability when agent messaging is enabled.[m3]

### PlannerAgent

1. Execute early in the dialogue, preferring cycle zero or an empty claim
   history.[m4]
2. Generate a ``research_plan`` claim using the ``planner.research_plan``
   template, optionally enriched with peer feedback.[m4]

### ModeratorAgent

1. Collect the most recent claims (up to ten) and detect conflict markers to
   summarize disagreements.[m6]
2. Produce ``moderation`` and ``guidance`` claims with associated metadata,
   including conflict flags and analyzed claim identifiers.[m6]

### UserAgent

1. Load configurable user preferences and collect recent claims plus current
   aggregated results.[m7]
2. Generate ``user_feedback`` and ``user_requirements`` claims that reinforce
   those preferences and share metadata for downstream alignment.[m7]
3. Emit direct feedback to contributing agents when enabled.[m7]

## Invariants

- Every specialized agent emits claims with stable ``type`` identifiers that
  match downstream expectations (for example ``research_findings``,
  ``domain_analysis``, and ``user_feedback``).[m1][m5][m7]
- Result payloads always mirror the claim content under matching keys so later
  orchestration steps can merge outputs without string parsing.[m1][m2][m3][m4]
- Metadata reports the active dialogue phase and supporting counts (such as
  analyzed claims, conflict detection, and source totals).[m1][m2][m3][m4][m6]
- Feedback hooks respect coalition routing and do not emit messages unless the
  configuration enables them.[m1][m2][m3][m7]

## Edge Cases

- Domain inference defaults to ``general`` when no keyword matches occur and
  falls back to preconfigured descriptions if search fails.[m5]
- The critic and summarizer gracefully evaluate the full claim list when
  targeted evidence is absent.[m2][m3]
- Planner execution short-circuits after the first cycle, preventing redundant
  plan regeneration.[m4]
- User feedback waits until at least one cycle has elapsed and skips execution
  when no claims exist to assess.[m7]

## Complexity

- Each agent performs a constant number of adapter generations, so runtime is
  dominated by gathering context (claim scans or search queries).
- Claim filtering and formatting are linear in the number of claims inspected
  (bounded by ten for the moderator and five for user feedback).

## Proof Sketch

Unit tests stub adapters and search results to assert claim types, metadata, and
feedback propagation for every specialized agent.[t1] Additional tests exercise
moderation conflict detection, domain gating, and planner eligibility thresholds
under varied states, demonstrating that guard clauses prevent mis-timed
execution.[t2]

## Simulation Expectations

Running ``uv run pytest tests/unit/test_specialized_agents.py`` yields mocked
LLM responses such as ``"Mock response from LLM"`` for each agent, confirming the
prompt wiring and metadata schema.[t1] Executing
``uv run pytest tests/unit/test_advanced_agents.py`` validates domain routing,
moderation conflict detection, and user preference handling with deterministic
fixtures.[t2]

## Traceability

- Modules
  - [ResearcherAgent][m1]
  - [CriticAgent][m2]
  - [SummarizerAgent][m3]
  - [PlannerAgent][m4]
  - [DomainSpecialistAgent][m5]
  - [ModeratorAgent][m6]
  - [UserAgent][m7]
- Tests
  - [test_specialized_agents.py][t1]
  - [test_advanced_agents.py][t2]

[m1]: ../../src/autoresearch/agents/specialized/researcher.py
[m2]: ../../src/autoresearch/agents/specialized/critic.py
[m3]: ../../src/autoresearch/agents/specialized/summarizer.py
[m4]: ../../src/autoresearch/agents/specialized/planner.py
[m5]: ../../src/autoresearch/agents/specialized/domain_specialist.py
[m6]: ../../src/autoresearch/agents/specialized/moderator.py
[m7]: ../../src/autoresearch/agents/specialized/user_agent.py
[t1]: ../../tests/unit/test_specialized_agents.py
[t2]: ../../tests/unit/test_advanced_agents.py
