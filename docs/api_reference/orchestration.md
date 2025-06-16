# Orchestration API

This page documents the Orchestration API, which provides components for coordinating agent execution in the Autoresearch system.

## Orchestrator

The `Orchestrator` class is the central coordination component that manages the execution of agents and the flow of data through the system.

::: autoresearch.orchestration.orchestrator.Orchestrator

## Query State

The `QueryState` class maintains the state of a query throughout the reasoning process.

::: autoresearch.orchestration.state.QueryState

## Reasoning Modes

The `ReasoningMode` enum defines the different reasoning strategies available in the system.

::: autoresearch.orchestration.reasoning.ReasoningMode

## Reasoning Strategy

The `ReasoningStrategy` protocol defines the interface for reasoning strategies.

::: autoresearch.orchestration.reasoning.ReasoningStrategy

## Chain of Thought Strategy

The `ChainOfThoughtStrategy` class implements a reasoning strategy that records intermediate thoughts at each loop.

::: autoresearch.orchestration.reasoning.ChainOfThoughtStrategy

## Orchestration Phases

The `Phase` enum defines the different phases of the orchestration process.

::: autoresearch.orchestration.phases.Phase

## Metrics

The `OrchestrationMetrics` class collects and reports metrics about the orchestration process.

::: autoresearch.orchestration.metrics.OrchestrationMetrics