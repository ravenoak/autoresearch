# Phase 2: Planner-Coordinator-ReAct Upgrade Design Specification

## Overview

Phase 2 of the Deep Research Enhancement Initiative transforms the planner from a simple decomposition tool into a sophisticated task graph coordinator with ReAct-style reasoning traces. This upgrade enables dependency-aware scheduling, tool affinity routing, and comprehensive observability for complex multi-step research workflows.

## Core Components

### 1. Task Graph Data Structures

#### TaskNode Schema

```python
@dataclass(frozen=True)
class TaskNode:
    """Represents a single research task in the execution graph."""

    id: str  # Unique identifier (e.g., "task_001")
    description: str  # Human-readable task description
    dependencies: frozenset[str]  # Set of task IDs this depends on
    tool_affinity: dict[str, float]  # Tool -> affinity score (0.0-1.0)
    estimated_tokens: int  # Expected token consumption
    priority: int  # Execution priority (higher = more urgent)
    agent_role: str  # Required agent type (e.g., "researcher", "fact_checker")
    exit_criteria: dict[str, Any]  # Success/failure conditions
    metadata: dict[str, Any]  # Additional task-specific data

    def is_ready(self, completed_tasks: set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return self.dependencies.issubset(completed_tasks)

    def can_use_tool(self, tool_name: str, min_affinity: float = 0.3) -> bool:
        """Check if task can use specified tool."""
        return self.tool_affinity.get(tool_name, 0.0) >= min_affinity
```

#### TaskGraph Schema

```python
@dataclass(frozen=True)
class TaskGraph:
    """Complete execution plan with dependency resolution."""

    nodes: dict[str, TaskNode]  # task_id -> TaskNode
    root_tasks: frozenset[str]  # Tasks with no dependencies
    execution_order: list[str]  # Topologically sorted task IDs
    estimated_total_tokens: int  # Sum of all task token estimates
    critical_path: list[str]  # Longest dependency chain

    def get_ready_tasks(self, completed: set[str]) -> list[TaskNode]:
        """Return tasks ready for execution."""
        return [node for node in self.nodes.values()
                if node.is_ready(completed)]

    def get_next_task(self, completed: set[str],
                     available_tools: set[str]) -> TaskNode | None:
        """Select optimal next task for execution."""
        ready = self.get_ready_tasks(completed)
        # Sort by priority, then by tool availability, then by token efficiency
        return max(ready, key=lambda t: (
            t.priority,
            sum(t.tool_affinity.get(tool, 0.0) for tool in available_tools),
            -t.estimated_tokens  # Prefer token-efficient tasks
        ), default=None)
```

### 2. Dependency Resolution Algorithm

#### Topological Sort with Tool Affinity

```python
def resolve_task_dependencies(
    nodes: dict[str, TaskNode],
    available_tools: set[str]
) -> TaskGraph | None:
    """Build execution graph with dependency-aware scheduling."""

    # Kahn's algorithm with tool affinity optimization
    in_degree = {node_id: len(node.dependencies) for node_id, node in nodes.items()}
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    execution_order = []

    while queue:
        # Select task with highest priority + tool affinity
        current = max(
            (nodes[task_id] for task_id in queue),
            key=lambda t: (t.priority, _calculate_tool_score(t, available_tools))
        )

        queue.remove(current.id)
        execution_order.append(current.id)

        # Update dependent tasks
        for dependent_id, dependent_node in nodes.items():
            if current.id in dependent_node.dependencies:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

    if len(execution_order) != len(nodes):
        return None  # Cycle detected

    return TaskGraph(
        nodes=nodes,
        root_tasks=frozenset(task_id for task_id, node in nodes.items()
                           if not node.dependencies),
        execution_order=execution_order,
        estimated_total_tokens=sum(node.estimated_tokens for node in nodes.values()),
        critical_path=_find_critical_path(nodes, execution_order)
    )
```

### 3. ReAct Trace Logging

#### ReActStep Schema

