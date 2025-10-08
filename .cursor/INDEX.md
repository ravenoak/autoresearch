# Cursor IDE Configuration Index

Complete index of Cursor IDE configuration for the Autoresearch project.

## Overview

This directory contains comprehensive Cursor IDE configuration to assist with AI-assisted development. The configuration includes:

- **Rules**: Project-specific guidelines and best practices
- **Workflows**: Structured development process documentation
- **Ignore Patterns**: Optimization for Cursor's indexing

## Directory Structure

```
.cursor/
├── INDEX.md                          # This file
├── rules/                            # Rule files for AI guidance
│   ├── README.md                     # Rule system documentation
│   ├── 00-project-overview.mdc       # Project overview and philosophy
│   ├── 01-python-style.mdc           # Python coding standards
│   ├── 02-testing.mdc                # Testing guidelines
│   ├── 03-architecture.mdc           # Architecture patterns
│   ├── 04-documentation.mdc          # Documentation standards
│   ├── 05-git-workflow.mdc           # Git and PR practices
│   ├── 06-dependencies.mdc           # Dependency management
│   ├── 07-ai-assistance.mdc          # AI collaboration guidelines
│   ├── 08-performance.mdc            # Performance optimization
│   └── 09-security.mdc               # Security best practices
└── workflows/                        # Workflow documentation
    ├── README.md                     # Detailed workflow guides
    ├── quick-reference.md            # Quick command reference
    └── ai-patterns.md                # AI prompting patterns

.cursorignore                         # Files to exclude from indexing
```

## Quick Start

### For New Contributors

1. **Read First**:
   - `.cursor/rules/00-project-overview.mdc` - Project context
   - `.cursor/workflows/quick-reference.md` - Essential commands

2. **Setup Environment**:
   ```bash
   task install
   task check
   ```

3. **Before First PR**:
   - Review `.cursor/rules/05-git-workflow.mdc`
   - Read `.cursor/workflows/README.md`

### For Daily Development

**Quick References:**
- Commands: `.cursor/workflows/quick-reference.md`
- AI Prompts: `.cursor/workflows/ai-patterns.md`
- Rules: `.cursor/rules/README.md`

**Common Tasks:**
- Writing code: Check `01-python-style.mdc`
- Writing tests: Check `02-testing.mdc`
- Architecture decisions: Check `03-architecture.mdc`
- Performance work: Check `08-performance.mdc`

## Rule Categories

### Core Rules (Always Applied)

These rules apply to all work in the project:

| Rule | Purpose |
|------|---------|
| `00-project-overview.mdc` | Project context, philosophy, and technology stack |
| `05-git-workflow.mdc` | Version control and collaboration practices |
| `07-ai-assistance.mdc` | Effective AI-assisted development |
| `09-security.mdc` | Security best practices and guidelines |

### Contextual Rules (Applied by File Type)

These rules apply based on what files you're working with:

| Rule | Applies To | Purpose |
|------|-----------|---------|
| `01-python-style.mdc` | `**/*.py` | Python coding style and conventions |
| `02-testing.mdc` | `tests/**/*.py`, `**/*test*.py` | Testing practices and patterns |
| `03-architecture.mdc` | `src/**/*.py` | Architecture patterns and design |
| `04-documentation.mdc` | `docs/**/*.md`, `**/*.md`, `src/**/*.py` | Documentation standards |
| `06-dependencies.mdc` | `pyproject.toml`, `uv.lock` | Dependency management |
| `08-performance.mdc` | `src/**/*.py`, benchmark/performance tests | Performance optimization |

## Workflow Guides

### Development Workflows

| Workflow | When to Use | Guide |
|----------|-------------|-------|
| Feature Development | Adding new functionality | `.cursor/workflows/README.md#1-feature-development-workflow` |
| Bug Fix | Fixing reported bugs | `.cursor/workflows/README.md#2-bug-fix-workflow` |
| Refactoring | Improving code structure | `.cursor/workflows/README.md#3-refactoring-workflow` |
| Documentation | Adding/updating docs | `.cursor/workflows/README.md#4-documentation-workflow` |

### Testing Workflows

| Workflow | When to Use | Guide |
|----------|-------------|-------|
| TDD | Developing with tests first | `.cursor/workflows/README.md#5-test-driven-development-tdd-workflow` |
| BDD | User-focused behavior testing | `.cursor/workflows/README.md#6-behavior-driven-development-bdd-workflow` |

### Specialized Workflows

| Workflow | When to Use | Guide |
|----------|-------------|-------|
| Performance Optimization | Addressing performance issues | `.cursor/workflows/README.md#7-performance-optimization-workflow` |
| Security Review | Security-critical changes | `.cursor/workflows/README.md#8-security-review-workflow` |

## AI Assistance Patterns

### Reasoning Patterns

Located in `.cursor/workflows/ai-patterns.md`:

- **Dialectical Reasoning**: For design decisions (Thesis → Antithesis → Synthesis)
- **Socratic Questioning**: For deep problem exploration
- **Systems Thinking**: For understanding component interactions
- **Holistic Thinking**: For balancing multiple concerns

### Code Generation Patterns

- Generate with full context
- Generate with tests first (TDD)
- Refactor existing code
- Implement design patterns

### Testing Patterns

- Generate comprehensive test suites
- Generate BDD scenarios
- Generate benchmark tests

### Debugging Patterns

- Diagnose errors
- Performance investigation
- Memory leak investigation

