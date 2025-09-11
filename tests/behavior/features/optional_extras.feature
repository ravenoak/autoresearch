Feature: Optional extras operate when installed
  Optional extras like NLP or UI should expose corresponding functionality.

  @requires_nlp
  Scenario: NLP extra provides spaCy
    When I check nlp extra
    Then the extra is functional

  @requires_ui
  Scenario: UI extra provides Streamlit
    When I check ui extra
    Then the extra is functional

  @requires_vss
  Scenario: VSS extra loads DuckDB extension
    When I check vss extra
    Then the extra is functional

  @requires_git
  Scenario: Git extra enables repository search
    When I check git extra
    Then the extra is functional

  @requires_distributed
  Scenario: Distributed extra enables message broker
    When I check distributed extra
    Then the extra is functional

  @requires_analysis
  Scenario: Analysis extra enables Polars
    When I check analysis extra
    Then the extra is functional

  @requires_llm
  Scenario: LLM extra provides adapters
    When I check llm extra
    Then the extra is functional

  @requires_parsers
  Scenario: Parsers extra reads documents
    When I check parsers extra
    Then the extra is functional

  @requires_gpu
  Scenario: GPU extra exposes BERTopic
    When I check gpu extra
    Then the extra is functional
