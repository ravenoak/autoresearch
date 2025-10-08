# Quick Reference for Cursor AI Workflows

## Common Commands

### Development
```bash
# Setup and install
task install                    # Initialize environment

# Quick checks (run often)
task check                      # Fast linting, type checks, tests

# Full verification (before commit)
task verify                     # Full test suite with coverage

# Clean up
task clean                      # Remove build artifacts
```

### Package Management
```bash
# Add dependencies
uv add package-name            # Production dependency
uv add --dev package-name      # Development dependency
uv add --optional gpu package  # Optional dependency

# Update dependencies
uv lock --upgrade              # Update all dependencies

# Run commands
uv run python script.py        # Run Python script
uv run pytest                  # Run tests
```

### Testing
```bash
# Run all tests
pytest

# Run by marker
pytest -m unit                 # Unit tests only
pytest -m integration          # Integration tests
pytest -m "not slow"           # Skip slow tests
pytest -m benchmark            # Benchmarks

# With coverage
pytest --cov=autoresearch --cov-report=html

# Specific file or test
pytest tests/unit/test_search.py
pytest tests/unit/test_search.py::test_specific_function
```

### Git Workflow
```bash
# Create branch
git checkout -b feature/name   # New feature
git checkout -b fix/name       # Bug fix
git checkout -b docs/name      # Documentation

# Commit with conventional commits
git commit -m "feat(scope): description"
git commit -m "fix(scope): description"
git commit -m "docs(scope): description"

# Before pushing
task verify                    # Ensure tests pass
```

### Documentation
```bash
# Build and serve docs locally
mkdocs serve                   # View at http://localhost:8000

# Build for production
mkdocs build
```

## AI Prompting Patterns

### Effective Prompts

#### Feature Implementation
```
I need to implement [feature] for [component].

Context:
- Current implementation in [file]
- Related functionality in [other file]
- Must follow [architectural pattern]

Requirements:
- [requirement 1]
- [requirement 2]
- Must include type hints and docstrings
- Follow 03-architecture.mdc rules

Please:
1. Suggest the design approach
2. Generate test cases first
3. Implement the feature
4. Ensure full test coverage
```

#### Bug Investigation
```
I'm investigating a bug where [description].

Symptoms:
- [symptom 1]
- [symptom 2]

Stack trace:
[paste stack trace]

Expected behavior:
[description]

Please help me:
1. Identify the root cause
2. Suggest test cases to reproduce
3. Propose a fix
4. Consider edge cases
```

#### Code Review
```
Please review this code for:
- Compliance with project rules (especially [specific rule])
- Potential bugs or edge cases
- Performance implications
- Security concerns
- Test coverage gaps

[paste code]
```

#### Refactoring
```
I want to refactor [component] to [goal].

Current code:
[paste code]

Constraints:
- Must maintain backward compatibility
- Performance should not degrade
- Tests must pass

Please:
1. Identify code smells
2. Suggest refactoring strategy
3. Show incremental steps
4. Highlight potential risks
```

#### Test Generation
```
Generate comprehensive tests for [function/class].

Code to test:
[paste code]

Please include:
- Happy path tests
- Edge cases
- Error conditions
- Use pytest markers appropriately
- Follow 02-testing.mdc guidelines
```

### Context Provision Tips

Always include relevant context:
- **File location**: "This is in `src/autoresearch/search/engine.py`"
- **Related files**: "This interacts with `storage/backend.py`"
- **Error messages**: Include full stack traces
- **Constraints**: "Must work with Python 3.12+, DuckDB backend"
- **Project rules**: Reference specific rule files when relevant

## Common Patterns

### Creating a New Feature

1. **Start with tests**
   ```python
   @pytest.mark.unit
   def test_new_feature():
       # Arrange
       input_data = ...
       
       # Act
       result = new_feature(input_data)
       
       # Assert
       assert result == expected
   ```

2. **Implement with types**
   ```python
   def new_feature(input_data: InputType) -> OutputType:
       """Brief description.
       
       Args:
           input_data: Description
           
       Returns:
           Description
           
       Raises:
           ValueError: When input is invalid
       """
       pass
   ```

3. **Add error handling**
   ```python
   if not validate(input_data):
       raise ValueError("Invalid input")
   
   try:
       result = process(input_data)
   except ProcessError as e:
       logger.error("Processing failed", exc_info=True)
       raise
   ```

4. **Document usage**
   - Add docstring example
   - Update relevant docs in `docs/`
   - Add to `examples/` if applicable

### Fixing a Bug

1. **Write regression test**
   ```python
   def test_bug_description():
       """Test for issue #123: Bug description."""
       # Create conditions that trigger bug
       result = buggy_function(edge_case_input)
       # Assert correct behavior
       assert result == expected
   ```

2. **Fix minimally**
   - Change only what's necessary
   - Preserve existing behavior
   - Add validation if missing

3. **Verify**
   ```bash
   # Test passes now
   pytest tests/unit/test_module.py::test_bug_description
   
   # No regressions
   task verify
   ```

### Adding Documentation

1. **Code documentation**
   ```python
   """Module description.
   
   This module provides [functionality].
   
   Example:
       >>> from autoresearch import feature
       >>> result = feature.process("input")
   """
   ```

2. **User documentation** (in `docs/`)
   ```markdown
   # Feature Name
   
   Brief overview.
   
   ## Installation
   
   [installation steps]
   
   ## Usage
   
   [usage examples]
   
   ## API Reference
   
   Link to API docs
   ```

## Debugging Checklist

When something doesn't work:

- [ ] Did you run `task install` recently?
- [ ] Are you using the right Python version? (3.12+)
- [ ] Is the virtual environment activated?
- [ ] Did you update dependencies after pulling? (`uv sync`)
- [ ] Are there any linter errors? (`task check`)
- [ ] Do tests pass? (`task verify`)
- [ ] Are there relevant logs? (check `baseline/logs/`)
- [ ] Is the error in a dependency? (check `uv.lock`)

## Getting Unstuck

### If Tests Fail
1. Read the error message carefully
2. Run the specific failing test: `pytest path/to/test.py::test_name -v`
3. Add print statements or use debugger
4. Check recent changes: `git diff`
5. Ask AI for help with the specific error

### If Type Checking Fails
1. Read mypy error message
2. Check type hints in function signature
3. Look for `Any` types that should be specific
4. Check for missing imports from `typing`
5. Run `mypy src/ --show-error-codes` for details

### If Code is Slow
1. Profile first: `python -m cProfile script.py`
2. Check for N+1 queries or loops
3. Look for unnecessary copying of large data
4. Consider caching or async
5. See `08-performance.mdc` for optimization patterns

### If Confused About Architecture
1. Check `docs/architecture/` for system design
2. Review `03-architecture.mdc` for patterns
3. Look at similar existing code
4. Draw a diagram of data flow
5. Ask AI to explain component interactions

## Best Practices Reminders

✅ **Do**
- Run `task check` frequently
- Write tests first
- Use type hints
- Add docstrings
- Commit often
- Read error messages carefully
- Ask for help when stuck

❌ **Don't**
- Commit without running `task verify`
- Skip type hints
- Leave TODO comments without tickets
- Commit commented-out code
- Ignore linter warnings
- Push broken code
- Commit secrets or credentials

## Resources

- `.cursor/rules/` - Complete rule set
- `.cursor/workflows/README.md` - Detailed workflow guides
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/development.md` - Development setup and practices
- `docs/testing_guidelines.md` - Testing best practices
- `AGENTS.md` - Project-wide guidelines

