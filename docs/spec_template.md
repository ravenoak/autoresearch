# Specification Template

This document is the canonical template for module specifications. Copy this
file into `docs/specs/` when defining a new spec. Each specification must
include algorithms, invariants, a proof sketch, simulation expectations, and
traceability to code and tests.

## Overview

Summarize the module's purpose, scope, and key interactions.

## Algorithms

- Detail core algorithms and data flows.
- Highlight assumptions and decision points.

## Invariants

- Record conditions that must always hold.
- Note constraints on inputs, state, or outputs.

## Proof Sketch

Explain why the algorithms uphold the invariants. Focus on reasoning rather
than formal proofs.

## Simulation Expectations

Describe how to simulate or test the algorithms. Define scenarios, metrics,
and any stochastic elements.

## Traceability

Link to implementation modules and related tests using relative paths.
