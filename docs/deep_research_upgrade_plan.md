# Deep Research Upgrade Plan

## Overview

This plan translates the September 26, 2025 dialectical review of the
Autoresearch enhancement proposal into actionable work. The approach blends
systems engineering, knowledge management, and human-computer interaction to
keep truthfulness, verifiability, and cost discipline in balance.

## Dialectical Synthesis

- **Thesis:** Adaptive orchestration, per-claim audits, structured planning,
  graph-augmented retrieval, and continuous evaluation will raise factuality
  and research depth.
- **Antithesis:** Each capability risks duplicating current functionality,
  inflating latency, or breaking established workflows and telemetry.
- **Synthesis:** Deliver the upgrades in staged, testable increments with
  guardrails that preserve current guarantees before expanding scope.

## Phase Breakdown

1. **Phase 1 – Adaptive Gate and Claim Audits**
   - Implement the scout pass and gating heuristics with clear metrics.
   - Surface configuration toggles (`gate_policy_enabled`, overlap, conflict,
     and complexity thresholds, plus overrides) so operators can tailor the
     decision boundary.
   - Extend the evidence pipeline to record per-claim support status.
   - Update response formats so clients can render audit tables.
2. **Phase 2 – Planner and Coordinator Evolution**
   - Promote planner outputs into a schedulable task graph.
   - Capture ReAct traces for transparency and replay.
   - Document interfaces for specialized agents and tool calls.
3. **Phase 3 – Graph-Augmented Retrieval**
   - Build session-scoped knowledge graphs using existing storage hooks.
   - Surface contradiction checks that feed back into the gate policy.
   - Export lightweight GraphML or JSON artifacts per session.
4. **Phase 4 – Evaluation Harness and Layered UX**
   - Automate TruthfulQA, FEVER, and HotpotQA smoke runs with KPIs.
   - Add layered summaries, Socratic prompts, and per-claim audits to the UI.
   - Ensure CLI and GUI share consistent depth controls.
5. **Phase 5 – Cost-Aware Model Routing**
   - Assign models per role with budget-aware fallbacks.
   - Monitor token, latency, and accuracy metrics for regressions.
   - Publish tuning guides for operators.

## Cross-Cutting Requirements

- Capture decision rationales in code comments, docs, and issues.
- Maintain diagrams and pseudo-code as interfaces evolve.
- Record benchmark and cost results in STATUS.md and TASK_PROGRESS.md.
- Keep lines under 80 characters and cite sources in new documentation.

## Immediate Deliverables

- Roadmap, status, and changelog updates that describe the phased plan.
- Issues tracking the adaptive gate, evidence pipeline, and GraphRAG work.
- Specification and pseudo-code revisions covering the new components.
- Bench harness architecture notes to unblock implementation in Phase 4.

## Next Steps

Complete the documentation and issue updates described above, then begin Phase
1 implementation under the new tickets while monitoring cost and accuracy.