```python
@dataclass
class ReActStep:
    """Individual step in ReAct reasoning process."""

    timestamp: datetime
    task_id: str
    action: str  # "thought", "action", "observation"
    content: str  # Step content
    tool_used: str | None  # Tool name if action step
    tool_input: dict[str, Any] | None  # Tool parameters
    tool_output: dict[str, Any] | None  # Tool results
    confidence_score: float | None  # Confidence in this step (0.0-1.0)
    metadata: dict[str, Any]  # Additional step metadata

    def is_action_step(self) -> bool:
        return self.action == "action"

    def is_observation_step(self) -> bool:
        return self.action == "observation"

    def is_thought_step(self) -> bool:
        return self.action == "thought"
```

#### ReActTrace Schema

```python
@dataclass
class ReActTrace:
    """Complete ReAct reasoning trace for a task."""

    task_id: str
    steps: list[ReActStep]
    final_answer: str | None
    total_tokens_used: int
    execution_time_ms: float
    success: bool
    error_message: str | None

    def get_thought_steps(self) -> list[ReActStep]:
        return [step for step in self.steps if step.is_thought_step()]

    def get_action_steps(self) -> list[ReActStep]:
        return [step for step in self.steps if step.is_action_step()]

    def get_observation_steps(self) -> list[ReActStep]:
        return [step for step in self.steps if step.is_observation_step()]

    def calculate_confidence(self) -> float:
        """Calculate overall confidence from step confidence scores."""
        action_steps = self.get_action_steps()
        if not action_steps:
            return 0.0
        return sum(step.confidence_score or 0.0 for step in action_steps) / len(action_steps)
```

### 4. Tool Affinity Scoring Mechanism

#### AffinityCalculator

```python
class AffinityCalculator:
    """Calculates tool affinity scores for research tasks."""

    def __init__(self, tool_profiles: dict[str, ToolProfile]):
        self.tool_profiles = tool_profiles

    def calculate_affinity(
        self,
        task_description: str,
        context: dict[str, Any]
    ) -> dict[str, float]:
        """Calculate affinity scores for all available tools."""

        # Extract task features (keywords, complexity, data types needed)
        task_features = self._extract_task_features(task_description)

        scores = {}
        for tool_name, profile in self.tool_profiles.items():
            score = self._calculate_tool_score(task_features, profile, context)
            scores[tool_name] = max(0.0, min(1.0, score))  # Clamp to [0,1]

        return scores

    def _extract_task_features(self, description: str) -> TaskFeatures:
        """Extract semantic features from task description."""
        # Use NLP to identify:
        # - Required data types (text, code, images, etc.)
        # - Complexity indicators (research depth, analysis type)
        # - Domain keywords (technical, scientific, business, etc.)
        # - Temporal aspects (current vs historical data)
        pass

    def _calculate_tool_score(
        self,
        features: TaskFeatures,
        profile: ToolProfile,
        context: dict[str, Any]
    ) -> float:
        """Calculate affinity score for specific tool."""
        # Weighted combination of:
        # - Feature compatibility (0.4 weight)
        # - Historical performance (0.3 weight)
        # - Context relevance (0.2 weight)
        # - Cost efficiency (0.1 weight)
        pass
```

#### ToolProfile Schema

```python
@dataclass
class ToolProfile:
    """Profile describing tool capabilities and performance."""

    name: str
    description: str
    supported_data_types: set[str]  # "text", "code", "image", etc.
    domains: set[str]  # "technical", "scientific", "business", etc.
    complexity_support: tuple[int, int]  # (min, max) complexity levels
    historical_accuracy: float  # 0.0-1.0
    average_latency_ms: float
    cost_per_token: float
    reliability_score: float  # 0.0-1.0
    last_updated: datetime
```

### 5. Coordinator Scheduling Logic

#### TaskCoordinator

