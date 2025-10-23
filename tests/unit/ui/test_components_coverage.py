# mypy: ignore-errors
"""Tests for UI components to improve coverage."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping
from unittest.mock import MagicMock, patch

import pytest

from autoresearch.api.models import QueryResponse
from autoresearch.output_format import OutputDepth
from autoresearch.ui.components.config_editor import ConfigEditorComponent
from autoresearch.ui.components.results_display import ResultsDisplayComponent
from autoresearch.ui.provenance import (
    audit_status_rollup,
    depth_sequence,
    extract_graphrag_artifacts,
    format_gate_rationales,
    generate_socratic_prompts,
    section_toggle_defaults,
    triggered_gate_signals,
)


class TestConfigEditorComponent:
    """Tests for ConfigEditorComponent."""

    @pytest.fixture()
    def component(self):
        """Create a ConfigEditorComponent instance."""
        return ConfigEditorComponent()

    @patch("autoresearch.ui.components.config_editor.st")
    @patch("autoresearch.ui.components.config_editor.ConfigLoader")
    def test_render_basic_structure(self, mock_config_loader, mock_st, component):
        """Test basic render structure."""
        mock_config = MagicMock()
        mock_config_loader.return_value.load_config.return_value = mock_config

        # Mock streamlit form and elements
        mock_form = MagicMock()
        mock_st.sidebar.form.return_value.__enter__ = mock_form
        mock_st.sidebar.form.return_value.__exit__ = MagicMock()

        component.render()

        # Verify basic structure was called
        mock_st.sidebar.form.assert_called_once_with("config_editor")
        mock_st.markdown.assert_called()

    @patch("autoresearch.ui.components.config_editor.st")
    @patch("autoresearch.ui.components.config_editor.ConfigLoader")
    def test_render_presets_section(self, mock_config_loader, mock_st, component):
        """Test presets section rendering."""
        mock_config = MagicMock()
        mock_config_loader.return_value.load_config.return_value = mock_config

        component._render_presets_section()

        # Verify preset-related calls
        mock_st.selectbox.assert_called()
        mock_st.button.assert_called()

    def test_get_config_help_text(self, component):
        """Test help text generation."""
        help_text = component.get_config_help_text()
        assert isinstance(help_text, str)
        assert len(help_text) > 0

    def test_validate_config_valid(self, component):
        """Test config validation with valid config."""
        valid_config = {
            "search": {"backends": ["duckduckgo"]},
            "llm": {"backend": "openai"},
            "storage": {"backend": "duckdb"}
        }
        is_valid, message = component.validate_config(valid_config)
        assert is_valid
        assert "valid" in message.lower()

    def test_validate_config_invalid(self, component):
        """Test config validation with invalid config."""
        invalid_config = {
            "search": {"backends": []},  # Empty backends
        }
        is_valid, message = component.validate_config(invalid_config)
        assert not is_valid
        assert len(message) > 0


class TestResultsDisplayComponent:
    """Tests for ResultsDisplayComponent."""

    @pytest.fixture()
    def component(self):
        """Create a ResultsDisplayComponent instance."""
        return ResultsDisplayComponent()

    @pytest.fixture()
    def sample_response(self):
        """Create a sample QueryResponse."""
        return QueryResponse(
            answer="Test answer",
            citations=[{"title": "Test", "url": "https://test.com"}],
            reasoning=["Test reasoning"],
            metrics={"tokens": 100}
        )

    @patch("autoresearch.ui.components.results_display.st")
    def test_render_basic_structure(self, mock_st, component, sample_response):
        """Test basic render structure."""
        component.render(sample_response)

        # Verify basic structure calls
        mock_st.header.assert_called()
        mock_st.tabs.assert_called()

    def test_get_toggle_definitions(self, component):
        """Test toggle definitions."""
        definitions = component._get_toggle_definitions()
        assert isinstance(definitions, list)
        assert len(definitions) > 0
        for definition in definitions:
            assert len(definition) == 3  # (key, label, help)

    def test_get_toggle_states(self, component):
        """Test toggle state extraction."""
        toggle_defaults = {
            "section1": {"option1": True, "option2": False},
            "section2": {"option3": True}
        }
        states = component._get_toggle_states(toggle_defaults)
        assert isinstance(states, dict)
        assert "option1" in states
        assert "option2" in states
        assert "option3" in states

    def test_get_status_color(self, component):
        """Test status color mapping."""
        assert component._get_status_color("verified") == "green"
        assert component._get_status_color("contradicted") == "red"
        assert component._get_status_color("unknown") == "gray"

    def test_format_result_as_markdown(self, component, sample_response):
        """Test markdown formatting."""
        markdown = component._format_result_as_markdown(sample_response)
        assert isinstance(markdown, str)
        assert "Test answer" in markdown

    def test_format_result_as_json(self, component, sample_response):
        """Test JSON formatting."""
        json_str = component._format_result_as_json(sample_response)
        assert isinstance(json_str, str)
        assert "Test answer" in json_str

        # Should be valid JSON
        import json
        parsed = json.loads(json_str)
        assert "answer" in parsed


class TestProvenanceFunctions:
    """Tests for provenance utility functions."""

    def test_generate_socratic_prompts(self):
        """Test Socratic prompt generation."""
        payload = MagicMock()
        payload.depth = OutputDepth.DEEP
        payload.reasoning = ["Some reasoning"]

        prompts = generate_socratic_prompts(payload, max_prompts=2)
        assert isinstance(prompts, list)
        assert len(prompts) <= 2
        for prompt in prompts:
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_extract_graphrag_artifacts(self):
        """Test GraphRAG artifact extraction."""
        metrics = {
            "graphrag": {
                "communities": [{"id": 1, "summary": "Community 1"}],
                "relationships": [{"source": "A", "target": "B"}]
            }
        }

        artifacts = extract_graphrag_artifacts(metrics)
        assert isinstance(artifacts, dict)
        assert "communities" in artifacts

    def test_depth_sequence(self):
        """Test depth sequence generation."""
        sequence = depth_sequence()
        assert isinstance(sequence, list)
        assert len(sequence) > 0
        assert all(isinstance(depth, OutputDepth) for depth in sequence)

    def test_audit_status_rollup(self):
        """Test audit status rollup."""
        claim_audits = [
            {"status": "verified", "confidence": 0.9},
            {"status": "verified", "confidence": 0.8},
            {"status": "contradicted", "confidence": 0.7},
            {"status": "unknown", "confidence": 0.5}
        ]

        rollup = audit_status_rollup(claim_audits)
        assert isinstance(rollup, dict)
        assert "verified" in rollup
        assert "contradicted" in rollup
        assert "unknown" in rollup
        assert rollup["verified"] == 2
        assert rollup["contradicted"] == 1
        assert rollup["unknown"] == 1

    def test_section_toggle_defaults(self):
        """Test section toggle defaults generation."""
        payload = MagicMock()
        payload.depth = OutputDepth.DEEP

        defaults = section_toggle_defaults(payload)
        assert isinstance(defaults, dict)
        # Should have sections based on depth
        assert len(defaults) > 0

    def test_triggered_gate_signals(self):
        """Test gate signal extraction."""
        snapshot = {
            "gates": {
                "gate1": {"triggered": True, "reason": "Test reason"},
                "gate2": {"triggered": False, "reason": "Not triggered"},
                "gate3": {"triggered": True, "reason": "Another reason"}
            }
        }

        signals = triggered_gate_signals(snapshot)
        assert isinstance(signals, list)
        assert "gate1" in signals
        assert "gate3" in signals
        assert "gate2" not in signals

    def test_format_gate_rationales(self):
        """Test gate rationale formatting."""
        snapshot = {
            "gates": {
                "gate1": {"triggered": True, "reason": "Reason 1"},
                "gate2": {"triggered": True, "reason": "Reason 2"},
                "gate3": {"triggered": False, "reason": "Not triggered"}
            }
        }

        rationales = format_gate_rationales(snapshot)
        assert isinstance(rationales, list)
        assert len(rationales) == 2  # Only triggered gates
        for rationale in rationales:
            assert "Reason" in rationale


class TestUIIntegration:
    """Integration tests for UI components."""

    @patch("autoresearch.ui.components.config_editor.st")
    @patch("autoresearch.ui.components.results_display.st")
    def test_component_initialization(self, mock_st_results, mock_st_config):
        """Test that components can be initialized without errors."""
        config_component = ConfigEditorComponent()
        results_component = ResultsDisplayComponent()

        assert config_component is not None
        assert results_component is not None

        # Test that they have required methods
        assert hasattr(config_component, 'render')
        assert hasattr(results_component, 'render')

    def test_provenance_utilities_no_exceptions(self):
        """Test that provenance utilities don't raise exceptions with valid inputs."""
        # Test with minimal valid inputs
        payload = MagicMock()
        payload.depth = OutputDepth.BASIC
        payload.reasoning = []

        # These should not raise exceptions
        prompts = generate_socratic_prompts(payload)
        assert isinstance(prompts, list)

        sequence = depth_sequence()
        assert isinstance(sequence, list)

        rollup = audit_status_rollup([])
        assert isinstance(rollup, dict)

        defaults = section_toggle_defaults(payload)
        assert isinstance(defaults, dict)

        signals = triggered_gate_signals({})
        assert isinstance(signals, list)

        rationales = format_gate_rationales({})
        assert isinstance(rationales, list)
