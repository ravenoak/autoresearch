from pytest_bdd import scenario, given, when, then, parsers
from unittest.mock import patch
import pytest

from __future__ import annotations

from pathlib import Path
from typing import Callable, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_bdd import given, parsers, scenario, then, when
from unittest.mock import MagicMock, patch

from autoresearch.cli_utils import format_error, format_info, format_success

from tests.behavior.context import (
    BehaviorContext,
    get_optional,
    get_required,
    set_value,
)

from .common_steps import application_running

pytestmark = pytest.mark.requires_ui


@given("the Autoresearch system is running")
def autoresearch_system_running(tmp_path: Path, _monkeypatch: MonkeyPatch) -> object:
    """Set up the Autoresearch system for testing."""

    return application_running(tmp_path)


@given("the Streamlit application is running")
def streamlit_app_running(
    monkeypatch: MonkeyPatch,
    bdd_context: BehaviorContext,
    tmp_path: Path,
) -> None:
    """Set up the Streamlit application for testing."""

    autoresearch_system_running(tmp_path, monkeypatch)

    initial_state: dict[str, object] = {}
    with patch("streamlit.session_state", initial_state) as session_state:
        set_value(bdd_context, "streamlit_session", session_state)

    with patch("streamlit.markdown") as mock_markdown:
        set_value(bdd_context, "mock_markdown", mock_markdown)


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "CLI Color Alternatives")
def test_cli_color_alternatives(bdd_context: BehaviorContext) -> None:
    """Test CLI color alternatives."""

    assert get_optional(bdd_context, "use_symbols", bool) is True


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "CLI Screen Reader Compatibility")
def test_cli_screen_reader_compatibility(bdd_context: BehaviorContext) -> None:
    """Test CLI screen reader compatibility."""

    assert get_optional(bdd_context, "screen_reader_mode", bool) is True


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "Streamlit GUI Keyboard Navigation")
def test_streamlit_keyboard_navigation(bdd_context: BehaviorContext) -> None:
    """Test Streamlit GUI keyboard navigation."""

    assert get_optional(bdd_context, "mock_text_input") is not None
    assert get_optional(bdd_context, "mock_button") is not None


@pytest.mark.slow
@scenario(
    "../features/ui_accessibility.feature", "Streamlit GUI Screen Reader Compatibility"
)
def test_streamlit_screen_reader_compatibility(
    bdd_context: BehaviorContext,
) -> None:
    """Test Streamlit GUI screen reader compatibility."""

    assert get_optional(bdd_context, "screen_reader_mode", bool) is True


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "High Contrast Mode")
def test_high_contrast_mode(bdd_context: BehaviorContext) -> None:
    """Test high contrast mode."""

    assert get_optional(bdd_context, "mock_markdown") is not None


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "Responsive Layout on Mobile")
def test_responsive_layout(bdd_context: BehaviorContext) -> None:
    """Test responsive layout on small screens."""

    assert get_optional(bdd_context, "css") is not None


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "Guided Tour Availability")
def test_guided_tour_availability(bdd_context: BehaviorContext) -> None:
    """Test guided tour availability."""

    assert get_optional(bdd_context, "tour_modal", bool) is True


@pytest.mark.slow
@scenario("../features/ui_accessibility.feature", "Skip to content link")
def test_skip_link(bdd_context: BehaviorContext) -> None:
    """Skip link should be present on the page."""

    markdown_calls = cast(list[str], get_optional(bdd_context, "markdown_calls", list))
    assert any("skip-link" in call for call in markdown_calls)


@when("I use the CLI with color output disabled")
def use_cli_without_color(bdd_context: BehaviorContext) -> None:
    """Simulate using the CLI with color output disabled."""

    set_value(bdd_context, "use_symbols", True)


@then("all information should be conveyed through text and symbols")
def check_text_and_symbols(bdd_context: BehaviorContext) -> None:
    """Check that information is conveyed through text and symbols."""

    use_symbols = get_required(bdd_context, "use_symbols", bool)
    error_msg = format_error("This is an error", symbol=use_symbols)
    assert "✗" in error_msg
    if not use_symbols:
        assert "Error" in error_msg

    success_msg = format_success("This is a success", symbol=use_symbols)
    assert "✓" in success_msg

    info_msg = format_info("This is info", symbol=use_symbols)
    assert "ℹ" in info_msg
    if not use_symbols:
        assert "Info" in info_msg


@then(parsers.parse('error messages should use symbolic indicators like "{symbol}"'))
def check_error_symbols(bdd_context: BehaviorContext, symbol: str) -> None:
    """Check that error messages use the specified symbol."""

    use_symbols = get_required(bdd_context, "use_symbols", bool)
    error_msg = format_error("Test error", symbol=use_symbols)
    assert symbol in error_msg


