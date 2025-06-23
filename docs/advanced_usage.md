# Advanced Usage Examples

This document provides advanced usage examples for the Autoresearch system, demonstrating how to leverage its capabilities for complex research tasks.

## Custom Reasoning Workflows

### Dialectical Reasoning with Multiple Loops

For complex research questions that benefit from extensive dialectical analysis:

```bash
autoresearch query "What are the environmental impacts of lithium mining for EV batteries?" \
  --reasoning-mode dialectical \
  --loops 3
```

This runs three complete dialectical cycles (Synthesizer → Contrarian → FactChecker), allowing for deeper exploration and refinement of the research question.

### Interactive Query Refinement

When running multiple loops you can refine the query after each cycle:

```bash
autoresearch search "initial question" --loops 2 --interactive
```

After the first cycle you'll be prompted:

```
Refine query or press Enter to continue (q to abort):
```

Enter an updated query string to guide the next cycle or `q` to abort.

### Chain of Thought for Step-by-Step Analysis

For problems that benefit from incremental reasoning:

```bash
autoresearch query "Explain the implications of quantum computing for cryptography" \
  --reasoning-mode chain-of-thought \
  --loops 5
```

This runs the Synthesizer agent five times, with each iteration building on the previous one, creating a chain of thought that shows the progression of reasoning.

### Direct Mode for Quick Answers

For straightforward questions that don't require dialectical analysis:

```bash
autoresearch query "What is the average lifespan of a blue whale?" \
  --reasoning-mode direct
```

This uses only the Synthesizer agent to provide a direct answer without the dialectical process.

## Agent Configuration

### Using Different Models for Different Agents

Configure different models for each agent to optimize for their specific roles:

```toml
# autoresearch.toml
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

### Customizing Prompt Templates

Customize the prompt templates for specific research domains:

```toml
# autoresearch.toml
[agent.Synthesizer.prompt_templates.execute]
template = """
You are a specialized medical researcher tasked with synthesizing information about {{query}}.
Focus on recent clinical studies and peer-reviewed research.
Provide a comprehensive analysis with particular attention to:
1. Current consensus in the medical community
2. Ongoing clinical trials
3. Potential applications in clinical practice

Your synthesis:
"""
```

## Advanced Search Configuration

### Combining Multiple Search Backends

Configure multiple search backends for comprehensive research:

```toml
# autoresearch.toml
[search]
backends = ["serper", "brave", "local_file", "local_git"]
results_per_backend = 5

[search.serper]
api_key = "${SERPER_API_KEY}"

[search.brave]
api_key = "${BRAVE_SEARCH_API_KEY}"

