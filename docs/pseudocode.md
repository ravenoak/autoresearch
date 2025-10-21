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

The search stubs keep instrumentation counters for every embedding lookup,
backend invocation, and storage add so regression tests can compare legacy
and vector-enabled flows without diffing raw documents. These counters feed
the parity assertions in `tests/unit/test_core_modules_additional.py`, which
expect instance `add_calls` and lookup bindings to match across phases.
【F:tests/unit/test_core_modules_additional.py†L363-L441】

## 4a. Semantic Tree Helpers (search/context.py, trees/semantic.py)
```
function build_semantic_tree(corpus, config):
    # Offline summarisation batches corpus slices and caches latent topics.
    topic_chunks = search.context.segment_corpus(
        corpus,
        window=config.search.segment_window,
    )
    root = trees.semantic.SemanticTree.root(
        name="root",
        metadata={"source": corpus.handle},
    )
    for chunk in topic_chunks:
        summary = Summariser.offline(chunk.text, config.summary)
        centroid = Embedder.embed(summary, model=config.summary.embedding)
        root.insert(
            trees.semantic.Node(
                text=summary,
                embedding=centroid,
                provenance=chunk.metadata,
            )
        )

    cache_path = config.cache.semantic_tree_path
    trees.semantic.persist(root, cache_path)
    telemetry.emit(
        "search.tree.persisted",
        {
            "path": cache_path,
            "nodes": root.count_nodes(),
            "offline_batches": len(topic_chunks),
        },
    )
    return root
```

```
function hierarchical_traversal(query, tree, config):
    # Online traversal expands beams with calibration from the latest query.
    beams = BeamTracker.start(
        root=tree,
        width=config.search.hierarchy.beam_width,
    )
    calibrator = BeamCalibrator(
        scorer=ScoreModel.load(config.search.calibration_model),
        temperature=config.search.hierarchy.temperature,
    )

    for depth in range(config.search.hierarchy.max_depth):
        frontier = beams.frontier()
        query_vec = Embedder.embed(query, model=config.search.query_encoder)
        scored = calibrator.score(frontier, query_vec)
        beams.expand(scored, limit=config.search.hierarchy.max_expansions)
        telemetry.emit(
            "search.tree.expansion",
            {
                "depth": depth,
                "frontier": len(frontier),
                "expanded": beams.expanded_count(depth),
                "calibration_bias": calibrator.bias,
            },
        )
        if beams.is_converged(config.search.hierarchy.convergence_threshold):
            break

    ranked_paths = beams.best_paths()
    telemetry.emit(
        "search.tree.paths",
        {
            "paths": len(ranked_paths),
            "best_score": ranked_paths[0].score if ranked_paths else None,
        },
    )
    return ranked_paths
```

## 4b. Scout Pass & Tree Refresh (search/passes.py)
```
function scout_pass(query, corpus, config):
    cache = TreeCache.resolve(config.cache.semantic_tree_path)
    if cache.is_stale(corpus.signature):
        telemetry.emit(
            "search.tree.cache_stale",
            {"signature": corpus.signature},
        )
        tree = build_semantic_tree(corpus, config)
    else:
        tree = cache.load()

    ranked_paths = hierarchical_traversal(query, tree, config)
    path_scores = [path.score for path in ranked_paths]
    telemetry.register_gate_history(
        query=query,
        scores=path_scores,
        expansions=[p.expansions for p in ranked_paths],
    )
    return {
        "paths": ranked_paths,
        "tree_signature": tree.signature,
        "stale_fallback": cache.is_stale(corpus.signature),
    }
```

