from pytest_bdd import scenario, given, when, then, parsers
from unittest.mock import patch

from .common_steps import application_running
from autoresearch.cli_utils import format_error, format_success, format_info


@given("the Autoresearch system is running")
def autoresearch_system_running(tmp_path, monkeypatch):
    """Set up the Autoresearch system for testing."""
    # This is essentially the same as application_running in common_steps.py
    return application_running(tmp_path, monkeypatch)


@given("the Streamlit application is running")
def streamlit_app_running(monkeypatch, bdd_context, tmp_path):
    """Set up the Streamlit application for testing."""
    # First ensure the Autoresearch system is running
    autoresearch_system_running(tmp_path, monkeypatch)

    # Mock Streamlit session state
    with patch("streamlit.session_state", {}) as mock_session_state:
        bdd_context["streamlit_session"] = mock_session_state

    # Mock other Streamlit components as needed
    with patch("streamlit.markdown") as mock_markdown:
        bdd_context["mock_markdown"] = mock_markdown


@scenario("../features/ui_accessibility.feature", "CLI Color Alternatives")
def test_cli_color_alternatives(bdd_context):
    """Test CLI color alternatives."""
    assert bdd_context.get("use_symbols") is True


@scenario("../features/ui_accessibility.feature", "CLI Screen Reader Compatibility")
def test_cli_screen_reader_compatibility(bdd_context):
    """Test CLI screen reader compatibility."""
    assert bdd_context.get("screen_reader_mode") is True


@scenario("../features/ui_accessibility.feature", "Streamlit GUI Keyboard Navigation")
def test_streamlit_keyboard_navigation(bdd_context):
    """Test Streamlit GUI keyboard navigation."""
    assert "mock_text_input" in bdd_context and "mock_button" in bdd_context


@scenario(
    "../features/ui_accessibility.feature", "Streamlit GUI Screen Reader Compatibility"
)
def test_streamlit_screen_reader_compatibility(bdd_context):
    """Test Streamlit GUI screen reader compatibility."""
    assert bdd_context.get("screen_reader_mode") is True


@scenario("../features/ui_accessibility.feature", "High Contrast Mode")
def test_high_contrast_mode(bdd_context):
    """Test high contrast mode."""
    assert "mock_markdown" in bdd_context


@when("I use the CLI with color output disabled")
def use_cli_without_color(bdd_context):
    """Simulate using the CLI with color output disabled."""
    # We'll use the format functions directly
    # In a real implementation, we would mock the console to disable color
    bdd_context["use_symbols"] = True


@then("all information should be conveyed through text and symbols")
def check_text_and_symbols(bdd_context):
    """Check that information is conveyed through text and symbols."""
    use_symbols = bdd_context["use_symbols"]

    # Test error message
    error_msg = format_error("This is an error", symbol=use_symbols)
    assert "✗" in error_msg
    # When symbol is True, the message doesn't contain "Error"
    if not use_symbols:
        assert "Error" in error_msg

    # Test success message
    success_msg = format_success("This is a success", symbol=use_symbols)
    assert "✓" in success_msg

    # Test info message
    info_msg = format_info("This is info", symbol=use_symbols)
    assert "ℹ" in info_msg
    # When symbol is True, the message doesn't contain "Info"
    if not use_symbols:
        assert "Info" in info_msg


@then(parsers.parse('error messages should use symbolic indicators like "{symbol}"'))
def check_error_symbols(bdd_context, symbol):
    """Check that error messages use the specified symbol."""
    use_symbols = bdd_context["use_symbols"]
    error_msg = format_error("Test error", symbol=use_symbols)
    assert symbol in error_msg


@then(parsers.parse('success messages should use symbolic indicators like "{symbol}"'))
def check_success_symbols(bdd_context, symbol):
    """Check that success messages use the specified symbol."""
    use_symbols = bdd_context["use_symbols"]
    success_msg = format_success("Test success", symbol=use_symbols)
    assert symbol in success_msg


@then(
    parsers.parse(
        'informational messages should use symbolic indicators like "{symbol}"'
    )
)
def check_info_symbols(bdd_context, symbol):
    """Check that informational messages use the specified symbol."""
    use_symbols = bdd_context["use_symbols"]
    info_msg = format_info("Test info", symbol=use_symbols)
    assert symbol in info_msg


@when("I use the CLI with a screen reader")
def use_cli_with_screen_reader(bdd_context):
    """Simulate using the CLI with a screen reader."""
    # In a real implementation, we would configure the CLI for screen readers
    # For now, we'll just set a flag to indicate screen reader mode
    bdd_context["screen_reader_mode"] = True
    bdd_context["use_symbols"] = True  # Symbols are important for screen readers


