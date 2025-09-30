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
            results.append({
                text: text,
                meta: { path: file, backend: "local_files" },
            })
        return results

    function index_git_repo(repo_path):
        results = []
        repo = open_repo(repo_path)
        for commit in repo.history():
            diff = read_commit_diff(repo, commit)
            results.append({
                text: diff,
                meta: { commit: commit.sha, backend: "local_git" },
            })
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
            sources.append({
                text: item.text,
                source: item.meta,
                embedding: embedding,
            })

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

## 6a. Answer Auditing, Re-Verification & Hedging (state.py)
```
class AnswerAuditor:
    function review(state, policy):
        audits = collect_claim_audits(state.claims)
        unsupported = filter(audits, status == "unsupported")
        for claim in unsupported:
            retry = Search.external_lookup(claim.text,
                                           max_results=policy.max_retry_results,
                                           return_handles=True)
            record = score_entailment(claim, retry)
            audits.append(record.to_payload())
        if policy.require_human_ack and unsupported.any():
            notify_operator(audits)
            await_ack(policy.timeout_s)
        hedged = hedge_answer(state.results.final_answer, audits,
                              policy.hedge_mode)
        return {
            answer: hedged,
            reasoning: annotate_claims(state.claims, audits,
                                       policy.explain_conflicts),
            claim_audits: audits,
            metrics: { answer_audit: snapshot(audits) }
        }

class QueryState:
    function synthesize(policy = AuditPolicy.load()):
        audited = AnswerAuditor.review(self, policy)
        merge_sources(self.sources, audited.new_sources)
        return QueryResponse(
            query=self.query,
            answer=audited.answer,
            reasoning=audited.reasoning,
            claim_audits=audited.claim_audits,
            metrics=merge(metadata, audited.metrics)
        )

class AuditPolicy:
    function load():
        return AuditPolicy(
            max_retry_results=config.audit.max_retry_results,
            require_human_ack=config.audit.require_human_ack,
            timeout_s=config.audit.operator_timeout_s,
            hedge_mode=config.audit.hedge_mode,
            explain_conflicts=config.audit.explain_conflicts
        )
```

## 7. Adaptive Gate (orchestration/gating.py)
```
function run_orchestration(query, config):
    draft, scout_evidence = scout_pass(query, config)
    signals = compute_signals(draft, scout_evidence, config)
    decision = gate_policy(signals, config)

    if decision.action == "exit":
        audited = audit_claims(draft, scout_evidence, config)
        return finalize(audited, decision, config)

    debate_state = initialize_debate_state(draft, scout_evidence)
    for cycle in range(decision.max_cycles):
        thesis = thesis_agent.act(debate_state)
        antithesis = antithesis_agent.challenge(debate_state, thesis)
        fact_check = fact_checker.audit(antithesis, config)
        debate_state.update(thesis, antithesis, fact_check)
        if debate_state.should_stop():
            break

    synthesis = synthesis_agent.compose(debate_state)
    return finalize(synthesis, decision, config)
```

## 8. Claim Auditing (evidence/audit.py)
```
function audit_claims(candidate, evidence, config):
    claims = extract_claims(candidate)
    audits = []
    for claim in claims:
        retrievals = iterative_retrieval(claim, evidence, config)
        entailment = score_entailment(claim, retrievals)
        stability = self_check(claim, config)
        status = classify_status(entailment, stability, config)
        audits.append({
            "claim": claim,
            "status": status,
            "sources": top_sources(retrievals),
            "entailment": entailment,
            "stability": stability,
        })

    if unsupported(audits):
        candidate = rewrite_with_hedges(candidate, audits)
        return audit_claims(candidate, evidence, config)

    return {
        "content": candidate,
        "audits": audits,
    }
```

## 9. Planner and Coordinator (planning/coordinator.py)
```
class PlannerPromptBuilder:
    function build(state):
        schema = json_schema(
            objectives=array(str),
            exit_criteria=array(str),
            tasks=array({
                id: str,
                question: str,
                objectives: array(str),
                tool_affinity: map(str -> float),
                exit_criteria: array(str),
                explanation: str,
            }),
        )
        return base_prompt + schema + planner_feedback(state)

class PlannerAgent:
    function execute(state, config):
        prompt = PlannerPromptBuilder.build(state)
        raw_plan = adapter.generate(prompt, model=config.model)
        warnings = state.set_task_graph(parse_json(raw_plan))
        state.record_planner_trace(
            prompt=prompt,
            raw_response=raw_plan,
            normalized=state.task_graph,
            warnings=warnings,
        )
        return state.task_graph

class TaskCoordinator:
    function ready_tasks():
        nodes = [TaskGraphNode(task) for task in state.task_graph.tasks]
        sorted_nodes = sort(
            nodes,
            key=(ready_rank(node), -node.max_affinity(), depth(node), node.id),
        )
        return [node for node in sorted_nodes if node.is_available()]

    function record_react_step(task_id, thought, action, tool):
        scheduler = {
            selected: TaskGraphNode(task_id).snapshot(),
            candidates: [node.snapshot() for node in ready_tasks()],
        }
        metadata = {
            unlock_events: unlocked_tasks(),
            task_depth: depth(task_id),
            affinity_delta: top_affinity(task_id) - affinity(task_id, tool),
            scheduler: scheduler,
        }
        entry = {
            task_id: task_id,
            step: next_step(task_id),
            phase: phase,
            thought: thought,
            action: action,
            tool: tool,
            metadata: metadata,
        }
        state.add_react_trace(entry)
        state.metadata.coordinator.decisions.append(
            {task_id: task_id, step: entry.step, scheduler: scheduler}
        )
        return entry
```

## 10. Graph-Augmented Retrieval (retrieval/graph.py)
```
function build_session_graph(evidence):
    graph = Graph()
    for doc in evidence:
        entities = extract_entities(doc)
        relations = extract_relations(doc)
        graph.add_entities(entities)
        graph.add_relations(relations)
    return graph

function augment_query(graph, query):
    neighbors = graph.neighbors_of(query.key_entities)
    summary = graph.community_summary(query.topic)
    return compose_prompt(query, neighbors, summary)

function contradiction_check(graph, answer):
    implied = infer_relations(answer)
    conflicts = []
    for relation in implied:
        if graph.contradicts(relation):
            conflicts.append(relation)
    return conflicts
```

## 11. Evaluation Harness (tests/benchmarks/harness.py)
```
function run_benchmarks(config, suite):
    results = []
    for case in suite.cases:
        response = Orchestrator.run_query(case.prompt, config)
        metrics = evaluate_case(case, response)
        results.append({
            "case_id": case.id,
            "metrics": metrics,
        })

    aggregate = aggregate_metrics(results)
    persist_results(results, aggregate, config)
    return aggregate
```
