# Agent Communication

Autoresearch can optionally let agents exchange short messages during each
reasoning cycle.
When `enable_agent_messages` is `true`, any agent may call `send_message()` to
share information with its peers. These messages are stored on the shared
`QueryState` and can be retrieved with `get_messages()` in later steps.

## Coalitions

Agents can be grouped into named coalitions for message broadcasting. Define
them in a `[coalitions]` section. Messages sent by one member are delivered to
all other agents in the same coalition.
Coalition names may also be listed in the `agents` array of your configuration
to execute all members as a unit during each cycle.

```toml
[coalitions]
research_team = ["Synthesizer", "Contrarian", "FactChecker"]

enable_agent_messages = true
```

## Feedback Mechanism

Enabling `enable_feedback` lets agents such as the Critic or UserAgent provide
feedback about other agents' outputs. Feedback messages are stored like normal
agent messages and can influence subsequent reasoning.

```toml
enable_feedback = true
```

For a brief overview of available agents see
[Agents Overview](agents_overview.md).
