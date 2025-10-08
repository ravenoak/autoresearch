# Cursor Rules for Autoresearch

This directory contains rules for Cursor AI to assist with development of the Autoresearch project.

## Rule Files

### Core Rules (Always Applied)
- `00-project-overview.mdc` - Project overview, philosophy, and key commands
- `05-git-workflow.mdc` - Git workflow and commit practices
- `07-ai-assistance.mdc` - Guidelines for AI-assisted development
- `09-security.mdc` - Security best practices

### Contextual Rules (Applied by File Pattern)
- `01-python-style.mdc` - Python coding style and conventions (`**/*.py`)
- `02-testing.mdc` - Testing guidelines (`tests/**/*.py`, `**/*test*.py`)
- `03-architecture.mdc` - Architecture patterns (`src/**/*.py`)
- `04-documentation.mdc` - Documentation standards (`docs/**/*.md`, `**/*.md`, `src/**/*.py`)
- `06-dependencies.mdc` - Dependency management (`pyproject.toml`, `uv.lock`)
- `08-performance.mdc` - Performance optimization (`src/**/*.py`, benchmark/performance tests)

## Rule Format

Each rule file uses the `.mdc` (Markdown with Cursor) format with frontmatter:

```markdown
---
description: Brief description of the rule
globs:
  - "**/*.py"  # File patterns this rule applies to
alwaysApply: false  # true for project-wide rules
---

# Rule Content

Detailed guidelines and examples...
```

## Using These Rules

### In Cursor IDE
Rules are automatically loaded by Cursor when working on this project. The AI assistant will apply:
- All rules with `alwaysApply: true` to all conversations
- Contextual rules based on the files you're working with

### Updating Rules
When you discover new patterns or best practices:
1. Update the relevant rule file
2. Keep rules focused and actionable
3. Include concrete examples
4. Commit with explanation of what changed and why

### Creating New Rules
If you need a new rule:
1. Create a new `.mdc` file with appropriate numbering
2. Add frontmatter with description and glob patterns
3. Write clear, specific guidelines
4. Include examples
5. Update this README
6. Set `alwaysApply: true` only for universal rules

## Rule Philosophy

These rules follow the project's core principles:
- **Clarity**: Rules should be clear and unambiguous
- **Actionability**: Provide specific guidance, not vague suggestions
- **Reasoning**: Explain the "why" behind guidelines
- **Examples**: Show concrete examples of good and bad practices
- **Focus**: Each rule file covers one coherent topic

## Scope and Organization

Rules are organized from general to specific:
- **00-0X**: Project-wide concerns (overview, git, AI, security)
- **01-0X**: Language and tooling (Python, testing, dependencies)
- **03-0X**: Architecture and design patterns
- **04-0X**: Documentation and communication
- **08-0X**: Cross-cutting concerns (performance, security)

## Advanced Features

### Nested Rules
You can create `.cursor/rules` directories in subdirectories for scoped rules:
```
src/
  autoresearch/
    agents/
      .cursor/rules/
        agent-patterns.mdc  # Only applies to agent code
```

### Reference Files
Rules can reference example files using `@filename.py` syntax to provide additional context.

### Rule Composition
Keep individual rules focused (< 500 lines). Create multiple composable rules rather than one large file.

## Continuous Improvement

These rules should evolve with the project:
- Update when new patterns emerge
- Refine based on code review feedback
- Add examples from real project code
- Remove outdated guidance
- Keep aligned with AGENTS.md files

See `07-ai-assistance.mdc` for guidelines on using these rules effectively with Cursor AI.

