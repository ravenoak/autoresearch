# Advanced Usage Examples

This document provides advanced usage examples for the Autoresearch system, demonstrating how to leverage its capabilities for complex research tasks.

## Custom Reasoning Workflows

### Dialectical Reasoning with Multiple Loops

For complex research questions that benefit from extensive dialectical analysis:

```bash
autoresearch search "What are the environmental impacts of lithium mining for EV batteries?" \
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
autoresearch search "Explain the implications of quantum computing for cryptography" \
  --reasoning-mode chain-of-thought \
  --loops 5
```

This runs the Synthesizer agent five times, with each iteration building on the previous one, creating a chain of thought that shows the progression of reasoning.

### Direct Mode for Quick Answers

For straightforward questions that don't require dialectical analysis:

```bash
autoresearch search "What is the average lifespan of a blue whale?" \
  --reasoning-mode direct
```

This uses only the Synthesizer agent to provide a direct answer without the dialectical process.

### Starting with a Specific Agent

You can control which agent begins the dialectical cycle using `--primus-start`:

```bash
autoresearch search "Compare JPEG and PNG compression" \
  --reasoning-mode dialectical \
  --primus-start 1
```

This example starts with the Contrarian agent (index `1`) before rotating through the others.

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

### Tuning Search Ranking Weights

You can evaluate how different relevance weights perform by running the
`evaluate_ranking.py` script against a labelled dataset. The repository provides
`examples/search_evaluation.csv` containing sample query results with ground
truth relevance labels.

```bash
python scripts/evaluate_ranking.py examples/search_evaluation.csv
```

To automatically search for the best combination of weights, use
`optimize_search_weights.py`. The script reads a labelled evaluation CSV,
performs a simple grid search and writes the tuned values back to the provided
configuration file (defaults to `examples/autoresearch.toml`):

```bash
python scripts/optimize_search_weights.py \
  examples/search_evaluation.csv examples/autoresearch.toml
```

After running the optimization the file's `bm25_weight`,
`semantic_similarity_weight`, and `source_credibility_weight` values reflect the
best-performing configuration. Our sample dataset favors semantic similarity and
source credibility, resulting in the following tuned weights:

```toml
[search]
semantic_similarity_weight = 0.85
bm25_weight = 0.05
source_credibility_weight = 0.1
```

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

### Inline Graph Visualization

Display a condensed view of the knowledge graph built during a search:

```bash
autoresearch search "Explain AI ethics" --visualize
```
The `--visualize` option now prints an ASCII summary of query metrics along with
the knowledge graph table.

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
from autoresearch.config.models import ConfigModel

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
autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"
```

The command applies the configured reasoner before executing the query, returning any inferred relationships.

Use the custom template:

```bash
autoresearch search "What are the neurological effects of meditation?" --output-template academic
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

Use the monitor commands to observe the system in real-time:

```bash
# Show metrics once
autoresearch monitor

# Continuously refresh metrics
autoresearch monitor -w

# In another terminal, run a query while watching
autoresearch search "What are the implications of AI on labor markets?"
```

The monitor shows real-time information about agent execution, token usage, and system state.

## Adaptive Token Budgeting

Autoresearch automatically scales the available token budget based on the
complexity of each query. The orchestrator considers query length and the number
of loops, capping excessive budgets while ensuring enough tokens are available.
When agents run in parallel groups each group receives a fair share of the
budget. Usage per query is stored in `tests/integration/baselines/query_tokens.json`
so the `check_token_regression.py` script can detect regressions.

## Prompt Compression

When prompts grow too long they may exceed the available token budget. The `autoresearch.synthesis` module provides utilities that shorten prompts by truncating the middle section and inserting an ellipsis. This keeps essential context while staying under the limit.

## Guided Tour and Help Overlay

When you first launch the Streamlit interface a short guided tour explains the main controls. Use the **Got it** button to dismiss the overlay. You can reopen the tour at any time from the sidebar via **Show Help**. The overlay highlights the query input, configuration sidebar and run button so you know where to start.

## Conclusion

These advanced usage examples demonstrate the flexibility and power of the Autoresearch system for complex research tasks. By combining different agents, reasoning modes, and configuration options, you can create customized research workflows tailored to your specific needs.