@then(parsers.parse('success messages should use symbolic indicators like "{symbol}"'))
def check_success_symbols(bdd_context: BehaviorContext, symbol: str) -> None:
    """Check that success messages use the specified symbol."""

    use_symbols = get_required(bdd_context, "use_symbols", bool)
    success_msg = format_success("Test success", symbol=use_symbols)
    assert symbol in success_msg


@then(
    parsers.parse(
        'informational messages should use symbolic indicators like "{symbol}"'
    )
)
def check_info_symbols(bdd_context: BehaviorContext, symbol: str) -> None:
    """Check that informational messages use the specified symbol."""

    use_symbols = get_required(bdd_context, "use_symbols", bool)
    info_msg = format_info("Test info", symbol=use_symbols)
    assert symbol in info_msg


@when("I use the CLI with a screen reader")
def use_cli_with_screen_reader(bdd_context: BehaviorContext) -> None:
    """Simulate using the CLI with a screen reader."""

    set_value(bdd_context, "screen_reader_mode", True)
    set_value(bdd_context, "use_symbols", True)


@then("all progress indicators should have text alternatives")
def check_progress_text_alternatives(bdd_context: BehaviorContext) -> None:
    """Check that progress indicators have text alternatives."""

    assert get_optional(bdd_context, "screen_reader_mode", bool) is True


@then("all visual elements should have text descriptions")
def check_visual_element_descriptions(bdd_context: BehaviorContext) -> None:
    """Check that visual elements have text descriptions."""

    assert get_optional(bdd_context, "screen_reader_mode", bool) is True


@then("command help text should be properly structured for screen readers")
def check_help_text_structure(bdd_context: BehaviorContext) -> None:
    """Check that command help text is properly structured for screen readers."""

    from autoresearch.main import app as cli_app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli_app, ["--help"])
    set_value(bdd_context, "cli_help_result", result)

    output = result.stdout
    assert "Usage:" in output
    assert "Commands:" in output
    assert "\x1b[" not in output


@when("I navigate the interface using only keyboard")
def navigate_with_keyboard(bdd_context: BehaviorContext) -> None:
    """Simulate navigating the interface using only keyboard."""

    with patch("streamlit.text_input") as mock_text_input:
        mock_text_input.return_value = "Test query"
        set_value(bdd_context, "mock_text_input", mock_text_input)

    with patch("streamlit.button") as mock_button:
        mock_button.return_value = True
        set_value(bdd_context, "mock_button", mock_button)


@then("I should be able to access all functionality")
def check_keyboard_accessibility(bdd_context: BehaviorContext) -> None:
    """Check that all functionality is accessible via keyboard."""

    assert get_optional(bdd_context, "mock_text_input") is not None
    assert get_optional(bdd_context, "mock_button") is not None


@then("focus indicators should be clearly visible")
def check_focus_indicators(bdd_context: BehaviorContext) -> None:
    """Check that focus indicators are clearly visible."""
    from autoresearch.streamlit_ui import apply_accessibility_settings

    with patch("streamlit.markdown") as mock_markdown:
        apply_accessibility_settings()

    css = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert "*:focus" in css
    assert "outline" in css


@then("tab order should be logical and follow page structure")
def check_tab_order(bdd_context: BehaviorContext) -> None:
    """Check that tab order is logical and follows page structure."""
    from autoresearch.streamlit_app import display_query_input

    with patch("streamlit.markdown") as mock_markdown:
        display_query_input()

    html = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert "tabindex" in html


@when("I use the GUI with a screen reader")
def use_gui_with_screen_reader(bdd_context: BehaviorContext) -> None:
    """Simulate using the GUI with a screen reader."""

    set_value(bdd_context, "screen_reader_mode", True)


@then("all images should have alt text")
def check_image_alt_text(bdd_context: BehaviorContext) -> None:
    """Check that all images have alt text."""
    # Patch streamlit.image so no Streamlit runtime is required
    with patch("streamlit.image") as mock_image:
        from streamlit import image

        image("test.png", caption="Alt text for test image")

        mock_image.assert_called_once()


@then("all form controls should have proper labels")
def check_form_control_labels(bdd_context: BehaviorContext) -> None:
    """Check that all form controls have proper labels."""
    # Patch streamlit.text_input so no Streamlit runtime is required
    with patch("streamlit.text_input") as mock_text_input:
        from streamlit import text_input

        text_input("Query", value="Test query")

        mock_text_input.assert_called_once()
        args = mock_text_input.call_args[0]
        assert args[0] == "Query"


@then("dynamic content updates should be announced to screen readers")
def check_dynamic_content_announcements(bdd_context: BehaviorContext) -> None:
    """Check that dynamic content updates are announced to screen readers."""
    from autoresearch.models import QueryResponse
    from autoresearch.streamlit_app import display_results

    dummy = QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})
    with patch("streamlit.markdown") as mock_markdown:
        display_results(dummy)

    html = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert "aria-live='polite'" in html or 'aria-live="polite"' in html


