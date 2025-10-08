# Cursor AI Workflows for Autoresearch

This directory contains workflow documentation and AI-assisted development patterns for the Autoresearch project. While Cursor doesn't have built-in "workflow files" like GitHub Actions, these documents provide structured approaches for common development tasks.

## Available Workflows

### Development Workflows

#### 1. Feature Development Workflow
**When to use**: Adding a new feature to the project

**Steps**:
1. **Planning Phase**
   - Review requirements and acceptance criteria
   - Check existing architecture in `docs/architecture/`
   - Identify affected components
   - Consider system-wide impacts (systems thinking)

2. **Design Phase**
   - Apply dialectical reasoning:
     * Thesis: Propose initial design
     * Antithesis: Challenge assumptions, identify risks
     * Synthesis: Refine design incorporating insights
   - Document design decisions
   - Review with relevant spec files in `docs/specs/`

3. **Implementation Phase**
   ```bash
   # Create feature branch
   git checkout -b feature/descriptive-name
   
   # Set up development environment
   task install
   
   # Run quick check frequently during development
   task check
   ```
   
   - Write tests first (TDD approach)
   - Implement feature following architecture rules
   - Add type hints throughout
   - Document code with docstrings
   - Keep commits atomic and well-described

4. **Validation Phase**
   ```bash
   # Run full test suite with coverage
   task verify
   
   # Check for any missed linting issues
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

5. **Documentation Phase**
   - Update relevant documentation in `docs/`
   - Add usage examples to `examples/`
   - Update CHANGELOG.md
   - Ensure API reference is complete

6. **Review Phase**
   - Self-review the diff
   - Check against all rule files
   - Create PR with comprehensive description
   - Address review feedback

**AI Assistance Tips**:
- Ask AI to generate test cases first
- Use AI for boilerplate code generation
- Verify AI suggestions against project rules
- Have AI review your code for rule compliance

---

#### 2. Bug Fix Workflow
**When to use**: Fixing a reported bug

**Steps**:
1. **Reproduction Phase**
   - Create a minimal test case that reproduces the bug
   - Add test to prevent regression
   - Document expected vs actual behavior

2. **Investigation Phase**
   - Use Socratic questioning:
     * What assumptions led to this bug?
     * What edge cases weren't considered?
     * How did this pass testing?
   - Check related code for similar issues

3. **Fix Phase**
   ```bash
   git checkout -b fix/issue-number-brief-description
   ```
   - Implement minimal fix
   - Ensure new test passes
   - Verify no regressions: `task verify`

4. **Documentation Phase**
   - Update docstrings if behavior changed
   - Add to CHANGELOG.md
   - Consider updating docs/faq.md

5. **Commit Phase**
   ```bash
   git commit -m "fix(component): brief description
   
   Detailed explanation of the bug, root cause,
   and how the fix addresses it.
   
   Fixes #issue-number"
   ```

**AI Assistance Tips**:
- Use AI to analyze stack traces
- Ask AI to suggest test cases for edge cases
- Have AI review fix for potential side effects

---

#### 3. Refactoring Workflow
**When to use**: Improving code structure without changing behavior

**Steps**:
1. **Preparation Phase**
   - Ensure all tests pass: `task verify`
   - Document current behavior
   - Identify refactoring goals and constraints

2. **Planning Phase**
   - Apply holistic thinking:
     * How does this affect other components?
     * What are the maintenance implications?
     * Are there cascading changes needed?
   - Plan incremental steps
   - Consider creating a refactoring spec

3. **Execution Phase**
   ```bash
   git checkout -b refactor/descriptive-name
   ```
   - Make small, incremental changes
   - Run `task check` after each change
   - Commit frequently with clear messages
   - Ensure tests pass continuously

4. **Verification Phase**
   ```bash
   # Full test suite
   task verify
   
   # Performance benchmarks (if relevant)
   pytest -m benchmark
   ```

5. **Documentation Phase**
   - Update architecture docs if structure changed
   - Add migration notes if API changed
   - Update CHANGELOG.md

**AI Assistance Tips**:
- Ask AI to identify code smells
- Use AI to suggest refactoring patterns
- Have AI check for missed updates

---

#### 4. Documentation Workflow
**When to use**: Adding or updating documentation

**Steps**:
1. **Audit Phase**
   - Identify documentation gaps
   - Check for outdated information
   - Review user feedback and questions

2. **Writing Phase**
   ```bash
   git checkout -b docs/topic-name
   ```
   - Follow documentation guidelines in `04-documentation.mdc`
   - Use clear, concise language
   - Include code examples
   - Add diagrams for complex concepts

3. **Review Phase**
   - Check all code examples run correctly
   - Verify links work
   - Ensure consistent terminology
   - Review for accessibility

4. **Integration Phase**
   - Update mkdocs.yml if adding new pages
   - Build docs locally: `mkdocs serve`
   - Check rendering and navigation

**AI Assistance Tips**:
- Use AI to generate initial drafts
- Ask AI to create code examples
- Have AI review for clarity and completeness
- Use AI to suggest related topics to link

---

### Testing Workflows

#### 5. Test-Driven Development (TDD) Workflow
**When to use**: Developing new functionality

**Steps**:
1. **Red Phase** - Write failing test
   ```python
   @pytest.mark.unit
   def test_new_feature_with_valid_input_returns_expected_output():
       """Test that new feature works with valid input."""
       # Arrange
       input_data = create_test_input()
       
       # Act
       result = new_feature(input_data)
       
       # Assert
       assert result == expected_output
   ```

2. **Green Phase** - Write minimal code to pass
   - Implement just enough to make test pass
   - Don't worry about perfection yet

3. **Refactor Phase** - Improve code quality
   - Clean up implementation
   - Add type hints
   - Improve naming
   - Ensure tests still pass

4. **Repeat** for next piece of functionality

**AI Assistance Tips**:
- Ask AI to generate test cases for different scenarios
- Use AI to suggest edge cases
- Have AI review test coverage

---

#### 6. Behavior-Driven Development (BDD) Workflow
**When to use**: Defining feature behavior from user perspective

**Steps**:
1. **Feature Definition**
   - Create `.feature` file in `tests/behavior/features/`
   ```gherkin
   Feature: Search functionality
     As a researcher
     I want to search the document corpus
     So that I can find relevant information
   
   Scenario: Search with valid query returns results
     Given a corpus with 100 documents
     When I search for "machine learning"
     Then I should receive 10 results
     And results should be ranked by relevance
   ```

2. **Step Implementation**
   - Implement step definitions in Python
   - Use fixtures for setup and teardown
   - Keep steps reusable

3. **Execution**
   ```bash
   pytest -m behavior
   ```

**AI Assistance Tips**:
- Ask AI to write Gherkin scenarios
- Use AI to generate step definitions
- Have AI suggest test data

---

### Performance Workflows

#### 7. Performance Optimization Workflow
**When to use**: Addressing performance issues

**Steps**:
1. **Measurement Phase**
   - Establish baseline performance
   - Profile the code
   ```bash
   python -m cProfile -o profile.stats script.py
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
   ```

2. **Analysis Phase**
   - Identify bottlenecks
   - Apply Socratic questioning:
     * Is this a real bottleneck or premature optimization?
     * What is the theoretical best performance?
     * What are the trade-offs?

3. **Optimization Phase**
   - Implement optimization
   - Measure improvement
   - Ensure correctness: `task verify`

4. **Benchmarking Phase**
   ```bash
   pytest -m benchmark --benchmark-compare
   ```
   - Compare before/after
   - Document performance gains
   - Add regression tests

**AI Assistance Tips**:
- Use AI to suggest optimization strategies
- Ask AI to identify algorithmic improvements
- Have AI review for correctness after optimization

---

### Security Workflows

#### 8. Security Review Workflow
**When to use**: Before releasing or when handling sensitive code

**Steps**:
1. **Threat Modeling**
   - Identify assets and threats
   - Map attack surfaces
   - Prioritize risks

2. **Code Review**
   - Check against `09-security.mdc` rules
   - Look for common vulnerabilities:
     * SQL injection
     * Command injection
     * Path traversal
     * XSS
     * Insecure secrets handling

3. **Dependency Audit**
   ```bash
   pip-audit
   uv lock --upgrade
   ```

4. **Testing**
   - Run security-focused tests
   - Test error handling
   - Verify input validation

5. **Documentation**
   - Document security considerations
   - Update threat model
   - Note any security-relevant changes

**AI Assistance Tips**:
- Ask AI to identify security vulnerabilities
- Use AI to suggest secure alternatives
- Have AI review error handling

---

## Workflow Selection Guide

### Quick Reference

| Task Type | Recommended Workflow | Estimated Time |
|-----------|---------------------|----------------|
| New feature | Feature Development | Hours to days |
| Bug fix | Bug Fix | Minutes to hours |
| Code improvement | Refactoring | Hours |
| Docs update | Documentation | 30min to 2 hours |
| New functionality | TDD | Hours |
| User stories | BDD | Hours |
| Performance issue | Performance Optimization | Hours to days |
| Security concern | Security Review | Hours |

### Decision Tree

```
Is it adding new functionality?
├─ Yes: Is it user-facing?
│  ├─ Yes: Consider BDD Workflow → Feature Development
│  └─ No: TDD Workflow → Feature Development
└─ No: Is it fixing a bug?
   ├─ Yes: Bug Fix Workflow
   └─ No: Is it improving code quality?
      ├─ Yes: Refactoring Workflow
      └─ No: Is it documentation?
         ├─ Yes: Documentation Workflow
         └─ No: Is it performance-related?
            ├─ Yes: Performance Optimization
            └─ No: Is it security-related?
               └─ Yes: Security Review
```

## Continuous Improvement

These workflows should evolve with the project:
- Update based on lessons learned
- Add new workflows as patterns emerge
- Share successful patterns with the team
- Refine workflows based on feedback

## See Also

- `.cursor/rules/` - All Cursor rules for the project
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/development.md` - Development documentation
- `docs/testing_guidelines.md` - Testing best practices

