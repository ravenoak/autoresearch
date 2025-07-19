"""Helper functions for the Streamlit user interface."""
from __future__ import annotations

import streamlit as st


def apply_accessibility_settings() -> None:
    """Apply high-contrast and focus styles when enabled."""
    st.markdown(
        """
        <style>
        *:focus {outline: 2px solid #ffbf00 !important; outline-offset: 2px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("high_contrast"):
        st.markdown(
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


def apply_theme_settings() -> None:
    """Toggle between light and dark themes based on session state."""
    if st.session_state.get("dark_mode"):
        st.markdown(
            """
            <style>
            body, .stApp {background-color:#1c1c1c !important; color:#e0e0e0 !important;}
            a {color:#93c5fd !important;}
            .stButton>button {background-color:#444 !important; color:#fff !important;}
            .stSidebar {background-color:#2c2c2c !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            body, .stApp {background-color:#fff !important; color:#000 !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def display_guided_tour() -> None:
    """Render a short onboarding tour on first launch."""
    if "show_tour" not in st.session_state:
        st.session_state.show_tour = True
    if st.session_state.show_tour:
        with st.modal("Welcome to Autoresearch", key="guided_tour", aria_modal=True):  # type: ignore[attr-defined]
            st.markdown(
                """
                <div role="dialog" aria-label="Onboarding Tour" aria-modal="true">
                <ol>
                    <li><strong>Enter a query</strong> in the text area on the main tab.</li>
                    <li><strong>Adjust settings</strong> like reasoning mode and loops.</li>
                    <li>Click <strong>Run Query</strong> to start the agents.</li>
                    <li>Review results using the tabs below the answer.</li>
                    <li>Use the sidebar to configure themes and preferences.</li>
                </ol>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Got it", key="tour_done", help="Close the guided tour"):
                st.session_state.show_tour = False


def display_help_sidebar() -> None:
    """Add a tutorial sidebar that can be dismissed."""
    if "first_visit" not in st.session_state:
        st.session_state.first_visit = True

    expanded = st.session_state.first_visit
    with st.sidebar.expander("Tutorial", expanded=expanded):
        st.markdown(
            """
            **Getting Started**

            1. Enter a question in the main panel.
            2. Choose the reasoning mode and loops.
            3. Press **Run Query** to launch the agents.
            """
        )
        if expanded:
            if st.button("Dismiss tutorial", key="dismiss_tutorial"):
                st.session_state.first_visit = False