```python
class TaskCoordinator:
    """Coordinates execution of task graphs with dependency awareness."""

    def __init__(self, task_graph: TaskGraph, available_tools: set[str]):
        self.task_graph = task_graph
        self.available_tools = available_tools
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()
        self.running_tasks: set[str] = set()
        self.react_traces: dict[str, ReActTrace] = {}

    async def execute(self) -> ExecutionResult:
        """Execute complete task graph with ReAct tracing."""

        start_time = time.time()
        execution_log = []

        try:
            while len(self.completed_tasks) < len(self.task_graph.nodes):
                # Find next executable task
                next_task = self.task_graph.get_next_task(
                    self.completed_tasks,
                    self.available_tools
                )

                if not next_task:
                    # Check for deadlocks
                    if self.running_tasks:
                        await self._wait_for_running_tasks()
                        continue
                    break

                # Execute task with ReAct tracing
                trace = await self._execute_task_with_react(next_task)
                self.react_traces[next_task.id] = trace

                if trace.success:
                    self.completed_tasks.add(next_task.id)
                    execution_log.append(f"Task {next_task.id} completed successfully")
                else:
                    self.failed_tasks.add(next_task.id)
                    execution_log.append(f"Task {next_task.id} failed: {trace.error_message}")

                    # Decide whether to continue or abort
                    if not await self._should_continue_on_failure(next_task, trace):
                        break

            return ExecutionResult(
                success=len(self.failed_tasks) == 0,
                completed_tasks=self.completed_tasks,
                failed_tasks=self.failed_tasks,
                execution_time=time.time() - start_time,
                react_traces=self.react_traces,
                execution_log=execution_log
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                completed_tasks=self.completed_tasks,
                failed_tasks=self.failed_tasks | {next_task.id if 'next_task' in locals() else "unknown"},
                execution_time=time.time() - start_time,
                react_traces=self.react_traces,
                execution_log=execution_log + [f"Execution failed: {str(e)}"]
            )
```

#### ExecutionResult Schema

```python
@dataclass
class ExecutionResult:
    """Result of task graph execution."""

    success: bool
    completed_tasks: set[str]
    failed_tasks: set[str]
    execution_time: float
    react_traces: dict[str, ReActTrace]
    execution_log: list[str]

    def get_success_rate(self) -> float:
        """Calculate success rate for completed tasks."""
        total = len(self.completed_tasks) + len(self.failed_tasks)
        return len(self.completed_tasks) / total if total > 0 else 0.0

    def get_average_task_time(self) -> float:
        """Calculate average execution time per task."""
        if not self.react_traces:
            return 0.0
        return sum(trace.execution_time_ms for trace in self.react_traces.values()) / len(self.react_traces)
```

### 6. ReAct Execution Engine

#### ReActExecutor

```python
class ReActExecutor:
    """Executes individual tasks using ReAct reasoning."""

    def __init__(self, tool_registry: ToolRegistry, model_adapter: ModelAdapter):
        self.tool_registry = tool_registry
        self.model_adapter = model_adapter

    async def execute_task(
        self,
        task: TaskNode,
        context: dict[str, Any]
    ) -> ReActTrace:
        """Execute task using ReAct reasoning pattern."""

        steps = []
        start_time = time.time()

        try:
            # Initial thought step
            thought_prompt = self._build_thought_prompt(task, context)
            thought_response = await self.model_adapter.generate(thought_prompt)
            steps.append(ReActStep(
                timestamp=datetime.now(),
                task_id=task.id,
                action="thought",
                content=thought_response,
                confidence_score=None,
                metadata={"prompt": thought_prompt}
            ))

            max_iterations = 10  # Prevent infinite loops
            for iteration in range(max_iterations):
                # Action step
                action_prompt = self._build_action_prompt(task, steps, context)
                action_response = await self.model_adapter.generate(action_prompt)

                # Parse action (e.g., "Action: search_web\nInput: query")
                action, tool_input = self._parse_action(action_response)
                if not action:
                    break

                steps.append(ReActStep(
                    timestamp=datetime.now(),
                    task_id=task.id,
                    action="action",
                    content=action_response,
                    tool_used=action,
                    tool_input=tool_input,
                    confidence_score=None,
                    metadata={"iteration": iteration}
                ))

                # Execute tool
                tool_output = await self.tool_registry.execute_tool(action, tool_input)

                steps.append(ReActStep(
                    timestamp=datetime.now(),
                    task_id=task.id,
                    action="observation",
                    content=str(tool_output),
                    tool_used=action,
                    tool_output=tool_output,
                    confidence_score=self._calculate_confidence(tool_output),
                    metadata={"iteration": iteration}
                ))

                # Check exit criteria
                if self._meets_exit_criteria(task, steps, tool_output):
                    break

            # Generate final answer
            final_prompt = self._build_final_prompt(task, steps)
            final_answer = await self.model_adapter.generate(final_prompt)

            return ReActTrace(
                task_id=task.id,
                steps=steps,
                final_answer=final_answer,
                total_tokens_used=sum(step.metadata.get("tokens", 0) for step in steps),
                execution_time_ms=(time.time() - start_time) * 1000,
                success=True,
                error_message=None
            )

        except Exception as e:
            return ReActTrace(
                task_id=task.id,
                steps=steps,
                final_answer=None,
                total_tokens_used=sum(step.metadata.get("tokens", 0) for step in steps),
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
```

