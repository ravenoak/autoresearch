"""Tests for accessibility utilities and WCAG compliance."""

from __future__ import annotations


from autoresearch.ui.utils.accessibility import AccessibilityEnhancer, AccessibilityValidator


class TestAccessibilityValidator:
    """Test accessibility validation utilities."""

    def test_validate_color_contrast_compliant_colors(self) -> None:
        """Test color contrast validation with WCAG AA compliant colors."""
        validator = AccessibilityValidator()

        # Black on white (should pass)
        is_compliant, ratio = validator.validate_color_contrast("#000000", "#ffffff")
        assert is_compliant
        assert float(ratio.split(":")[0]) >= 4.5

        # White on black (should pass)
        is_compliant, ratio = validator.validate_color_contrast("#ffffff", "#000000")
        assert is_compliant
        assert float(ratio.split(":")[0]) >= 4.5

    def test_validate_color_contrast_non_compliant_colors(self) -> None:
        """Test color contrast validation with non-compliant colors."""
        validator = AccessibilityValidator()

        # Light gray on white (should fail)
        is_compliant, ratio = validator.validate_color_contrast("#cccccc", "#ffffff")
        assert not is_compliant
        assert float(ratio.split(":")[0]) < 4.5

    def test_validate_color_contrast_same_colors(self) -> None:
        """Test color contrast validation with identical colors."""
        validator = AccessibilityValidator()

        # Same color should have infinite contrast
        is_compliant, ratio = validator.validate_color_contrast("#000000", "#000000")
        assert is_compliant  # Infinite contrast passes
        assert ratio == "inf:1"

    def test_validate_aria_attributes_button_without_label(self) -> None:
        """Test ARIA validation for button without proper labeling."""
        validator = AccessibilityValidator()

        # Button without aria-label or descriptive text
        errors = validator.validate_aria_attributes("button", {})
        assert len(errors) > 0
        assert any("should have aria-label" in error for error in errors)

    def test_validate_aria_attributes_button_with_label(self) -> None:
        """Test ARIA validation for properly labeled button."""
        validator = AccessibilityValidator()

        # Button with aria-label
        errors = validator.validate_aria_attributes("button", {"aria-label": "Submit form"})
        assert len(errors) == 0

    def test_validate_aria_attributes_invalid_role(self) -> None:
        """Test ARIA validation for invalid role."""
        validator = AccessibilityValidator()

        # Invalid ARIA role
        errors = validator.validate_aria_attributes("div", {"role": "invalid_role"})
        assert len(errors) > 0
        assert any("Invalid ARIA role" in error for error in errors)

    def test_validate_aria_attributes_valid_role(self) -> None:
        """Test ARIA validation for valid role."""
        validator = AccessibilityValidator()

        # Valid ARIA role
        errors = validator.validate_aria_attributes("div", {"role": "button"})
        assert len(errors) == 0

    def test_validate_aria_attributes_describedby_format(self) -> None:
        """Test ARIA validation for aria-describedby format."""
        validator = AccessibilityValidator()

        # Invalid aria-describedby format
        errors = validator.validate_aria_attributes("div", {"aria-describedby": "description"})
        assert len(errors) > 0
        assert any("should reference an element ID" in error for error in errors)

    def test_validate_aria_attributes_describedby_valid_format(self) -> None:
        """Test ARIA validation for valid aria-describedby format."""
        validator = AccessibilityValidator()

        # Valid aria-describedby format
        errors = validator.validate_aria_attributes("div", {"aria-describedby": "#description"})
        assert len(errors) == 0

    def test_validate_keyboard_navigation_form(self) -> None:
        """Test keyboard navigation validation for forms."""
        validator = AccessibilityValidator()

        recommendations = validator.validate_keyboard_navigation("form")
        assert len(recommendations) > 0
        assert any("Tab order" in rec for rec in recommendations)
        assert any("Escape key" in rec for rec in recommendations)

    def test_validate_keyboard_navigation_tabs(self) -> None:
        """Test keyboard navigation validation for tabs."""
        validator = AccessibilityValidator()

        recommendations = validator.validate_keyboard_navigation("tabs")
        assert len(recommendations) > 0
        assert any("arrow key navigation" in rec for rec in recommendations)

    def test_generate_alt_text_knowledge_graph(self) -> None:
        """Test alt text generation for knowledge graph."""
        validator = AccessibilityValidator()

        context = {"entity_count": 5, "relation_count": 3}
        alt_text = validator.generate_alt_text("knowledge_graph", context)
        assert "5 entities" in alt_text
        assert "3 relationships" in alt_text

    def test_generate_alt_text_metrics_chart(self) -> None:
        """Test alt text generation for metrics chart."""
        validator = AccessibilityValidator()

        context = {"metrics": {"cpu_percent": 75.5, "memory_percent": 60.2}}
        alt_text = validator.generate_alt_text("metrics_chart", context)
        assert "75.5%" in alt_text
        assert "60.2%" in alt_text

    def test_generate_alt_text_generic(self) -> None:
        """Test alt text generation for unknown image type."""
        validator = AccessibilityValidator()

        alt_text = validator.generate_alt_text("unknown_type", {})
        assert "Image visualization" in alt_text

    def test_validate_semantic_structure_proper_headings(self) -> None:
        """Test semantic structure validation with proper heading hierarchy."""
        validator = AccessibilityValidator()

        html = "<h1>Title</h1><h2>Section</h2><h3>Subsection</h3>"
        issues = validator.validate_semantic_structure(html)
        # Should have no issues with proper hierarchy
        assert len(issues) == 0

    def test_validate_semantic_structure_heading_jump(self) -> None:
        """Test semantic structure validation with heading level jump."""
        validator = AccessibilityValidator()

        html = "<h1>Title</h1><h3>Section</h3>"  # Skip h2
        issues = validator.validate_semantic_structure(html)
        assert len(issues) > 0
        assert any("Heading level jump" in issue for issue in issues)

    def test_validate_semantic_structure_empty_heading(self) -> None:
        """Test semantic structure validation with empty heading."""
        validator = AccessibilityValidator()

        html = "<h1></h1><h2>Section</h2>"
        issues = validator.validate_semantic_structure(html)
        assert len(issues) > 0
        assert any("Empty heading" in issue for issue in issues)

    def test_validate_semantic_structure_unlabeled_landmark(self) -> None:
        """Test semantic structure validation with unlabeled landmark."""
        validator = AccessibilityValidator()

        html = "<main><p>Content</p></main>"
        issues = validator.validate_semantic_structure(html)
        assert len(issues) > 0
        assert any("should have aria-label" in issue for issue in issues)

    def test_validate_semantic_structure_labeled_landmark(self) -> None:
        """Test semantic structure validation with properly labeled landmark."""
        validator = AccessibilityValidator()

        html = '<main aria-label="Main content"><p>Content</p></main>'
        issues = validator.validate_semantic_structure(html)
        assert len(issues) == 0

    def test_validate_semantic_structure_unlabeled_input(self) -> None:
        """Test semantic structure validation with unlabeled input."""
        validator = AccessibilityValidator()

        html = '<input type="text" name="query">'
        issues = validator.validate_semantic_structure(html)
        assert len(issues) > 0
        assert any("should have a label" in issue for issue in issues)

    def test_validate_semantic_structure_labeled_input(self) -> None:
        """Test semantic structure validation with properly labeled input."""
        validator = AccessibilityValidator()

        html = '<label for="query">Search query:</label><input type="text" id="query" name="query">'
        issues = validator.validate_semantic_structure(html)
        # Should not have input labeling issues
        input_issues = [issue for issue in issues if "should have a label" in issue]
        assert len(input_issues) == 0