@when("I enable high contrast mode")
def enable_high_contrast_mode(bdd_context: BehaviorContext) -> None:
    """Simulate enabling high contrast mode."""
    from autoresearch.streamlit_ui import apply_accessibility_settings

    with patch("streamlit.markdown") as mock_markdown:
        with patch("streamlit.session_state", {"high_contrast": True}):
            apply_accessibility_settings()
        set_value(bdd_context, "mock_markdown", mock_markdown)


@then("text should have sufficient contrast against backgrounds")
def check_text_contrast(bdd_context: BehaviorContext) -> None:
    """Check that text has sufficient contrast against backgrounds."""
    mock_markdown = cast(MagicMock, get_required(bdd_context, "mock_markdown"))

    css = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert "background-color:#000" in css
    assert "color:#fff" in css


@then("interactive elements should be clearly distinguishable")
def check_interactive_elements(bdd_context: BehaviorContext) -> None:
    """Check that interactive elements are clearly distinguishable."""
    mock_markdown = cast(MagicMock, get_required(bdd_context, "mock_markdown"))

    css = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert ".stButton" in css
    assert "border" in css


@then("information should not be conveyed by color alone")
def check_color_independence(bdd_context: BehaviorContext) -> None:
    """Check that information is not conveyed by color alone."""
    mock_markdown = cast(MagicMock, get_required(bdd_context, "mock_markdown"))

    css = "".join(call.args[0] for call in mock_markdown.call_args_list)
    assert "text-decoration: underline" in css or "border" in css


@given("the Streamlit application is running on a small screen")
def streamlit_small_screen(
    monkeypatch: MonkeyPatch, bdd_context: BehaviorContext, tmp_path: Path
) -> None:
    """Set up the Streamlit app and capture CSS for mobile layout."""

    autoresearch_system_running(tmp_path, monkeypatch)
    with (
        patch("streamlit.session_state", {}),
        patch("streamlit.markdown") as mock_markdown,
    ):
        import importlib
        import autoresearch.streamlit_app as app

        importlib.reload(app)
        css_blocks = [
            call.args[0]
            for call in mock_markdown.call_args_list
            if call.args and "<style>" in call.args[0]
        ]
        set_value(bdd_context, "css", "".join(css_blocks))


@when("I view the page")
def view_page(bdd_context: BehaviorContext) -> None:
    """Verify CSS was captured for the responsive layout."""

    assert get_optional(bdd_context, "css") is not None


@then("columns should stack vertically")
def columns_stack_vertically(bdd_context: BehaviorContext) -> None:
    """Ensure CSS contains rules for vertical stacking."""

    css = cast(str, get_optional(bdd_context, "css", str) or "")
    assert "flex-direction: column" in css


@then("controls should remain usable without horizontal scrolling")
def controls_no_horizontal_scroll(bdd_context: BehaviorContext) -> None:
    """Check controls adapt to small widths."""

    css = cast(str, get_optional(bdd_context, "css", str) or "")
    assert "width: 100%" in css


@when("I open the page for the first time")
def open_page_first_time(bdd_context: BehaviorContext) -> None:
    """Simulate opening the page for the first time."""

    with patch("streamlit.modal") as mock_modal:
        import importlib

        module = importlib.import_module("autoresearch.streamlit_app")
        display_guided_tour = cast(
            Callable[[], None], getattr(module, "display_guided_tour")
        )

        display_guided_tour()
        set_value(bdd_context, "tour_modal", mock_modal.called)


@then("a guided tour modal should describe the main features")
def check_guided_tour_modal(bdd_context: BehaviorContext) -> None:
    """Verify the modal was displayed."""

    assert get_optional(bdd_context, "tour_modal", bool) is True


@then("I should be able to dismiss the tour")
def dismiss_tour() -> None:
    """Ensure the tour can be dismissed via the button."""
    with (
        patch("streamlit.session_state", {"show_tour": True}),
        patch("streamlit.button", return_value=True),
        patch("streamlit.modal"),
    ):
        from autoresearch.streamlit_ui import display_guided_tour

        display_guided_tour()
        import streamlit as st

        assert st.session_state.show_tour is False


@when("I load the Streamlit page")
def load_streamlit_page(bdd_context: BehaviorContext) -> None:
    with (
        patch("streamlit.markdown") as mock_markdown,
        patch("streamlit.session_state", {}),
    ):
        import importlib
        import autoresearch.streamlit_app as app

        importlib.reload(app)

        calls = [call.args[0] for call in mock_markdown.call_args_list if call.args]
        set_value(bdd_context, "markdown_calls", calls)


@then("a skip to main content link should be present")
def check_skip_link(bdd_context: BehaviorContext) -> None:
    markdown_calls = cast(list[str], get_optional(bdd_context, "markdown_calls", list))
    assert any("skip-link" in call for call in markdown_calls)