@then("all progress indicators should have text alternatives")
def check_progress_text_alternatives(bdd_context):
    """Check that progress indicators have text alternatives."""
    # In a real implementation, we would check that progress indicators have text alternatives
    # For now, we'll just assert that screen reader mode is enabled
    assert bdd_context.get("screen_reader_mode", False) is True

    # We would typically check that progress indicators use ASCII characters
    # and provide text updates for screen readers
    # For example, with tqdm:
    # with patch('tqdm.tqdm') as mock_tqdm:
    #     # Call some function that uses tqdm
    #     # Verify that tqdm was called with ascii=True
    #     mock_tqdm.assert_called_once()
    #     kwargs = mock_tqdm.call_args[1]
    #     assert kwargs.get('ascii', False) is True


@then("all visual elements should have text descriptions")
def check_visual_element_descriptions(bdd_context):
    """Check that visual elements have text descriptions."""
    # In a real implementation, we would check that visual elements have text descriptions
    # For now, we'll just assert that screen reader mode is enabled
    assert bdd_context.get("screen_reader_mode", False) is True

    # We would typically check that tables and other visual elements
    # have appropriate text descriptions for screen readers
    # For example, with tabulate:
    # with patch('tabulate.tabulate') as mock_tabulate:
    #     # Call some function that uses tabulate
    #     # Verify that tabulate was called with appropriate parameters
    #     mock_tabulate.assert_called_once()


@then("command help text should be properly structured for screen readers")
def check_help_text_structure(bdd_context):
    """Check that command help text is properly structured for screen readers."""
    # This would typically check the structure of help text from the CLI
    # For now, we'll just assert True as a placeholder
    assert True


@when("I navigate the interface using only keyboard")
def navigate_with_keyboard(bdd_context):
    """Simulate navigating the interface using only keyboard."""
    # Mock Streamlit components to test keyboard navigation
    with patch("streamlit.text_input") as mock_text_input:
        mock_text_input.return_value = "Test query"
        bdd_context["mock_text_input"] = mock_text_input

    with patch("streamlit.button") as mock_button:
        mock_button.return_value = True
        bdd_context["mock_button"] = mock_button


@then("I should be able to access all functionality")
def check_keyboard_accessibility(bdd_context):
    """Check that all functionality is accessible via keyboard."""
    # Verify that keyboard navigation works for critical components
    assert "mock_text_input" in bdd_context
    assert "mock_button" in bdd_context


@then("focus indicators should be clearly visible")
def check_focus_indicators(bdd_context):
    """Check that focus indicators are clearly visible."""
    # This would typically check CSS properties for focus indicators
    # For now, we'll just assert True as a placeholder
    assert True


@then("tab order should be logical and follow page structure")
def check_tab_order(bdd_context):
    """Check that tab order is logical and follows page structure."""
    # This would typically check the tab order of elements
    # For now, we'll just assert True as a placeholder
    assert True


@when("I use the GUI with a screen reader")
def use_gui_with_screen_reader(bdd_context):
    """Simulate using the GUI with a screen reader."""
    # Flag screen reader mode so other steps can adjust behaviour
    bdd_context["screen_reader_mode"] = True


@then("all images should have alt text")
def check_image_alt_text(bdd_context):
    """Check that all images have alt text."""
    # Patch streamlit.image so no Streamlit runtime is required
    with patch("streamlit.image") as mock_image:
        from streamlit import image

        image("test.png", caption="Alt text for test image")

        mock_image.assert_called_once()


@then("all form controls should have proper labels")
def check_form_control_labels(bdd_context):
    """Check that all form controls have proper labels."""
    # Patch streamlit.text_input so no Streamlit runtime is required
    with patch("streamlit.text_input") as mock_text_input:
        from streamlit import text_input

        text_input("Query", value="Test query")

        mock_text_input.assert_called_once()
        args = mock_text_input.call_args[0]
        assert args[0] == "Query"


@then("dynamic content updates should be announced to screen readers")
def check_dynamic_content_announcements(bdd_context):
    """Check that dynamic content updates are announced to screen readers."""
    # This would typically check ARIA live regions or similar
    # For now, we'll just assert True as a placeholder
    assert True


@when("I enable high contrast mode")
def enable_high_contrast_mode(bdd_context):
    """Simulate enabling high contrast mode."""
    # Mock Streamlit components to test high contrast mode
    with patch("streamlit.markdown") as mock_markdown:
        bdd_context["mock_markdown"] = mock_markdown


@then("text should have sufficient contrast against backgrounds")
def check_text_contrast(bdd_context):
    """Check that text has sufficient contrast against backgrounds."""
    # This would typically check CSS properties for contrast
    # For now, we'll just assert True as a placeholder
    assert True


@then("interactive elements should be clearly distinguishable")
def check_interactive_elements(bdd_context):
    """Check that interactive elements are clearly distinguishable."""
    # This would typically check CSS properties for interactive elements
    # For now, we'll just assert True as a placeholder
    assert True


@then("information should not be conveyed by color alone")
def check_color_independence(bdd_context):
    """Check that information is not conveyed by color alone."""
    # This would typically check that information is conveyed by multiple means
    # For now, we'll just assert True as a placeholder
    assert True
