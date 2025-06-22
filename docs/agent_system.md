# Agent System Architecture

## Overview

The Autoresearch agent system is a sophisticated framework for coordinating multiple AI agents in a dialectical reasoning process to produce evidence-backed answers to research queries. This document explains the architecture of the agent system, including the core components, agent types, and interaction patterns.

## Core Components

### Agent Base Class

The foundation of the agent system is the `Agent` base class, which defines the interface that all agents must implement. Key features of the base class include:

- **Role-based design**: Agents are assigned specific roles (Synthesizer, Contrarian, FactChecker, etc.)
- **Execution interface**: All agents implement an `execute()` method that processes the current state and returns results
- **LLM integration**: Agents use language models through a flexible adapter system
- **Configuration**: Agents can be configured with different models and prompt templates

### Agent Registry and Factory

The agent system uses a registry and factory pattern for managing agent types and instances:

- **AgentRegistry**: Maintains a central registry of all available agent types
- **AgentFactory**: Creates and caches agent instances, supporting dependency injection for testing

### Orchestration System

The orchestration system coordinates the execution of agents in a dialectical reasoning process:

- **Orchestrator**: Manages the execution of agents, handles errors, and persists results
- **QueryState**: Maintains the state of a query throughout the reasoning process
- **ReasoningMode**: Defines different reasoning strategies (direct, dialectical, chain-of-thought)

## Agent Types

### Dialectical Agents

The core dialectical agents implement a thesis-antithesis-synthesis cycle:

1. **Synthesizer**: Creates the initial thesis or synthesizes information from previous cycles
2. **Contrarian**: Challenges the thesis by identifying weaknesses or alternative viewpoints
3. **FactChecker**: Verifies claims and provides evidence-backed corrections

### Specialized Agents

Additional specialized agents extend the system's capabilities:

1. **Researcher**: Focuses on deep information gathering from multiple sources
2. **Critic**: Evaluates the quality of research and provides constructive feedback
3. **Summarizer**: Generates concise summaries of complex information
4. **Planner**: Structures complex research tasks into manageable steps
5. **Moderator**: Facilitates productive discussions between agents
6. **Domain Specialist**: Provides deep expertise in a specific field
7. **User Agent**: Represents user intent and preferences

## Reasoning Modes

The system supports three reasoning modes:

1. **Direct**: Uses only the Synthesizer agent for straightforward queries
2. **Dialectical**: Rotates through agents in a thesis→antithesis→synthesis cycle
3. **Chain-of-thought**: Loops the Synthesizer agent, recording intermediate thoughts

## Interaction Flow

The typical interaction flow in dialectical mode follows these steps:

1. User submits a query through the CLI or API
2. Orchestrator initializes the QueryState with the query
3. For each cycle (configurable number of loops):
   a. Synthesizer generates a thesis or synthesis
   b. Contrarian challenges the thesis
   c. FactChecker verifies claims and provides evidence
4. Results from each agent are persisted to storage
5. Final synthesis is generated and returned to the user

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Synthesizer   │────▶│   Contrarian    │────▶│   FactChecker   │
│                 │     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └────────┬────────┘
         │                                               │
         │                                               │
         └───────────────────┐         ┌─────────────────┘
                             │         │
                             ▼         ▼
                      ┌─────────────────────┐
                      │                     │
                      │     Orchestrator    │
                      │                     │
                      └─────────┬───────────┘
                                │
                                │
                      ┌─────────▼───────────┐
                      │                     │
                      │   Storage Manager   │
                      │                     │
                      └─────────────────────┘
```

## Extension Points

The agent system is designed to be extensible in several ways:

1. **New Agent Types**: Create new agent classes that inherit from the base Agent class
2. **Custom Reasoning Modes**: Implement new reasoning strategies by creating classes that follow the ReasoningStrategy protocol
3. **Alternative LLM Backends**: Add new LLM adapters to support different language model providers
4. **Storage Backends**: Implement alternative storage backends for different persistence needs

## Configuration

Agents can be configured through the `autoresearch.toml` configuration file:

```toml
[agent.Synthesizer]
model = "gpt-4"
enabled = true

[agent.Contrarian]
model = "claude-3-opus-20240229"
enabled = true

[agent.FactChecker]
model = "gpt-4"
enabled = true
```

## Best Practices

When extending the agent system:

1. **Follow the Agent Interface**: Ensure new agents implement the required methods
2. **Use Prompt Templates**: Define clear prompt templates for consistent agent behavior
3. **Handle Errors Gracefully**: Implement proper error handling in agent execution
4. **Test Agent Behavior**: Write comprehensive tests for agent functionality
5. **Document Agent Purpose**: Clearly document the purpose and behavior of new agents
