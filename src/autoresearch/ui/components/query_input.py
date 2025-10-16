"""Query input component with reasoning mode controls.

This module provides a focused, accessible query input interface that handles:
- Query text input with validation
- Reasoning mode selection
- Loop configuration
- Form submission and validation
- Accessibility features and keyboard navigation
"""

from __future__ import annotations

from typing import Any, Optional, cast

from ...orchestration import ReasoningMode

try:
    import streamlit as st
except ImportError:
    # For test environments without streamlit
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        import streamlit as st
    else:

        class MockStreamlit:
            def __getattr__(self, name: str) -> Any:
                return lambda *args, **kwargs: None

        st = MockStreamlit()


class QueryInputComponent:
    """Handles query input, reasoning mode selection, and form submission."""

    def __init__(self) -> None:
        """Initialize the query input component."""
        self._form_key = "query_form"
        self._query_input_key = "query_input"
        self._reasoning_mode_key = "reasoning_mode_widget"
        self._loops_key = "loops_slider"

    def render(self) -> tuple[Optional[str], Optional[str], Optional[int]]:
        """Render the query input interface.

        Returns:
            Tuple of (query_text, reasoning_mode, loops) or (None, None, None) if not submitted
        """
        st.markdown(
            "<h2 class='subheader'>Query Input</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            (
                "<p id='keyboard-nav' class='sr-only'>"
                "Use Tab to navigate fields and press Enter on 'Run Query' to submit."
                "</p>"
            ),
            unsafe_allow_html=True,
        )

        with st.form(self._form_key):
            st.markdown(
                "<div role='region' aria-label='Query input area' tabindex='0'>",
                unsafe_allow_html=True,
            )

            # Query input column
            col_query, col_actions = st.columns([3, 1])

            with col_query:
                query = st.text_area(
                    "Enter your query:",
                    height=100,
                    placeholder="What would you like to research?",
                    key=self._query_input_key,
                    help="After typing, press Tab to reach the Run button",
                )

            with col_actions:
                # Get current config for defaults
                config = cast(dict[str, Any], st.session_state.get("config", {}))

                # Reasoning mode selection
                reasoning_modes = [mode.value for mode in ReasoningMode]
                current_mode = config.get("reasoning_mode", ReasoningMode.DIALECTICAL.value)
                default_index = (
                    reasoning_modes.index(current_mode) if current_mode in reasoning_modes else 0
                )

                reasoning_mode = st.selectbox(
                    "Reasoning Mode:",
                    options=reasoning_modes,
                    index=default_index,
                    key=self._reasoning_mode_key,
                )

                # Loops configuration
                current_loops = config.get("loops", 3)
                loops = st.slider(
                    "Loops:",
                    min_value=1,
                    max_value=5,
                    value=current_loops,
                    key=self._loops_key,
                )

                # Submit button
                submitted = st.form_submit_button(
                    "Run Query",
                    type="primary",
                    help="Activate to run your query",
                    use_container_width=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

        # Return results if form was submitted
        if submitted and query:
            return query, reasoning_mode, loops
        elif submitted and not query:
            st.warning("Please enter a query")
            return None, None, None

        return None, None, None

    def get_help_text(self) -> str:
        """Get contextual help text for the query input."""
        return """
        **Query Input Help:**

        1. **Enter your question** in the text area above
        2. **Choose a reasoning mode** that fits your research needs:
           - **Dialectical**: Multiple agents debate and synthesize findings
           - **Socratic**: Guided questioning approach
           - **Collaborative**: Team-based research approach
        3. **Set the number of loops** for deeper analysis (1-5)
        4. **Click "Run Query"** to start the research process

        **Keyboard Navigation:**
        - Tab through form fields
        - Enter to submit when focused on "Run Query" button
        - Escape to cancel and clear form
        """

    def validate_query(self, query: str) -> tuple[bool, str]:
        """Validate the query input.

        Args:
            query: The query string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"

        if len(query.strip()) < 3:
            return False, "Query must be at least 3 characters long"

        if len(query) > 1000:
            return False, "Query must be less than 1000 characters"

        # Check for potentially harmful content
        dangerous_patterns = ["<script", "javascript:", "eval(", "exec("]
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False, "Query contains potentially unsafe content"

        return True, ""