```
function audit_claims(claims, scout_payload, config):
    tree = TreeCache.resolve(config.cache.semantic_tree_path).load()
    if scout_payload.tree_signature != tree.signature:
        telemetry.emit(
            "search.tree.signature_mismatch",
            {
                "expected": scout_payload.tree_signature,
                "actual": tree.signature,
            },
        )
        tree = build_semantic_tree(config.corpus, config)

    traversal = hierarchical_traversal(
        query=claims.parent_query,
        tree=tree,
        config=config,
    )
    calibrated = [path.score for path in traversal]
    telemetry.update_reverification_stats(
        path_scores=calibrated,
        total_expansions=sum(path.expansions for path in traversal),
    )
    return ClaimAuditor.review(
        claims,
        support_paths=traversal,
        calibration=calibrated,
    )
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
        layers = config.output.layers or ["baseline"]
        layered = LayeredFormatter.apply(result, layers)
        if format_type == "json":
            print(JSON.stringify(layered))
        else:
            print("# Answer")
            print(layered.answer)
            print("## Citations")
            print_list(layered.citations)
            print("## Reasoning")
            print_list(layered.reasoning)
            print("## Metrics")
            print_metrics(layered.metrics)
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

## 6b. Desktop Cancellation & Recovery (main_window.py)
```
class AutoresearchMainWindow:
    function request_cancel():
        if not self.is_query_running:
            return

        confirmed = QMessageBox.warning(
            self,
            title="Cancel query?",
            message="Cancel the active desktop query?",
            buttons=[QMessageBox.Cancel, QMessageBox.Destructive],
        )

        if confirmed != QMessageBox.Destructive:
            return

        self.status_bar.set_message("Cancelling…")
        self.metrics_timer.stop()
        self.query_panel.setEnabled(False)
        self.worker.cancel()
        self.worker.on_finished(self._complete_cancellation)

    function _complete_cancellation(result):
        try:
            result.unwrap()
            self._reset_after_success(result.payload)
        except WorkerError as error:
            self._show_failure_dialog(error)
        finally:
            self._teardown_worker()
            self._reset_status_bar()

    function _show_failure_dialog(error):
        QMessageBox.critical(
            self,
            title="Query failed",
            message=f"Worker failed: {error.code}",
            details=error.traceback,
        )
        self.results_display.annotate_error(error)

    function _teardown_worker():
        self.worker.cancel()
        self.worker.deleteLater()
        self.worker = None

    function _reset_status_bar():
        self.status_bar.set_message("Ready")
        self.metrics_timer.start(DEFAULT_TIMER_INTERVAL)
        self.is_query_running = False
        self.query_panel.setEnabled(True)
        self.status_bar.reset_counters()
```

## 6c. Desktop Launch & Query Lifecycle (PySide6 modules)

See the [PySide desktop specification](specs/pyside-desktop.md) and the
[PySide6 layout diagram](diagrams/pyside6_layout.md) for the widget structure
referenced below.

```
module autoresearch.ui.desktop.main:
    function main():
        configure_high_dpi_attributes()
        app = QApplication(sys.argv)
        window = AutoresearchMainWindow()
        window.show()
        return app.exec()

