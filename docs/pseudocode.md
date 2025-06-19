# Pseudocode for Autoresearch

## 1. CLI Parsing & Dispatch (main.py)
```
function main():
    config = ConfigLoader.load_config()
    args = CLI.parse_args()  # Typer/Typer

    if args.command == "search":
        query = args.query
        output_format = args.output or detect_output_format()
        result = Orchestrator.run_query(query, config)
        OutputFormatter.format(result, output_format)

    elif args.command == "monitor":
        Monitor.start(config)

    elif args.command == "config":
        CLI.print_config(config)
    
    else:
        CLI.show_help()
```

## 2. Configuration Validation & Hot-Reload (config.py)
```
class ConfigLoader:
    watch_paths = ["autoresearch.toml", ".env"]

    function load_config():
        raw = read_toml("autoresearch.toml")
        env = load_env()
        config = merge_and_validate(raw, env)
        return config

    function watch_changes(callback):
        watchfile_paths(watch_paths, on_change=callback)

    function on_config_change():
        new_config = load_config()
        notify_observers(new_config)
```

## 3. Agent Loop & Orchestrator (agent.py)
```
class Orchestrator:
    function run_query(query, config):
        agents = config.agents.enabled_list()
        primus_index = config.primus_start
        state = initialize_query_state(query)

        for loop in range(config.loops):
            order = rotate_list(agents, start=primus_index)
            for agent_name in order:
                agent = AgentFactory.get(agent_name)
                result = agent.execute(state, config)
                log_agent_turn(agent_name, loop, result)
                state.update(result)
            primus_index = (primus_index + 1) % len(agents)

        return state.synthesize()
```

## 4. Search Retrieval & Source Tagging (search.py)
```
class SearchExecutor:
    function load_local_files(path):
        results = []
        for file in scan_directory(path):
            text = parse_file(file)
            results.append({ text: text, meta: { path: file, backend: "local_files" } })
        return results

    function index_git_repo(repo_path):
        results = []
        repo = open_repo(repo_path)
        for commit in repo.history():
            diff = read_commit_diff(repo, commit)
            results.append({ text: diff, meta: { commit: commit.sha, backend: "local_git" } })
        return results

    function execute(query):
        backends = config.search_backends
        raw_results = []
        for b in backends:
            if b.name == "local_files":
                for dir in b.paths:
                    raw_results.extend(load_local_files(dir))
            elif b.name == "local_git":
                raw_results.extend(index_git_repo(b.path))
            else:
                raw_results.extend(b.search(query))

        sources = []
        for item in raw_results:
            embedding = Embedder.embed(item.text)
            sources.append({ text: item.text, source: item.meta, embedding: embedding })

        return merge_sources(sources)
```

## 5. Graph Persistence & Eviction (storage.py)
```
class StorageManager:
    function persist_claim(claim):
        NetworkXGraph.add_node(claim)
        for rel in claim.relations:
            NetworkXGraph.add_edge(rel)

        DuckDB.insert("nodes", claim.to_row())
        DuckDB.insert("edges", claim.relation_rows())
        DuckDB.insert("embeddings", claim.embedding_vector)

        RDFStore.add_quads(claim.to_quads())

    function enforce_ram_budget():
        while memory_usage() > config.ram_budget_mb:
            node = LRUCache.evict_one()
            DuckDB.insert("nodes", node.to_row())
            NetworkXGraph.remove_node(node)
            PromMetrics.increment("duckdb_evictions_total")
```

## 6. Rendering & Synthesis (synthesis.py)
```
class SynthesizerAgent:
    function execute(state, config):
        prompt = build_prompt(state.claims, config)
        response = LLM.call(prompt, config.model)
        content = parse_llm_response(response)
        return content  # { answer, reasoning, citations, metrics }

class OutputFormatter:
    function format(result, format_type):
        if format_type == "json":
            print(JSON.stringify(result))
        else:
            print("# Answer")
            print(result.answer)
            print("## Citations")
            print_list(result.citations)
            print("## Reasoning")
            print_list(result.reasoning)
            print("## Metrics")
            print_metrics(result.metrics)
```