See `.cursor/workflows/ai-patterns.md` for complete prompt templates.

## Key Commands Reference

### Essential Commands

```bash
# Setup
task install              # Initialize environment

# Development
task check                # Quick validation (run often)
task verify               # Full validation (before commit)
task clean                # Clean build artifacts

# Testing
pytest                    # Run all tests
pytest -m unit            # Run unit tests only
pytest -m integration     # Run integration tests

# Package Management
uv add package-name       # Add dependency
uv lock --upgrade         # Update dependencies
```

See `.cursor/workflows/quick-reference.md` for comprehensive command reference.

## Best Practices Summary

### Code Quality

✅ **Always**:
- Run `task check` frequently during development
- Run `task verify` before committing
- Write tests for new functionality
- Add type hints to all functions
- Include docstrings for public APIs
- Follow PEP 8 and project style guidelines

❌ **Never**:
- Commit without running tests
- Skip type hints or docstrings
- Ignore linter warnings
- Commit secrets or credentials
- Leave TODO comments without tickets

### AI Collaboration

✅ **Do**:
- Provide full context in prompts
- Verify AI-generated code thoroughly
- Test all AI suggestions
- Apply reasoning frameworks to decisions
- Iterate and refine outputs

❌ **Don't**:
- Blindly accept AI suggestions
- Skip code review for AI output
- Ignore project rules in AI prompts
- Share sensitive information with AI

### Git Workflow

✅ **Do**:
- Use conventional commits
- Write descriptive commit messages
- Keep commits atomic and focused
- Create feature branches
- Review your own diffs before pushing

❌ **Don't**:
- Commit to main directly
- Push broken code
- Use vague commit messages
- Include unrelated changes in commits

## Troubleshooting

### Common Issues

**Tests failing?**
- Check `.cursor/workflows/quick-reference.md#if-tests-fail`

**Type checking errors?**
- See `.cursor/workflows/quick-reference.md#if-type-checking-fails`

**Performance issues?**
- Review `.cursor/rules/08-performance.mdc`
- Check `.cursor/workflows/quick-reference.md#if-code-is-slow`

**Architecture questions?**
- Review `.cursor/rules/03-architecture.mdc`
- See `.cursor/workflows/quick-reference.md#if-confused-about-architecture`

### Getting Help

1. Check relevant rule files in `.cursor/rules/`
2. Review workflow guides in `.cursor/workflows/`
3. Look at existing similar code in the project
4. Use AI assistance with proper context
5. Ask team members for guidance

## Configuration Maintenance

### Updating Rules

When updating rules:
1. Edit the relevant `.mdc` file in `.cursor/rules/`
2. Keep rules focused and actionable
3. Add concrete examples
4. Update related workflow documentation
5. Commit with clear explanation

### Adding New Rules

To add a new rule:
1. Create new `.mdc` file with appropriate numbering
2. Add frontmatter with metadata:
   ```yaml
   ---
   description: Brief description
   globs:
     - "pattern/to/match/*.py"
   alwaysApply: false
   ---
   ```
3. Write clear, specific guidelines with examples
4. Update `.cursor/rules/README.md`
5. Update this index

### Updating Workflows

When updating workflows:
1. Edit files in `.cursor/workflows/`
2. Keep instructions clear and actionable
3. Include relevant examples
4. Update the index if structure changes
5. Share improvements with team

## Philosophy

These Cursor configurations embody the project's core values:

- **Clarity**: Clear, unambiguous guidance
- **Safety**: Security and correctness first
- **Maintainability**: Sustainable, readable code
- **Reasoning**: Dialectical and Socratic thinking
- **Continuous Improvement**: Evolve with the project

## Learning Path

### Week 1: Foundation
1. Read `00-project-overview.mdc`
2. Read `01-python-style.mdc`
3. Read `quick-reference.md`
4. Complete first small task

### Week 2: Testing & Architecture
1. Read `02-testing.mdc`
2. Read `03-architecture.mdc`
3. Review existing code structure
4. Write tests for a feature

### Week 3: Best Practices
1. Read `05-git-workflow.mdc`
2. Read `07-ai-assistance.mdc`
3. Read `09-security.mdc`
4. Review PRs and learn patterns

### Ongoing
- Reference rules as needed
- Use workflow guides for tasks
- Apply AI patterns for efficiency
- Contribute improvements to configurations

## Integration with Project

### Related Documentation

These Cursor configurations complement:

- `AGENTS.md` - Project-wide agent guidelines
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/development.md` - Development setup and practices
- `docs/testing_guidelines.md` - Detailed testing documentation

### Consistency

Rules in `.cursor/rules/` are aligned with:
- Project AGENTS.md files
- Contribution guidelines
- Architecture documentation
- Testing strategies

### Evolution

As the project evolves:
- Rules are updated to reflect new patterns
- Workflows are refined based on experience
- Best practices are continuously improved
- Team feedback shapes the configuration

## Feedback and Improvement

Help improve these configurations:
1. Notice what works well and what doesn't
2. Suggest improvements via PR or discussion
3. Add examples from real project experience
4. Share effective AI prompts and patterns
5. Update outdated guidance

## Version History

- **2025-10-07**: Initial comprehensive Cursor configuration
  - 10 rule files covering all aspects of development
  - 3 workflow guides with detailed processes
  - AI pattern library with prompt templates
  - Complete indexing and documentation

---

**Next Steps**: Read `.cursor/workflows/quick-reference.md` for immediate productivity, then explore rules relevant to your current task.

