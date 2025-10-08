# AI-Assisted Development Patterns for Autoresearch

This guide provides specific patterns and prompts for effective AI-assisted development using Cursor in the Autoresearch project.

## Table of Contents
- [Reasoning Frameworks](#reasoning-frameworks)
- [Code Generation Patterns](#code-generation-patterns)
- [Testing Patterns](#testing-patterns)
- [Debugging Patterns](#debugging-patterns)
- [Architecture Patterns](#architecture-patterns)
- [Documentation Patterns](#documentation-patterns)

## Reasoning Frameworks

### Dialectical Reasoning Pattern

Use this for making design decisions:

**Prompt Template:**
```
I need to decide how to implement [feature].

Thesis (Initial approach):
[Describe your initial idea]

Please help me with dialectical reasoning:
1. Antithesis - Challenge this approach:
   - What could go wrong?
   - What assumptions am I making?
   - What are the weaknesses?

2. Synthesis - Suggest an improved approach that addresses the concerns

3. Trade-offs - Explain the trade-offs in the synthesized approach
```

**Example:**
```
I need to decide how to implement caching for search results.

Thesis: Use an in-memory LRU cache with unlimited size.

Please help me with dialectical reasoning:
1. Antithesis - What could go wrong with unlimited caching?
2. Synthesis - What's a better caching strategy?
3. Trade-offs - What are we giving up and gaining?
```

### Socratic Questioning Pattern

Use this for exploring problems deeply:

**Prompt Template:**
```
I'm working on [problem/feature].

Please use Socratic questioning to help me think through this:
1. What problem am I really trying to solve?
2. What assumptions am I making?
3. What edge cases should I consider?
4. How will this scale?
5. What are the maintenance implications?
6. How can this fail?
7. What alternatives exist?
8. What are the second-order effects?

Context:
[Provide relevant context]
```

### Systems Thinking Pattern

Use this for understanding component interactions:

**Prompt Template:**
```
I'm modifying [component] to [change].

Please help me think systemically:
1. Direct effects: What does this change directly?
2. Interactions: How will this affect other components?
3. Feedback loops: What cycles or dependencies are created?
4. Emergent behavior: What patterns might emerge at scale?
5. Constraints: What system limits will this hit?
6. Cascading effects: What downstream changes are needed?

Current architecture:
[Describe relevant architecture]
```

## Code Generation Patterns

### Pattern 1: Generate with Full Context

**Prompt Template:**
```
Generate [functionality] for the Autoresearch project.

Project Context:
- Location: src/autoresearch/[module]/
- Uses: uv for packages, Python 3.12+
- Architecture: [relevant pattern from 03-architecture.mdc]

Requirements:
- [requirement 1]
- [requirement 2]
- Must include type hints (use Protocol for interfaces)
- Include comprehensive docstrings (Google style)
- Handle errors appropriately
- Add logging for important operations

Related Code:
[Paste related code or describe interfaces]

Constraints:
- [any constraints]
```

### Pattern 2: Generate with Tests First

**Prompt Template:**
```
I need to implement [feature]. Let's use TDD.

Step 1: Generate comprehensive test cases

Requirements:
- [requirement 1]
- [requirement 2]

Please generate:
1. Happy path tests
2. Edge case tests
3. Error condition tests
4. Use appropriate pytest markers (unit/integration)
5. Follow AAA pattern (Arrange-Act-Assert)
6. Use descriptive test names

After tests, we'll implement the feature to make them pass.
```

### Pattern 3: Refactor Existing Code

**Prompt Template:**
```
Refactor this code to [improvement goal].

Current Code:
[paste code]

Requirements:
- Maintain backward compatibility
- Improve [specific aspect]
- Follow patterns in 03-architecture.mdc
- Keep tests passing

Please:
1. Identify code smells
2. Propose refactoring strategy
3. Show incremental steps
4. Highlight any risks
5. Suggest additional tests if needed
```

## Testing Patterns

### Pattern 1: Generate Comprehensive Test Suite

**Prompt Template:**
```
Generate a comprehensive test suite for this code:

[paste code]

Test Requirements:
- Unit tests for each public method
- Test markers: @pytest.mark.unit (or appropriate marker)
- AAA pattern (Arrange-Act-Assert)
- Descriptive names: test_<method>_<scenario>_<expected>

Test Coverage:
1. Happy path with typical inputs
2. Boundary conditions
3. Edge cases:
   - Empty inputs
   - None values
   - Maximum values
   - Invalid types
4. Error conditions:
   - Invalid inputs (should raise ValueError)
   - Missing dependencies
   - State errors
5. Integration points (if applicable)

Use fixtures from tests/conftest.py where appropriate.
```

### Pattern 2: Generate BDD Scenarios

**Prompt Template:**
```
Create BDD feature file for [feature] from user perspective.

User Story:
As a [role]
I want to [action]
So that [benefit]

Please generate:
1. Gherkin feature file with scenarios
2. Python step definitions
3. Test data fixtures

Format:
- Feature file: tests/behavior/features/[feature].feature
- Steps: tests/behavior/steps/test_[feature].py
- Follow Given-When-Then structure
```

### Pattern 3: Generate Benchmark Tests

**Prompt Template:**
```
Create benchmark tests for [functionality].

Performance Requirements:
- [requirement 1, e.g., "Search should complete in < 100ms for 1000 docs"]
- [requirement 2]

Please generate:
- Benchmark test using pytest-benchmark
- Mark with @pytest.mark.benchmark
- Test different data sizes (small, medium, large)
- Include assertions for acceptable performance
- Group related benchmarks

Reference 08-performance.mdc for patterns.
```

## Debugging Patterns

### Pattern 1: Diagnose Error

**Prompt Template:**
```
I'm encountering this error:

Error Message:
[paste error message]

Stack Trace:
[paste stack trace]

Context:
- What I was trying to do: [description]
- Recent changes: [if any]
- Environment: Python 3.12, [other relevant info]

Please help me:
1. Identify the root cause
2. Explain why this is happening
3. Suggest a fix
4. Recommend tests to prevent this
5. Check for similar issues elsewhere in the code
```

### Pattern 2: Performance Investigation

**Prompt Template:**
```
This code is slower than expected:

[paste code]

Performance:
- Current: [current performance]
- Expected: [expected performance]
- Profiling shows: [profiling results if available]

Please:
1. Identify bottlenecks
2. Suggest algorithmic improvements
3. Recommend optimization strategies from 08-performance.mdc
4. Show before/after performance estimates
5. Highlight any trade-offs
```

### Pattern 3: Memory Leak Investigation

**Prompt Template:**
```
I suspect a memory leak in this code:

[paste code]

Symptoms:
- [describe memory growth pattern]
- [when it occurs]

Please check for:
1. Circular references
2. Unclosed resources
3. Growing caches without bounds
4. Event listeners not cleaned up
5. Global state accumulation

Suggest fixes and monitoring approaches.
```

## Architecture Patterns

### Pattern 1: Design New Component

**Prompt Template:**
```
Design a new [component] for Autoresearch.

Requirements:
- [requirement 1]
- [requirement 2]

Constraints:
- Must integrate with [existing components]
- Should follow [architectural pattern]
- Must be testable and maintainable

Please provide:
1. High-level architecture
2. Interface definitions (using Protocol)
3. Key classes and their responsibilities
4. Component interactions (how it fits with existing code)
5. Error handling strategy
6. Configuration needs
7. Testing strategy

Reference 03-architecture.mdc for project patterns.
```

### Pattern 2: Evaluate Architecture Decision

**Prompt Template:**
```
Evaluate this architecture decision:

Decision: [describe the decision]

Context:
- Current architecture: [relevant parts]
- Requirements: [what needs to be achieved]
- Constraints: [limitations]

Please evaluate using:
1. Pros and cons
2. Impact on other components
3. Scalability implications
4. Maintenance burden
5. Testability
6. Alternative approaches
7. Recommendation

Apply systems thinking to consider broader impacts.
```

### Pattern 3: Implement Design Pattern

**Prompt Template:**
```
Implement the [pattern name] pattern for [use case].

Context:
- Purpose: [why we need this pattern]
- Components involved: [list components]
- Integration points: [how it connects]

Please:
1. Explain how the pattern applies
2. Implement with Python best practices
3. Use type hints and Protocols
4. Include example usage
5. Show testing approach
6. Document trade-offs

Follow patterns in 03-architecture.mdc.
```

## Documentation Patterns

### Pattern 1: Generate API Documentation

**Prompt Template:**
```
Generate comprehensive documentation for this API:

[paste code]

Please include:
1. Module-level docstring with overview
2. Class docstrings with purpose and usage
3. Method docstrings with:
   - Brief description
   - Args with types and descriptions
   - Returns with type and description
   - Raises with exception types and conditions
   - Example usage
   - Notes for complex behavior

Follow Google-style docstrings per 04-documentation.mdc.
```

### Pattern 2: Generate User Guide Section

**Prompt Template:**
```
Create a user guide section for [feature].

Audience: [describe target users]

Please include:
1. Overview (what it does, why it's useful)
2. Prerequisites
3. Installation/setup steps
4. Basic usage with example
5. Advanced usage scenarios
6. Configuration options
7. Common pitfalls and troubleshooting
8. Related features/documentation

Format as markdown suitable for docs/ directory.
```

### Pattern 3: Generate Architecture Documentation

**Prompt Template:**
```
Document the architecture of [component/system].

Include:
1. Purpose and responsibilities
2. High-level design overview
3. Component diagram (describe it, I'll create visual)
4. Key interfaces and protocols
5. Data flow
6. Error handling approach
7. Configuration and dependencies
8. Design decisions and rationale
9. Trade-offs made
10. Future extensibility considerations

Audience: Developers working on or integrating with this component.
```

## Complex Task Patterns

### Pattern 1: Multi-Step Feature Implementation

**Prompt Template:**
```
I need to implement [complex feature] in multiple steps.

Requirements:
- [list all requirements]

Please help me:
1. Break this into incremental, testable steps
2. For each step, identify:
   - What to implement
   - What tests to write
   - Dependencies on previous steps
   - Risks and mitigations
3. Suggest order of implementation
4. Identify integration points
5. Recommend testing strategy

Let's implement step-by-step, validating each before moving forward.
```

### Pattern 2: Gradual Migration

**Prompt Template:**
```
Plan migration from [old approach] to [new approach].

Context:
- Current state: [description]
- Target state: [description]
- Constraints: [must maintain compatibility, zero downtime, etc.]

Please:
1. Design migration strategy with phases
2. For each phase:
   - What changes
   - How to maintain compatibility
   - Rollback plan
   - Testing approach
3. Identify risks
4. Suggest monitoring and validation
5. Provide incremental steps

Goal: Safe, gradual migration with no breaking changes.
```

### Pattern 3: Cross-Cutting Concern

**Prompt Template:**
```
Implement [cross-cutting concern] across the codebase.

Concern: [e.g., logging, caching, monitoring, error handling]

Scope:
- Affects: [list components]
- Requirements: [what needs to be achieved]

Please:
1. Design consistent approach
2. Identify all touch points
3. Suggest implementation strategy
4. Show example for one component
5. List all components needing changes
6. Recommend testing approach
7. Consider impact on existing functionality

Ensure consistency and maintainability.
```

## Review and Validation Patterns

### Pattern 1: Self-Review Checklist

**Prompt Template:**
```
Review this code against project standards:

[paste code]

Check for:
1. Style compliance (PEP 8, 100 char lines, black formatted)
2. Type hints completeness
3. Docstring quality (Google style)
4. Error handling appropriateness
5. Security concerns (09-security.mdc)
6. Performance considerations (08-performance.mdc)
7. Test coverage adequacy
8. Architecture alignment (03-architecture.mdc)
9. Documentation needs
10. Potential bugs or edge cases

Provide specific feedback for each area.
```

### Pattern 2: Pre-Commit Review

**Prompt Template:**
```
I'm about to commit these changes. Please review:

Changed Files:
[list files]

Changes Summary:
[describe changes]

Please verify:
1. All project rules followed
2. Tests written and passing
3. Documentation updated if needed
4. No security issues introduced
5. No performance regressions likely
6. Backward compatibility maintained
7. Error handling appropriate
8. Logging added for important operations
9. Type hints complete
10. Commit message follows convention

Suggest improvements before committing.
```

## Tips for Effective AI Collaboration

### Provide Context Efficiently

**Good Context:**
```
Working on: src/autoresearch/search/engine.py
Related to: storage backend, query processor
Constraint: Must work with DuckDB VSS
Following: 03-architecture.mdc patterns
```

**Poor Context:**
```
Fix the search thing
```

### Iterate and Refine

1. Start with high-level design
2. Review and refine
3. Generate detailed implementation
4. Review for correctness
5. Generate tests
6. Iterate on feedback

### Validate AI Output

Always verify:
- Code runs correctly
- Tests pass
- Follows project rules
- Makes logical sense
- Handles errors properly
- Is maintainable

### Learn and Adapt

After each task:
- What worked well?
- What could improve?
- Update prompts
- Refine patterns
- Share learnings

## See Also

- `.cursor/rules/07-ai-assistance.mdc` - AI assistance guidelines
- `.cursor/workflows/README.md` - Detailed workflows
- `.cursor/workflows/quick-reference.md` - Quick command reference
- `AGENTS.md` - Project guidelines
- `CONTRIBUTING.md` - Contribution practices