[search.local_file]
path = "/path/to/docs"
file_types = ["md", "pdf", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 50
```

Local backends build a searchable index of your files and repository history the
first time they run. You may optionally preprocess documents—for example by
converting PDFs to text—before indexing them. PDF and DOCX files are parsed by
default and commit diffs are stored alongside file snapshots. When local and web
backends are enabled together, Autoresearch merges the top
`results_per_backend` entries from each provider and ranks everything together
using BM25 and embedding similarity.

### Context-Aware Search with Entity Recognition

Enable context-aware search with entity recognition for more precise results:

```toml
# autoresearch.toml
[search.context_aware]
enabled = true
entity_recognition = true
topic_modeling = true
history_awareness = true
entity_weight = 0.4
topic_weight = 0.3
history_weight = 0.3
```

### Local File Backend

The `local_file` backend searches documents stored on disk. Enable this backend
when you have notes, PDFs, or other reference materials you want included in
results. Provide a `path` to the root directory and specify which `file_types`
should be indexed. All matching files are scanned recursively and merged with
web search results during ranking.

Indexing occurs the first time the backend runs. You can optionally preprocess
documents (for example using `pandoc` to convert PDFs) before they are added to
the index.

```toml
# autoresearch.toml
[search.local_file]
path = "/path/to/docs"
file_types = ["md", "pdf", "txt"]
```

A typical layout might look like:

```
research_docs/
├─ papers/
│  └─ example.pdf
├─ notes/
│  └─ summary.txt
```

Every matching file is added to the local index so it can be retrieved in
search results.

### Local Git Backend

The `local_git` backend indexes the history of a Git repository. Enable this
when you want search results to include commit messages and file snapshots from
your own projects. Set `repo_path` to your repository, list the `branches` you
want indexed, and limit how far back in history to search with `history_depth`.

```toml
# autoresearch.toml
[search.local_git]
repo_path = "/path/to/repo"
branches = ["main", "experiment"]
history_depth = 50
```

Each commit on the selected branches is scanned up to the specified depth, and
file revisions are stored individually for historical search.

As with local files, indexing happens automatically on first use. You can run a
pre-processing step to filter or transform repository content before indexing.

To enable both local backends along with other providers:

```toml
# autoresearch.toml
[search]
backends = ["serper", "local_file", "local_git"]
results_per_backend = 5
```

When multiple backends are enabled, Autoresearch merges the top
`results_per_backend` entries from each provider into a single ranked list so
local documents appear alongside web results. The ranking algorithm combines
BM25 scores and embedding similarity across backends for consistent relevance.

## Storage and Knowledge Graph

### Configuring Storage for Large Research Projects

Optimize storage for large research projects:

```toml
# autoresearch.toml
[storage]
db_path = "/path/to/research/database.duckdb"
ram_budget_mb = 2048
eviction_policy = "score"
vector_extension = true
vector_dimensions = 768

[storage.backup]
enabled = true
interval_hours = 24
max_backups = 7
compression = true
```

### Querying the Knowledge Graph

Use the CLI to query the knowledge graph directly:

```bash
# Find all claims related to a specific topic
autoresearch kg query "MATCH (c:Claim) WHERE c.topic CONTAINS 'climate change' RETURN c.text, c.source"

# Find connections between two concepts
autoresearch kg query "MATCH p=shortestPath((a:Concept)-[*]-(b:Concept)) WHERE a.name = 'renewable energy' AND b.name = 'carbon emissions' RETURN p"
```

## API Integration

### Running as a Service

Run Autoresearch as a service with the HTTP API:

```bash
# Start the API server
autoresearch serve --host 0.0.0.0 --port 8000

# Query using curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advancements in fusion energy?", "reasoning_mode": "dialectical", "loops": 2}'
```

### Webhook Integration

Configure webhooks to notify external systems when research is complete:

```toml
# autoresearch.toml
[api]
webhooks = ["https://example.com/webhook", "https://another-service.com/callback"]
webhook_timeout = 5
```

## Parallel Research

### Running Multiple Research Streams

Use parallel query execution for comparative research:

```bash
# Create a research plan file
cat > research_plan.json << EOF
{
  "query": "Compare solar and wind energy technologies",
  "agent_groups": [
    ["Synthesizer", "Contrarian", "FactChecker"],
    ["Researcher", "Critic", "Summarizer"]
  ]
}
EOF

# Execute parallel research
autoresearch parallel-query --plan research_plan.json
```

This runs two separate research streams with different agent combinations, allowing for comparative analysis.

## Extending with Custom Agents

### Creating a Domain-Specific Agent

Create a custom agent for specialized domains:

```python
# medical_researcher.py
from autoresearch.agents.base import Agent, AgentRole
from autoresearch.orchestration.state import QueryState
from autoresearch.config import ConfigModel

class MedicalResearcher(Agent):
    """Agent specialized in medical research."""
    
    role = AgentRole.SPECIALIST
    
    def execute(self, state: QueryState, config: ConfigModel) -> dict:
        """Execute medical research on the query."""
        # Get the adapter and model
        adapter = self.get_adapter(config)
        model = self.get_model(config)
        
        # Generate the prompt
        prompt = self.generate_prompt(
            "execute",
            query=state.query,
            context=state.get_context(),
            medical_databases=["PubMed", "Cochrane", "ClinicalTrials.gov"]
        )
        
        # Execute the query
        response = adapter.complete(prompt, model=model)
        
        # Process and return results
        return self.generate_claim(
            response=response,
            source="MedicalResearcher",
            results={
                "medical_findings": response,
                "clinical_relevance": self._assess_clinical_relevance(response)
            }
        )
    
    def _assess_clinical_relevance(self, response: str) -> str:
        """Assess the clinical relevance of the findings."""
        # Implementation details...
        return "High clinical relevance based on recent studies."

# Register the agent
from autoresearch.agents.registry import AgentFactory
AgentFactory.register("MedicalResearcher", MedicalResearcher)
```

### Loading Custom Agents

Load custom agents using the extension system:

```toml
# autoresearch.toml
[extensions]
paths = ["./custom_agents"]

[agent.MedicalResearcher]
enabled = true
model = "gpt-4"
```

## Advanced Output Formatting

### Custom Output Templates

Create custom output templates for specific formats:

```toml
# autoresearch.toml
[output.templates.academic]
format = """
# Research Report: {{query}}

## Abstract
{{results.synthesis}}

## Methodology
This research was conducted using dialectical reasoning with {{loops}} cycles.

## Findings
{{results.thesis}}

## Critical Analysis
{{results.antithesis}}

## Synthesis
{{results.synthesis}}

## References
{% for source in sources %}
- {{source.title}} ({{source.url}})
{% endfor %}
"""
```

## Knowledge Graph Queries

Persisted claims trigger ontology reasoning so that inferred triples are stored automatically. Use the `sparql` command to inspect the graph:

```bash
poetry run autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"
```

The command applies the configured reasoner before executing the query, returning any inferred relationships.

Use the custom template:

```bash
autoresearch query "What are the neurological effects of meditation?" --output-template academic
```

## Monitoring and Debugging

### Enabling Tracing

Enable detailed tracing for debugging:

```toml
# autoresearch.toml
[core]
tracing_enabled = true
tracing_level = "DEBUG"
```

### Using the Monitor

Use the interactive monitor to observe the system in real-time:

```bash
# Start the monitor
autoresearch monitor

# In another terminal, run a query
autoresearch query "What are the implications of AI on labor markets?"
```

The monitor shows real-time information about agent execution, token usage, and system state.

## Conclusion

These advanced usage examples demonstrate the flexibility and power of the Autoresearch system for complex research tasks. By combining different agents, reasoning modes, and configuration options, you can create customized research workflows tailored to your specific needs.
