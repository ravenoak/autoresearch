"""UI helper functions for theme, accessibility, and user guidance.

This module provides utility functions for:
- Theme management (light/dark mode, high contrast)
- Accessibility enhancements
- Guided tours and help systems
- Modal dialogs and user guidance
"""

from __future__ import annotations

import time
from typing import Any, cast

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

            def empty(self) -> Any:
                return self

            def code(self, *args, **kwargs) -> None:
                pass

        st = cast(Any, MockStreamlit())


def apply_theme_settings() -> None:
    """Apply theme settings based on session state."""
    if cast(Any, st).session_state.get("dark_mode"):
        cast(Any, st).markdown(
            """
            <style>
            body, .stApp {background-color:#222 !important; color:#e0e0e0 !important;}
            a {color:#93c5fd !important;}
            .stButton>button {background-color:#444 !important; color:#fff !important;}
            .stSidebar {background-color:#2c2c2c !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        cast(Any, st).markdown(
            """
            <style>
            body, .stApp {background-color:#fff !important; color:#000 !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def apply_accessibility_settings() -> None:
    """Apply accessibility enhancements based on session state."""
    cast(Any, st).markdown(
        """
        <style>
        *:focus {outline: 2px solid #ffbf00 !important; outline-offset: 2px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if cast(Any, st).session_state.get("high_contrast"):
        cast(Any, st).markdown(
            """
            <style>
            body, .stApp {background-color:#000 !important; color:#fff !important;}
            a {color:#0ff !important; text-decoration: underline !important;}
            .stButton>button {background-color:#fff !important; color:#000 !important; border:2px solid #fff !important;}
            .stSidebar {background-color:#000 !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def display_guided_tour() -> None:
    """Display a guided tour for new users."""
    if "show_tour" not in cast(Any, st).session_state:
        cast(Any, st).session_state.show_tour = True

    if cast(Any, st).session_state.show_tour:
        # Use a simple modal if available, otherwise use an expander
        try:
            # Try to use st.modal if available (Streamlit 1.28+)
            modal_func = getattr(cast(Any, st), "modal", None)
            if modal_func and callable(modal_func):
                with cast(Any, st).modal("Welcome to Autoresearch", key="guided_tour"):
                    _render_tour_content()
            else:
                # Fallback to expander for older Streamlit versions
                with cast(Any, st).expander("🚀 Welcome to Autoresearch", expanded=True):
                    _render_tour_content()
        except Exception:
            # Ultimate fallback
            cast(Any, st).info(
                "🚀 Welcome to Autoresearch! Check out the tutorial in the sidebar for help getting started."
            )


def _render_tour_content() -> None:
    """Render the content of the guided tour."""
    cast(Any, st).markdown(
        """
        **Welcome to Autoresearch!** 🎉

        This tool helps you conduct comprehensive research using multiple AI agents that collaborate to provide evidence-backed answers.

        **Quick Start:**
        1. **Enter a question** in the main panel
        2. **Choose your reasoning approach** (Dialectical, Socratic, or Collaborative)
        3. **Set the number of research loops** (1-5)
        4. **Click "Run Query"** to start the research

        **What you'll get:**
        - **Evidence-backed answers** with citations
        - **Multiple perspectives** from different AI agents
        - **Knowledge graph** showing relationships between concepts
        - **Claim verification** with confidence scores

        **Tips:**
        - Use the sidebar to configure settings and view preferences
        - Check the "History" tab to see previous queries
        - Use "Metrics Dashboard" to monitor system performance
        - Enable "High Contrast Mode" in the sidebar for better accessibility

        Ready to explore? Enter your first question above!
        """
    )

    if cast(Any, st).button("Got it! Let's start researching", key="tour_done", type="primary"):
        cast(Any, st).session_state.show_tour = False
        cast(Any, st).rerun()


def display_help_sidebar() -> None:
    """Display contextual help in the sidebar."""
    if "first_visit" not in cast(Any, st).session_state:
        cast(Any, st).session_state.first_visit = True

    expanded = cast(Any, st).session_state.first_visit

    with cast(Any, st).sidebar.expander("💡 Help & Tips", expanded=expanded):
        cast(Any, st).markdown(
            """
            **Getting Started**

            1. **Enter your research question** in the main panel
            2. **Choose a reasoning mode** that fits your needs:
               - **Dialectical**: Multiple agents debate and synthesize findings
               - **Socratic**: Guided questioning approach
               - **Collaborative**: Team-based research approach
            3. **Set the number of loops** for deeper analysis (1-5)
            4. **Click "Run Query"** to start the research process

            **Understanding Results**

            - **TL;DR**: Auto-generated summary of key findings
            - **Answer**: Main response with evidence and reasoning
            - **Citations**: Sources and references for claims
            - **Reasoning**: Step-by-step agent thought process
            - **Knowledge Graph**: Visual representation of concepts and relationships

            **Advanced Features**

            - **Claim Verification**: Check the reliability of individual claims
            - **Progressive Disclosure**: Use depth controls to see more/less detail
            - **Export Options**: Download results as Markdown or JSON
            - **Configuration**: Customize settings in the sidebar

            **Troubleshooting**

            - If queries fail, check your LLM backend configuration
            - For slow responses, try reducing the number of loops
            - Use the "Logs" tab to debug issues

            **Keyboard Shortcuts**

            - **Tab**: Navigate between form fields
            - **Enter**: Submit form when focused on "Run Query"
            - **Ctrl+R**: Refresh the page (if needed)

            Need more help? Check the documentation or ask in the community forums!
            """
        )

        if expanded:
            if cast(Any, st).button("Got it, thanks!", key="dismiss_help"):
                cast(Any, st).session_state.first_visit = False


def create_loading_spinner(text: str = "Processing...") -> None:
    """Create a loading spinner with custom text."""
    with cast(Any, st).spinner(text):
        pass


def show_success_message(message: str, duration: int = 3) -> None:
    """Show a temporary success message."""
    placeholder = cast(Any, st).empty()
    placeholder.success(message)

    # Auto-dismiss after duration
    time.sleep(duration)
    placeholder.empty()


def show_error_message(message: str, details: str = "") -> None:
    """Show an error message with optional details."""
    cast(Any, st).error(message)

    if details:
        with cast(Any, st).expander("Error Details"):
            cast(Any, st).code(details, language="text")


def create_info_card(title: str, content: str, icon: str = "ℹ️") -> None:
    """Create a styled information card."""
    cast(Any, st).markdown(
        f"""
        <div style="
            background-color: #f0f2f6;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #0066cc;
        ">
            <h4 style="margin-top: 0; color: #0066cc;">{icon} {title}</h4>
            <p style="margin-bottom: 0;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_progress_card(title: str, progress: float, details: str = "") -> None:
    """Create a progress indicator card."""
    cast(Any, st).markdown(f"**{title}**")
    cast(Any, st).progress(progress)

    if details:
        cast(Any, st).caption(details)


def format_file_size(size_bytes: float) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
