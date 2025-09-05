@behavior
Feature: Optional extras availability
  Verify optional extras can be imported.

  @requires_nlp
  Scenario: NLP extra modules are importable
    Given the optional module "spacy" can be imported
    Then the module exposes attribute "__version__"

  @requires_ui
  Scenario: UI extra modules are importable
    Given the optional module "streamlit" can be imported
    Then the module exposes attribute "__version__"

  @requires_vss
  Scenario: VSS extra modules are importable
    Given the optional module "duckdb" can be imported
    Then the module exposes attribute "__version__"

  @requires_git
  Scenario: Git extra modules are importable
    Given the optional module "git" can be imported
    Then the module exposes attribute "Repo"

  @requires_distributed
  Scenario: Distributed extra modules are importable
    Given the optional module "redis" can be imported
    Then the module exposes attribute "Redis"

  @requires_analysis
  Scenario: Analysis extra modules are importable
    Given the optional module "polars" can be imported
    Then the module exposes attribute "__version__"

  @requires_llm
  Scenario: LLM extra modules are importable
    Given the optional module "fastembed" can be imported
    Then the module exposes attribute "__version__"

  @requires_parsers
  Scenario: Parsers extra modules are importable
    Given the optional module "docx" can be imported
    Then the module exposes attribute "Document"

  @requires_gpu
  Scenario: GPU extra modules are importable
    Given the optional module "bertopic" can be imported
    Then the module exposes attribute "__version__"