### 7. Persistence and Replay

#### TracePersistence

```python
class TracePersistence:
    """Handles persistence and replay of ReAct traces."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_trace(self, trace: ReActTrace) -> str:
        """Save trace to disk and return identifier."""
        trace_id = f"{trace.task_id}_{int(trace.execution_time_ms)}"
        trace_file = self.storage_path / f"{trace_id}.json"

        trace_data = {
            "trace_id": trace_id,
            "task_id": trace.task_id,
            "timestamp": trace.steps[0].timestamp.isoformat() if trace.steps else None,
            "steps": [
                {
                    "timestamp": step.timestamp.isoformat(),
                    "action": step.action,
                    "content": step.content,
                    "tool_used": step.tool_used,
                    "tool_input": step.tool_input,
                    "tool_output": step.tool_output,
                    "confidence_score": step.confidence_score,
                    "metadata": step.metadata
                }
                for step in trace.steps
            ],
            "final_answer": trace.final_answer,
            "total_tokens_used": trace.total_tokens_used,
            "execution_time_ms": trace.execution_time_ms,
            "success": trace.success,
            "error_message": trace.error_message
        }

        trace_file.write_text(json.dumps(trace_data, indent=2))
        return trace_id

    def load_trace(self, trace_id: str) -> ReActTrace | None:
        """Load trace from disk."""
        trace_file = self.storage_path / f"{trace_id}.json"
        if not trace_file.exists():
            return None

        trace_data = json.loads(trace_file.read_text())

        steps = [
            ReActStep(
                timestamp=datetime.fromisoformat(step_data["timestamp"]),
                task_id=trace_data["task_id"],
                action=step_data["action"],
                content=step_data["content"],
                tool_used=step_data["tool_used"],
                tool_input=step_data["tool_input"],
                tool_output=step_data["tool_output"],
                confidence_score=step_data["confidence_score"],
                metadata=step_data["metadata"]
            )
            for step_data in trace_data["steps"]
        ]

        return ReActTrace(
            task_id=trace_data["task_id"],
            steps=steps,
            final_answer=trace_data["final_answer"],
            total_tokens_used=trace_data["total_tokens_used"],
            execution_time_ms=trace_data["execution_time_ms"],
            success=trace_data["success"],
            error_message=trace_data["error_message"]
        )

    def list_traces(self, task_id: str | None = None) -> list[str]:
        """List available trace IDs, optionally filtered by task."""
        pattern = f"{'*' if task_id is None else task_id}*.json"
        return [f.stem for f in self.storage_path.glob(pattern)]
```

## Implementation Plan

### Phase 2.1: Core Data Structures (Weeks 1-2)

1. **TaskNode and TaskGraph Implementation**
   - Implement core data structures with proper typing
   - Add dependency validation and cycle detection
   - Create serialization/deserialization methods

2. **Basic Dependency Resolution**
   - Implement Kahn's algorithm for topological sorting
   - Add tool affinity-based task prioritization
   - Create basic execution order calculation

### Phase 2.2: ReAct Trace Infrastructure (Weeks 3-4)

