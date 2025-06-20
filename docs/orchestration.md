# Orchestration

The orchestration system is responsible for coordinating the execution of multiple agents in a dialectical reasoning process. It manages the flow of information between agents, tracks the state of the query, and synthesizes the final response.

## Reasoning Modes

The orchestration system supports three reasoning modes:

1. **Direct** - Uses only a single agent (typically the Synthesizer) to answer the query directly.
2. **Dialectical** - Rotates through multiple agents in a thesis→antithesis→synthesis cycle, with each agent building on the work of the previous agents.
3. **Chain-of-thought** - Loops a single agent (typically the Synthesizer) multiple times, allowing it to refine its answer through multiple iterations.

## Architecture

The orchestration component consists of several key classes:

- **Orchestrator** - Coordinates the execution of agents and manages the query state
- **QueryState** - Maintains the state of the query, including claims, sources, and results
- **OrchestrationMetrics** - Collects metrics about the orchestration process
- **ReasoningMode** - Enumeration of supported reasoning modes
- **ChainOfThoughtStrategy** - Strategy for executing chain-of-thought reasoning

The Orchestrator class provides methods for:
- Running queries through dialectical agent cycles
- Running parallel queries with multiple agent groups
- Executing individual agents and cycles
- Managing token usage and metrics
- Handling errors and timeouts

The diagram below shows the relationships between these classes and their interactions with other components:

![Orchestration Component](diagrams/orchestration.png)

## Execution Flow

1. The user submits a query through the CLI, API, or monitor interface
2. The Orchestrator parses the configuration and initializes the query state
3. For each loop:
   - The Orchestrator executes a cycle of agents
   - Each agent receives the current state and updates it with its results
   - Claims are persisted to storage
   - Metrics are collected
4. The final state is synthesized into a QueryResponse
5. The response is returned to the user