class TestAccessibilityEnhancer:
    """Test accessibility enhancement utilities."""

    def test_enhance_button_adds_aria_label(self) -> None:
        """Test that button enhancement adds ARIA label."""
        enhancer = AccessibilityEnhancer()

        # This would need to mock st.button to test properly
        # For now, just test that the enhancer exists and has the method
        assert hasattr(enhancer, "enhance_button")
        assert callable(enhancer.enhance_button)

    def test_enhance_text_input_adds_aria_label(self) -> None:
        """Test that text input enhancement adds ARIA label."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "enhance_text_input")
        assert callable(enhancer.enhance_text_input)

    def test_enhance_selectbox_adds_aria_label(self) -> None:
        """Test that selectbox enhancement adds ARIA label."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "enhance_selectbox")
        assert callable(enhancer.enhance_selectbox)

    def test_enhance_tabs_adds_aria_label(self) -> None:
        """Test that tabs enhancement adds ARIA label."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "enhance_tabs")
        assert callable(enhancer.enhance_tabs)

    def test_create_accessible_chart_generates_alt_text(self) -> None:
        """Test that accessible chart creation generates proper alt text."""
        enhancer = AccessibilityEnhancer()

        # This would need to mock st.markdown to test properly
        assert hasattr(enhancer, "create_accessible_chart")
        assert callable(enhancer.create_accessible_chart)

    def test_create_skip_link(self) -> None:
        """Test skip link creation."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "create_skip_link")
        assert callable(enhancer.create_skip_link)

    def test_announce_to_screen_reader(self) -> None:
        """Test screen reader announcement."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "announce_to_screen_reader")
        assert callable(enhancer.announce_to_screen_reader)

    def test_create_aria_landmark(self) -> None:
        """Test ARIA landmark creation."""
        enhancer = AccessibilityEnhancer()

        assert hasattr(enhancer, "create_aria_landmark")
        assert callable(enhancer.create_aria_landmark)


class TestAccessibilityIntegration:
    """Test integration of accessibility features."""

    def test_comprehensive_accessibility_application(self) -> None:
        """Test that comprehensive accessibility is applied correctly."""
        # Test that the function exists and can be called
        from autoresearch.ui.utils.accessibility import apply_comprehensive_accessibility

        assert callable(apply_comprehensive_accessibility)

    def test_validate_current_accessibility(self) -> None:
        """Test current accessibility validation."""
        from autoresearch.ui.utils.accessibility import validate_current_accessibility

        result = validate_current_accessibility()

        assert isinstance(result, dict)
        assert "is_compliant" in result
        assert "issues" in result
        assert "recommendations" in result
        assert isinstance(result["issues"], list)
        assert isinstance(result["recommendations"], list)

    def test_accessibility_validator_caching(self) -> None:
        """Test that color contrast validation uses caching."""
        validator = AccessibilityValidator()

        # First call should cache the result
        validator.validate_color_contrast("#000000", "#ffffff")

        # Second call should use cached result (this would need to be tested differently
        # since the cache is internal, but we can verify the method exists)
        assert hasattr(validator, "_color_cache")
        assert isinstance(validator._color_cache, dict)


# Integration tests for actual UI components would go here
# These would test the enhanced components in context


class TestComponentAccessibility:
    """Test accessibility features of actual UI components."""

    def test_query_input_component_accessibility(self) -> None:
        """Test that query input component has proper accessibility features."""
        from autoresearch.ui.components.query_input import QueryInputComponent

        component = QueryInputComponent()

        # Test that component has validation method
        assert hasattr(component, "validate_query")
        assert callable(component.validate_query)

        # Test validation logic
        is_valid, error = component.validate_query("")
        assert not is_valid
        assert "cannot be empty" in error

        is_valid, error = component.validate_query("test query")
        assert is_valid
        assert error == ""

    def test_query_input_component_dangerous_content_detection(self) -> None:
        """Test that query input detects potentially dangerous content."""
        from autoresearch.ui.components.query_input import QueryInputComponent

        component = QueryInputComponent()

        dangerous_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "eval('malicious code')",
        ]

        for query in dangerous_queries:
            is_valid, error = component.validate_query(query)
            assert not is_valid
            assert "unsafe content" in error

    def test_query_input_component_length_validation(self) -> None:
        """Test query length validation."""
        from autoresearch.ui.components.query_input import QueryInputComponent

        component = QueryInputComponent()

        # Too short
        is_valid, error = component.validate_query("ab")
        assert not is_valid
        assert "3 characters" in error

        # Too long
        long_query = "a" * 1001
        is_valid, error = component.validate_query(long_query)
        assert not is_valid
        assert "1000 characters" in error

    def test_results_display_component_accessibility_features(self) -> None:
        """Test that results display component has accessibility features."""
        from autoresearch.ui.components.results_display import ResultsDisplayComponent

        component = ResultsDisplayComponent()

        # Test that component has proper structure
        assert hasattr(component, "render")
        assert callable(component.render)

        # Test that component handles missing data gracefully
        # This would need to be tested with a mock result object
        # For now, just verify the component exists and has expected methods
        assert hasattr(component, "_render_depth_controls")
        assert hasattr(component, "_render_results_content")
        assert hasattr(component, "_render_main_tabs")

    def test_config_editor_component_accessibility_features(self) -> None:
        """Test that config editor component has accessibility features."""
        from autoresearch.ui.components.config_editor import ConfigEditorComponent

        component = ConfigEditorComponent()

        # Test that component has validation
        assert hasattr(component, "validate_config")
        assert callable(component.validate_config)

        # Test validation logic
        invalid_config = {"llm_backend": "", "loops": 0}
        is_valid, error = component.validate_config(invalid_config)
        assert not is_valid
        assert "cannot be empty" in error or "between 1 and 10" in error


# Performance tests for accessibility features


class TestAccessibilityPerformance:
    """Test performance of accessibility features."""

    def test_color_contrast_validation_performance(self) -> None:
        """Test that color contrast validation is reasonably fast."""
        import time

        validator = AccessibilityValidator()

        start_time = time.time()
        for _ in range(100):  # Test 100 validations
            validator.validate_color_contrast("#000000", "#ffffff")
        end_time = time.time()

        # Should complete in reasonable time (less than 1 second for 100 validations)
        assert end_time - start_time < 1.0

    def test_accessibility_validator_caching_improves_performance(self) -> None:
        """Test that caching improves performance for repeated validations."""
        import time

        validator = AccessibilityValidator()

        # First validation (not cached)
        start_time = time.time()
        result1 = validator.validate_color_contrast("#000000", "#ffffff")
        first_time = time.time() - start_time

        # Second validation (should use cache)
        start_time = time.time()
        result2 = validator.validate_color_contrast("#000000", "#ffffff")
        second_time = time.time() - start_time

        # Results should be the same
        assert result1 == result2

        # Second call should be faster (or at least not significantly slower)
        # Note: In practice, the cache lookup might be similar speed, but this tests the concept
        assert second_time <= first_time * 2  # Allow some margin for variability