module autoresearch.ui.desktop.main_window:
    function __init__():
        self.query_panel = QueryPanel()
        self.results_display = ResultsDisplay()
        self.progress_bar = QProgressBar()
        self._metrics_provider = get_orchestration_metrics or None
        self.setup_connections()
        self._start_metrics_timer()
        self.load_configuration()

    function setup_connections():
        self.query_panel.query_submitted.connect(self.on_query_submitted)
        self.query_panel.query_cancelled.connect(self.on_query_cancelled)
        if self.export_manager:
            self.export_manager.export_requested.connect(
                self.on_export_requested
            )

    function on_query_submitted(query):
        if not query.strip():
            self._show_warning(
                "Empty Query", "Please enter a query before submitting."
            )
            return
        session_id = self._resolve_session_id()
        self.current_query = query
        self.run_query()

    function run_query():
        if not self.orchestrator or not self.config:
            self._show_critical(
                "System Error",
                "Autoresearch core components are not available."
            )
            return
        self.query_panel.set_busy(True)
        self.progress_bar.setRange(0, 0)
        self._set_status_message("Running query…")
        worker = QueryWorker(self.orchestrator, self.current_query,
                             self.config, self, self._active_session_id)
        QThreadPool.globalInstance().start(worker)

    class QueryWorker(QRunnable):
        function run():
            try:
                result = orchestrator.run_query(query, config)
                QTimer.singleShot(0, lambda: parent.display_results(result,
                                                                   session_id))
            except Exception as error:
                QTimer.singleShot(0, lambda: parent.display_error(error,
                                                                  session_id))

    function display_results(result, session_id):
        self.query_panel.set_busy(False)
        self.results_display.display_results(result)
        self._latest_metrics_payload = getattr(result, "metrics", None)
        self._refresh_status_metrics()
        telemetry.emit("ui.query.completed", self._build_query_payload(
            session_id, status="completed",
            extra={"result_has_metrics": bool(self._latest_metrics_payload)}))

    function display_error(error, session_id):
        self.query_panel.set_busy(False)
        self._set_status_message("Query failed")
        telemetry.emit("ui.query.failed", self._build_query_payload(
            session_id,
            status="failed",
            extra={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        ))

    function on_query_cancelled(session_id):
        self.query_panel.set_busy(False)
        self._set_status_message("Query cancelled")
        telemetry.emit(
            "ui.query.cancelled",
            self._build_query_payload(session_id, status="cancelled"),
        )

module autoresearch.ui.desktop.query_panel:
    function on_run_clicked():
        query = self.query_input.toPlainText().strip()
        session_id = uuid.uuid4().hex
        self._active_session_id = session_id
        telemetry.emit("ui.query.submitted", {
            "session_id": session_id,
            "query_length": len(query),
            "reasoning_mode": self.current_reasoning_mode,
            "loops": self.current_loops,
        })
        self.query_submitted.emit(query)

    function set_busy(is_busy):
        for widget in self._iter_control_widgets():
            widget.setEnabled(not is_busy)
        if self.cancel_button:
            self.cancel_button.setVisible(is_busy)
            self.cancel_button.setEnabled(is_busy)
        if not ReasoningMode:  # fallback when orchestration enums are missing
            self.reasoning_mode_combo.setCurrentText("balanced")

module autoresearch.ui.desktop.results_display:
    function display_answer(result):
        if self._web_engine_available and QWebEngineView is not None:
            html = render_markdown_as_html(result)
            self.answer_view.setHtml(html)
        else:  # fallback when Qt WebEngine is absent
            self.answer_fallback_label.setText(
                "Qt WebEngine is unavailable. Rendering simplified text."
            )
            html = render_markdown_as_html(result)
            set_html = getattr(self.answer_view, "setHtml", None)
            if callable(set_html):
                set_html(html)
            else:
                self.answer_view.setText(strip_markup(html))

    function display_metrics(result):
        metrics = getattr(result, "metrics", None)
        self.metrics_dashboard.update_metrics(metrics)

module autoresearch.ui.desktop.metrics_dashboard:
    function update_metrics(metrics):
        if self._chart_available and metrics:
            snapshot = self._extract_snapshot(metrics)
            self._append_snapshot(snapshot)
            self._render_chart()
        else:  # fallback text mode when matplotlib is missing or metrics absent
            self._update_summary(no_data=not metrics)

module autoresearch.ui.desktop.telemetry:
    function emit(event, payload):
        qCInfo(category, message_from(payload))
        dispatcher = get_dispatcher()
        if dispatcher:
            dispatcher(event, payload)
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

## 8b. Reverification Loop (`orchestration/reverify.py`)
```
function reverify(state_id, options):
    state, config = clone_state(state_id)
    claims = state.claims or extract_claims(state.final_answer)
    attempts = 0
    while attempts < options.max_retries:
        attempts += 1
        audits, verification = fact_checker.execute(claims, config, options)
        record_history(state, audits, attempts, options)
        if audits_are_stable(audits):
            break
        reset_transient_state(state, claims)
        sleep(options.retry_backoff)
    persist_claims(StorageManager, claims + verification)
    update_metadata(state, audits, attempts)
    return state.synthesize()
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

## 12. PRDV Verification Loop (planner/research/debate/validate)
The evaluation harness expects every summary to include dataset metadata, the
active configuration signature, and planner/routing telemetry. Behavior and
unit tests assert both populated values and `None` fallbacks so CLI tables stay
aligned with the schema.

```
function run_prdv_cycle(state, harness):
    plan = PlannerAgent.execute(state, config)
    research = Researcher.collect(plan, state, config)
    debate = DebateLoop.run(research, state, config)
    validated = Validator.confirm(debate, state, config)

    telemetry = gather_prdv_metrics(state, plan, debate)
    summary = EvaluationSummary(
        dataset=telemetry.dataset,
        run_id=telemetry.run_id,
        started_at=telemetry.started,
        completed_at=telemetry.completed,
        total_examples=telemetry.total_examples,
        config_signature=telemetry.config_signature,
        planner=PlannerMetrics(avg_depth=telemetry.planner.avg_depth),
        routing=RoutingMetrics(
            avg_delta=telemetry.routing.avg_delta,
            total_delta=telemetry.routing.total_delta,
            avg_decisions=telemetry.routing.avg_decisions,
            strategy=telemetry.routing.strategy,
        ),
        example_csv=telemetry.artifacts.example_csv,
        summary_csv=telemetry.artifacts.summary_csv,
    )
    harness.persist(summary)
    return validated
```

## 13. Desktop Startup & Query Cycle (ui/desktop/main_window.py)
```
class AutoresearchMainWindow(QMainWindow):
    function __init__():
        setup_ui()  # splitter binds QueryPanel and ResultsDisplay
        setup_connections()  # QueryPanel.query_submitted → on_query_submitted
        _start_metrics_timer()  # QTimer polls orchestrator metrics facade
        load_configuration()

    function load_configuration():
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_config()
            orchestrator = Orchestrator()
            status = "Configuration loaded - ready for queries"
        except Exception as exc:
            _show_warning("Configuration Error", render_config_error(exc))
            status = "Configuration error - limited functionality"
        _set_status_message(status)

    function on_query_submitted(query):
        if not query.strip():
            _show_warning("Empty Query", prompt_for_input())
            return
        if is_query_running:
            _show_information("Query in Progress", wait_notice())
            return
        current_query = query
        session_id = _resolve_session_id()
        _query_started_at = now()
        telemetry.emit(
            "ui.query.submitted",
            {
                "session_id": session_id,
                "query_length": len(query),
                "reasoning_mode": query_panel.current_reasoning_mode,
                "loops": query_panel.current_loops,
            },
        )
        run_query(session_id)

    function run_query(session_id):
        if orchestrator is None or config is None:
            _show_critical("System Error", missing_core_notice())
            return
        _merge_query_panel_configuration()
        _enter_query_busy_state()

        class QueryWorker(QRunnable):
            function run():
                try:
                    result = orchestrator.run_query(current_query, config)
                    QTimer.singleShot(
                        0, lambda: display_results(result, session_id)
                    )
                except Exception as exc:
                    QTimer.singleShot(
                        0, lambda: display_error(exc, session_id)
                    )

        QThreadPool.globalInstance().start(QueryWorker())

    function on_query_cancelled(session_id):
        if not is_query_running or session_id != _active_session_id:
            return
        _leave_query_busy_state()
        telemetry.emit(
            "ui.query.cancelled",
            _build_payload(session_id, status="cancelled"),
        )

    function display_results(result, session_id):
        _leave_query_busy_state()
        ResultsDisplay.display_results(result)
        update_export_options(result)
        metrics_payload = getattr(result, "metrics", None)
        _latest_metrics_payload = metrics_payload
        telemetry.emit(
            "ui.query.completed",
            _build_payload(
                session_id,
                status="completed",
                extra={"result_has_metrics": bool(metrics_payload)},
            ),
        )
        _refresh_status_metrics()  # metrics timer updates status labels
        session_manager.add_session(uuid4(), title_from(current_query))
        _set_status_message("Query completed")

    function display_error(error, session_id):
        _leave_query_busy_state()
        _show_critical("Query Error", detail(error))
        telemetry.emit(
            "ui.query.failed",
            _build_payload(
                session_id,
                status="failed",
                extra={
                    "error_type": error.__class__.__name__,
                    "error_message": str(error),
                },
            ),
        )
        _set_status_message("Query failed")
        _refresh_status_metrics()

    function _show_warning(title, message):
        if _suppress_dialogs():  # AUTORESEARCH_SUPPRESS_DIALOGS bypasses UI
            _log_dialog("warning", title, message)
            return
        QMessageBox.warning(self, title, message)
```

Busy-state transitions live on `AutoresearchMainWindow` via
`_enter_query_busy_state()` and `_leave_query_busy_state()`. They keep status
messaging, progress indicators, and `is_query_running` updates coordinated.

Desktop telemetry sends the following analytics events via `telemetry.emit`:

- `ui.query.submitted`: `session_id`, `query_length`, `reasoning_mode`, `loops`.
- `ui.query.completed`: adds `duration_ms` and `result_has_metrics`.
- `ui.query.failed`: adds `duration_ms`, `error_type`, `error_message`.
- `ui.query.cancelled`: includes `duration_ms` alongside the shared fields.

`_apply_configuration_overrides()` copies QueryPanel overrides, then normalises
the `reasoning_mode` value through `_coerce_reasoning_mode()` so downstream
ConfigModel validation and reasoning transcripts remain consistent.

```
    function _merge_query_panel_configuration():
        overrides = QueryPanel.get_configuration()
        if overrides:
            _apply_configuration_overrides(overrides)

    function _apply_configuration_overrides(overrides):
        updates = copy(overrides)
        if "reasoning_mode" in updates:
            updates["reasoning_mode"] =
                _coerce_reasoning_mode(updates["reasoning_mode"])

        if hasattr(config, "model_copy"):
            config = config.model_copy(update=updates)
        elif isinstance(config, Mapping):
            config = {**config, **updates}
        else:
            for key, value in updates.items():
                setattr(config, key, value)

        ConfigEditor.load_config(config)
```

`_coerce_reasoning_mode()` follows the runtime guard: it tries to build a
`ReasoningMode` from string inputs and otherwise preserves the existing enum so
desktop reasoning histories stay intact.

## 14. PySide6 Desktop Loop (ui/desktop/main.py)
```
function desktop.main(argv):
    configure_high_dpi_scaling()
    try:
        app = QApplication(argv)
    except ImportError:
        print("PySide6 missing; install with `uv add PySide6`")
        return 1

    app.setApplicationName("Autoresearch")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Autoresearch Project")

    try:
        window = AutoresearchMainWindow()
        window.show()
        return app.exec()
    except Exception as exc:
        handle_startup_error(window, exc)
        return 1
```

AutoresearchMainWindow.__init__ immediately calls `setup_connections()`,
which wires query, configuration, session, and export signals to their
handlers as part of its startup routine. This keeps the signal wiring
co-located with widget initialization and ensures new panels register
their slots by extending `setup_connections()`.

function AutoresearchMainWindow.run_query():
    if orchestrator is None or config is None:
        _show_critical("System Error", missing_core_notice())
        return
    _merge_query_panel_configuration()
    mark_busy(progress_bar)
    _latest_metrics_payload = None

    class QueryWorker(QRunnable):
        function run():
            try:
                result = orchestrator.run_query(current_query, config)
                QTimer.singleShot(0, lambda: display_results(result))
            except Exception as exc:
                QTimer.singleShot(0, lambda: display_error(exc))

    worker = QueryWorker()
    QThreadPool.globalInstance().start(worker)

function AutoresearchMainWindow.display_results(result):
    mark_idle(progress_bar)
    if results_display:
        results_display.display_results(result)
    update_export_options(result)
    if session_manager:
        session_manager.add_session(uuid4(), title_from(current_query))
    _latest_metrics_payload = getattr(result, "metrics", None)
    _refresh_status_metrics()

function handle_startup_error(window, exc):
    if window._suppress_dialogs():
        window._log_dialog("critical", "Startup Error", str(exc))
    else:
        QMessageBox.critical(
            window,
            "Autoresearch - Startup Error",
            render_startup_failure(exc)
        )

function AutoresearchMainWindow._start_metrics_timer():
    if metrics_timer exists:
        return
    metrics_timer = QTimer(interval=2000)
    metrics_timer.timeout.connect(_refresh_status_metrics)
    metrics_timer.start()

function AutoresearchMainWindow.display_error(exc):
    mark_idle(progress_bar)
    if _suppress_dialogs():
        _log_dialog("critical", "Query Error", detail(exc))
    else:
        QMessageBox.critical(self, "Query Error", detail(exc))
    _set_status_message("Query failed")
    _refresh_status_metrics()

function AutoresearchMainWindow.closeEvent(event):
    if is_query_running and _ask_question(confirm_close()) == QMessageBox.No:
        event.ignore()
        return
    if metrics_timer:
        metrics_timer.stop()
    event.accept()
```

## 14a. Desktop Optional Modules (ui/desktop/results_display.py)
```
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None

class ResultsDisplay(QWidget):
    function __init__():
        self._web_engine_available = QWebEngineView is not None
        self.answer_notice = None
        if self._web_engine_available:
            self.answer_view = QWebEngineView()
        else:
            self.answer_notice = QLabel(
                "Qt WebEngine missing. Falling back to a simplified view."
            )
            self.answer_notice.setWordWrap(True)
            self.answer_view = QTextBrowser()
            self.answer_view.setOpenExternalLinks(True)
        answer_layout = QVBoxLayout()
        if self.answer_notice:
            answer_layout.addWidget(self.answer_notice)
        answer_layout.addWidget(self.answer_view)

    function display_answer(result):
        if OutputFormatter:
            body = OutputFormatter.render(result, "markdown", depth="standard")
        else:
            body = markdown_to_html(result.answer)
        html = wrap_html_template(render_markdown(body))
        if hasattr(self.answer_view, "setHtml"):
            self.answer_view.setHtml(html)
        else:
            self.answer_view.setText(html)

try:
    import networkx as nx
except Exception:
    nx = None

class KnowledgeGraphView(QWidget):
    function __init__():
        self._layout_mode = "circular"
        self._message = QLabel("Graph data will appear here when available.")
        if nx is None:
            disable_layout_actions(["spring", "spectral"])

    function _compute_layout_positions(nodes, edges):
        if nx and self._layout_mode != "circular":
            return nx.layout(self._layout_mode, nodes, edges)
        return circular_layout(nodes)

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
except ImportError:
    FigureCanvasQTAgg = None
    Figure = None

class MetricsDashboard(QWidget):
    function __init__():
        self._chart_available = bool(FigureCanvasQTAgg and Figure)
        self._summary_label = QLabel("Metrics not available yet.")
        self._stack = QStackedWidget()
        if self._chart_available:
            self._canvas = FigureCanvasQTAgg(Figure(figsize=(6.0, 3.5)))
            self._stack.addWidget(self._canvas)
            self._stack.addWidget(self._summary_label)
        else:
            self._stack.addWidget(self._summary_label)
            disable_toggle_button(
                text="Charts unavailable",
                description="Install matplotlib to enable plotting."
            )

    function update_metrics(metrics):
        snapshot = extract_snapshot(metrics)
        if not self._chart_available:
            self._summary_label.setText(render_text_summary(snapshot))
            return
        append_snapshot_to_chart(snapshot)
        redraw_chart()
        self._summary_label.setText(render_text_summary(snapshot))
```