1. **ReActStep and ReActTrace Schemas**
   - Implement complete ReAct data structures
   - Add trace persistence and loading
   - Create trace validation and integrity checks

2. **TracePersistence Implementation**
   - Build file-based trace storage system
   - Add trace querying and filtering capabilities
   - Implement trace compression for large executions

### Phase 2.3: Tool Affinity System (Weeks 5-6)

1. **AffinityCalculator Implementation**
   - Build task feature extraction from descriptions
   - Implement tool profile management
   - Create affinity scoring algorithms

2. **Tool Registry Enhancement**
   - Extend tool registry with profile information
   - Add historical performance tracking
   - Implement tool capability discovery

### Phase 2.4: Coordinator Integration (Weeks 7-8)

1. **TaskCoordinator Implementation**
   - Build complete task execution coordinator
   - Add error handling and retry logic
   - Implement execution state management

2. **ReActExecutor Integration**
   - Connect ReAct executor with coordinator
   - Add tool execution integration
   - Implement exit criteria checking

### Phase 2.5: Testing and Validation (Weeks 9-10)

1. **Unit Test Coverage**
   - Test all core data structures
   - Validate dependency resolution algorithms
   - Test ReAct trace generation and persistence

2. **Integration Testing**
   - Test complete task graph execution
   - Validate tool affinity scoring
   - Test error handling and recovery

3. **Performance Testing**
   - Benchmark task graph execution
   - Test scalability with large graphs
   - Validate memory usage patterns

## Success Criteria

### Functional Requirements

1. **Task Graph Execution**
   - Tasks execute in correct dependency order
   - Parallel execution respects dependencies
   - Failed tasks don't block unrelated tasks

2. **ReAct Trace Quality**
   - All steps properly logged with timestamps
   - Tool interactions correctly captured
   - Confidence scores accurately calculated

3. **Tool Affinity Effectiveness**
   - Tasks routed to appropriate tools
   - Affinity scores correlate with task success
   - Historical performance improves routing

4. **Persistence and Replay**
   - Traces persist correctly to disk
   - Traces can be loaded and replayed
   - Large traces handled efficiently

### Performance Requirements

1. **Execution Efficiency**
   - Task graph resolution: <100ms for 100 nodes
   - ReAct execution: <5s per task on average
   - Memory usage: <100MB for 1000-node graphs

2. **Scalability**
   - Support graphs with 1000+ nodes
   - Handle concurrent executions safely
   - Maintain performance under load

### Observability Requirements

1. **Comprehensive Logging**
   - All coordinator decisions logged
   - Performance metrics captured
   - Error conditions properly reported

2. **Debugging Support**
   - Traces provide clear execution history
   - Tool interactions fully observable
   - Performance bottlenecks identifiable

## Migration Strategy

### Backward Compatibility

1. **Gradual Rollout**
   - Phase 2 features disabled by default
   - Configuration flags control new behavior
   - Existing workflows continue unchanged

2. **Feature Flags**
   - `enable_task_graphs`: Enable new task graph system
   - `enable_react_tracing`: Enable ReAct trace logging
   - `enable_tool_affinity`: Enable affinity-based routing

3. **Migration Path**
   - v0.1.0: Current planner behavior (default)
   - v0.2.0: Task graph features available but optional
   - v0.3.0: Task graphs become default execution model

### Risk Mitigation

1. **Incremental Testing**
   - Test each component independently before integration
   - Validate performance at each milestone
   - Monitor for regressions in existing functionality

2. **Rollback Plan**
   - Feature flags allow quick disabling of new features
   - Existing planner continues as fallback
   - Database schema changes are additive only

## Conclusion

Phase 2 transforms Autoresearch from a simple query-response system into a sophisticated research orchestration platform. The task graph approach enables complex multi-step workflows while ReAct tracing provides unprecedented observability into the reasoning process. Tool affinity routing ensures tasks use the most appropriate tools, improving both efficiency and quality.

The implementation maintains backward compatibility while providing a clear upgrade path to the new architecture. Success will be measured by improved task success rates, better resource utilization, and enhanced debugging capabilities for complex research workflows.

