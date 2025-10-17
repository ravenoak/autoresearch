# Optional Extras Documentation

## Overview

Autoresearch provides optional extras that enable specific functionality. This document explains what each extra provides and how to use it.

## Available Extras

### Core Extras (Always Available)
- **dev-minimal**: Basic development tools (pytest, flake8, mypy, black)
- **test**: Full test suite (pytest-bdd, hypothesis, coverage tools)

### Optional Extras

#### UI (`ui`)
**Purpose**: Enables Streamlit-based web interface
**Dependencies**: streamlit, pillow, altair, pandas, pyarrow
**Test Coverage**: 25 passed, 3 skipped (1,892 deselected)
**Features**:
- Web-based research interface
- Interactive query builder
- Results visualization
- Configuration management UI

**Usage**:
```bash
uv sync --extra ui
uv run pytest -m requires_ui  # Run UI tests
```

#### Vector Search (`vss`)
**Purpose**: Enables DuckDB vector search extension
**Dependencies**: duckdb-extension-vss
**Test Coverage**: 3 passed, 4 skipped (1,868 deselected)
**Features**:
- Vector similarity search
- Embedding-based search
- VSS extension management

**Usage**:
```bash
uv sync --extra vss
uv run pytest -m requires_vss  # Run VSS tests
```

**Known Issues**:
- `test_extension_path_normalized` fails on macOS (Windows path normalization test)
- Should be skipped on non-Windows platforms

#### NLP (`nlp`)
**Purpose**: Natural language processing features
**Dependencies**: spacy
**Features**:
- Text processing and analysis
- Entity recognition
- Language model integration

#### GPU (`gpu`)
**Purpose**: GPU-accelerated features
**Dependencies**: torch, transformers, bertopic, etc.
**Features**:
- GPU-accelerated embeddings
- Large language model inference
- Topic modeling

#### Distributed (`distributed`)
**Purpose**: Multi-node distributed processing
**Dependencies**: ray, redis
**Features**:
- Distributed agent execution
- Redis-backed coordination
- Multi-worker orchestration

#### Git (`git`)
**Purpose**: Git repository search and analysis
**Dependencies**: GitPython
**Features**:
- Repository indexing
- Commit history search
- Code analysis

#### Analysis (`analysis`)
**Purpose**: Data analysis and visualization
**Dependencies**: polars, matplotlib
**Features**:
- Data frame operations
- Statistical analysis
- Chart generation

#### LLM (`llm`)
**Purpose**: Large language model integrations
**Dependencies**: dspy-ai, fastembed, transformers
**Features**:
- Multiple LLM backends
- Embedding generation
- Model routing and selection

#### Parsers (`parsers`)
**Purpose**: Document parsing and extraction
**Dependencies**: pdfminer-six, python-docx, lxml
**Features**:
- PDF text extraction
- DOCX document parsing
- HTML/XML parsing

#### Build (`build`)
**Purpose**: Package building and publishing
**Dependencies**: build, twine, cibuildwheel
**Features**:
- Python package building
- Cross-platform wheel building
- PyPI publishing

## Test Markers

Each extra has corresponding pytest markers:

| Extra | Marker | Description |
|-------|--------|-------------|
| ui | `requires_ui` | Tests requiring Streamlit UI |
| vss | `requires_vss` | Tests requiring VSS extension |
| nlp | `requires_nlp` | Tests requiring spaCy |
| gpu | `requires_gpu` | Tests requiring GPU libraries |
| distributed | `requires_distributed` | Tests requiring Ray/Redis |
| git | `requires_git` | Tests requiring GitPython |
| analysis | `requires_analysis` | Tests requiring Polars |
| llm | `requires_llm` | Tests requiring LLM libraries |
| parsers | `requires_parsers` | Tests requiring document parsers |
| build | `requires_build` | Tests requiring build tools |

## Usage Guidelines

### Installing Extras
```bash
# Install specific extra
uv sync --extra ui

# Install multiple extras
uv sync --extra ui --extra vss --extra nlp

# Install all extras (for development)
uv sync --extra full
```

### Running Tests
```bash
# Run tests for specific extra
uv run pytest -m requires_ui

# Run tests for multiple extras
uv run pytest -m "requires_ui or requires_vss"

# Skip tests requiring specific extras
uv run pytest -m "not requires_gpu"
```

### Development Workflow
1. Install `dev-minimal` and `test` extras for basic development
2. Add specific extras as needed for features you're working on
3. Use markers to run only relevant tests
4. Document any new extras in this file

## Performance Considerations

- **UI extra**: Adds ~50MB of dependencies, enables web interface
- **GPU extra**: Adds ~2GB of dependencies, requires CUDA-compatible hardware
- **LLM extra**: Adds ~500MB of dependencies for model inference
- **Distributed extra**: Adds Ray/Redis for multi-node processing

## Troubleshooting

### Common Issues

**Missing pytest_bdd for behavior tests**:
```bash
uv sync --extra test
```

**Extension not found errors**:
- Ensure extras are installed before running tests
- Check that optional dependencies are available

**Platform-specific test failures**:
- Some tests may be Windows-specific (e.g., path normalization)
- These should be marked with platform conditionals

## Future Improvements

- [ ] Platform-specific test conditionals for Windows-only tests
- [ ] Better documentation of extra interdependencies
- [ ] Performance benchmarks for different extra combinations
- [ ] Automated testing of all extras in CI

