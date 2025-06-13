# Agents

Autoresearch orchestrates multiple agents in a dialectical cycle. The default roster includes:

- **Synthesizer** – proposes initial answers.
- **Contrarian** – challenges assumptions and provides counter arguments.
- **Fact Checker** – verifies claims against reliable sources.

Agents communicate via a shared state object and can be customized in `autoresearch.toml`.

## Adding custom agents

1. Create a new subclass of `Agent` in `src/autoresearch/agents/`.
2. Register it with `AgentFactory.register("MyAgent", MyAgent)`.
3. Enable the agent in `autoresearch.toml` under `[agent.MyAgent]`.

## Adding new LLM adapters

1. Subclass `LLMAdapter` in `src/autoresearch/llm/adapters.py`.
2. Register the adapter via `LLMFactory.register("mybackend", MyAdapter)` (for example in `src/autoresearch/llm/__init__.py`).
3. Select it by setting `llm_backend = "mybackend"` in your configuration.
