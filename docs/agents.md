# Agents

Autoresearch orchestrates multiple agents in a dialectical cycle. The default roster includes:

- **Synthesizer** – proposes initial answers.
- **Contrarian** – challenges assumptions and provides counter arguments.
- **Fact Checker** – verifies claims against reliable sources.

Additional specialized agents extend these roles:

- **Researcher** – performs in-depth information gathering.
- **Critic** – evaluates research quality and methodology.
- **Summarizer** – condenses complex information into short summaries.
- **Planner** – breaks down large tasks into manageable steps.
- **Moderator** – manages multi-agent discussions.
- **Domain Specialist** – provides expert knowledge for a field.
- **User Agent** – represents user preferences in the dialogue.

Agents communicate via a shared state object and can be customized in `autoresearch.toml`.

## Architecture

The agents component consists of several key classes:

- **Agent** - Base class for all agents, providing common functionality
- **AgentRole** - Enumeration of standard agent roles (Synthesizer, Contrarian, FactChecker, etc.)
- **AgentConfig** - Configuration for an agent
- **Mixins** - Reusable functionality for agents (PromptGenerator, ModelConfig, ClaimGenerator, ResultGenerator)
- **AgentRegistry** - Registry of available agent types
- **AgentFactory** - Factory for creating and retrieving agent instances

The diagram below shows the relationships between these classes and their interactions with other components:

![Agents Component](diagrams/agents.png)

## Adding custom agents

1. Create a new subclass of `Agent` in `src/autoresearch/agents/`.
2. Register it with `AgentFactory.register("MyAgent", MyAgent)`.
3. Enable the agent in `autoresearch.toml` under `[agent.MyAgent]`.

## Adding new LLM adapters

1. Subclass `LLMAdapter` in `src/autoresearch/llm/adapters.py`.
2. Register the adapter via `LLMFactory.register("mybackend", MyAdapter)` (for example in `src/autoresearch/llm/__init__.py`).
3. Select it by setting `llm_backend = "mybackend"` in your configuration.

