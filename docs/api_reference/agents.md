# Agents API

This page documents the Agents API, which provides classes and functions for implementing and managing agents in the Autoresearch system.

## Agent Base Class

The `Agent` class is the foundation of the agent system, defining the interface that all agents must implement.

::: autoresearch.agents.base.Agent

## Agent Roles

The `AgentRole` enum defines the standard roles for agents in the dialectical system.

::: autoresearch.agents.base.AgentRole

## Agent Configuration

The `AgentConfig` class defines the configuration for an agent.

::: autoresearch.agents.base.AgentConfig

## Agent Registry

The `AgentRegistry` class provides a central registry for all available agent types.

::: autoresearch.agents.registry.AgentRegistry

## Agent Factory

The `AgentFactory` class provides a factory for creating and retrieving agent instances.

::: autoresearch.agents.registry.AgentFactory

## Dialectical Agents

### Synthesizer

The `Synthesizer` agent creates the initial thesis or synthesizes information from previous cycles.

::: autoresearch.agents.dialectical.synthesizer.SynthesizerAgent

### Contrarian

The `Contrarian` agent challenges the thesis by identifying weaknesses or alternative viewpoints.

::: autoresearch.agents.dialectical.contrarian.ContrarianAgent

### FactChecker

The `FactChecker` agent verifies claims and provides evidence-backed corrections.

::: autoresearch.agents.dialectical.fact_checker.FactChecker

## Specialized Agents

### Researcher

The `Researcher` agent focuses on deep information gathering from multiple sources.

::: autoresearch.agents.specialized.researcher.ResearcherAgent

### Critic

The `Critic` agent evaluates the quality of research and provides constructive feedback.

::: autoresearch.agents.specialized.critic.CriticAgent

### Summarizer

The `Summarizer` agent generates concise summaries of complex information.

::: autoresearch.agents.specialized.summarizer.SummarizerAgent

### Planner

The `Planner` agent structures complex research tasks into manageable steps.

::: autoresearch.agents.specialized.planner.PlannerAgent

## Agent Mixins

The agent mixins provide common functionality that can be shared across different agent types.

::: autoresearch.agents.mixins.PromptGeneratorMixin
::: autoresearch.agents.mixins.ModelConfigMixin
::: autoresearch.agents.mixins.ClaimGeneratorMixin
::: autoresearch.agents.mixins.ResultGeneratorMixin

## Prompt Templates

The prompt templates module provides templates for generating prompts for different agent types.

::: autoresearch.agents.prompts


