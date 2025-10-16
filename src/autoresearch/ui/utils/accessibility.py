"""Accessibility utilities for WCAG compliance and enhanced usability.

This module provides utilities for ensuring WCAG 2.1 AA compliance including:
- Color contrast validation
- Screen reader support
- Keyboard navigation enhancements
- Focus management
- ARIA labeling and landmarks
- Alternative text for images
- Semantic HTML structure
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

try:
    import streamlit as st
except ImportError:
    # For test environments without streamlit
    from typing import Callable

    class MockStreamlit:
        def __getattr__(self, name: str) -> Callable[..., Any]:
            return lambda *args, **kwargs: None

    st = MockStreamlit()  # type: ignore


class AccessibilityValidator:
    """Validates accessibility compliance for UI components."""

    def __init__(self) -> None:
        """Initialize the accessibility validator."""
        self._color_cache: Dict[str, Tuple[bool, str]] = {}

    def validate_color_contrast(self, foreground: str, background: str) -> Tuple[bool, str]:
        """Validate color contrast ratio for WCAG AA compliance.

        Args:
            foreground: Foreground color (hex)
            background: Background color (hex)

        Returns:
            Tuple of (is_compliant, contrast_ratio)
        """
        cache_key = f"{foreground}:{background}"
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        try:
            # Convert hex to RGB
            fg_rgb = self._hex_to_rgb(foreground)
            bg_rgb = self._hex_to_rgb(background)

            # Calculate relative luminance
            fg_lum = self._relative_luminance(fg_rgb)
            bg_lum = self._relative_luminance(bg_rgb)

            # Calculate contrast ratio
            lighter = max(fg_lum, bg_lum)
            darker = min(fg_lum, bg_lum)

            if darker == 0:
                ratio = float("inf")
            else:
                ratio = (lighter + 0.05) / (darker + 0.05)

            # Check WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)
            is_compliant = ratio >= 4.5

            result = (is_compliant, f"{ratio:.2f}:1")
            self._color_cache[cache_key] = result
            return result

        except Exception as e:
            return False, f"Error calculating contrast: {str(e)}"

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to RGB values."""
        hex_color = hex_color.lstrip("#")

        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])

        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        return (r, g, b)

    def _relative_luminance(self, rgb: Tuple[float, float, float]) -> float:
        """Calculate relative luminance for a color."""
        r, g, b = rgb

        # Apply gamma correction
        def gamma_correct(channel: float) -> float:
            if channel <= 0.03928:
                return channel / 12.92
            else:
                return float(((channel + 0.055) / 1.055) ** 2.4)

        r_corrected = gamma_correct(r)
        g_corrected = gamma_correct(g)
        b_corrected = gamma_correct(b)

        # Calculate luminance
        return 0.2126 * r_corrected + 0.7152 * g_corrected + 0.0722 * b_corrected

    def validate_aria_attributes(self, element: str, attributes: Dict[str, str]) -> List[str]:
        """Validate ARIA attributes for an element.

        Args:
            element: The HTML element type
            attributes: Dictionary of ARIA attributes

        Returns:
            List of validation errors
        """
        errors = []

        # Check for required ARIA attributes based on element type
        if (
            element in ["button", "a"]
            and "aria-label" not in attributes
            and "aria-labelledby" not in attributes
        ):
            if not attributes.get("title") and not attributes.get("alt"):
                errors.append(
                    f"{element} should have aria-label, aria-labelledby, or descriptive text"
                )

        # Check for valid ARIA roles
        if "role" in attributes:
            valid_roles = [
                "button",
                "link",
                "checkbox",
                "radio",
                "tab",
                "tabpanel",
                "dialog",
                "alert",
                "status",
                "progressbar",
                "textbox",
                "combobox",
                "listbox",
                "option",
                "menuitem",
                "menu",
                "tooltip",
                "banner",
                "navigation",
                "main",
                "contentinfo",
                "complementary",
                "region",
                "application",
                "document",
                "img",
                "figure",
                "caption",
                "table",
                "row",
                "cell",
            ]

            if attributes["role"] not in valid_roles:
                errors.append(f"Invalid ARIA role: {attributes['role']}")

        # Check for proper ARIA relationships
        if "aria-describedby" in attributes:
            # Should reference an existing element ID
            described_by_id = attributes["aria-describedby"]
            if not described_by_id or not described_by_id.startswith("#"):
                errors.append("aria-describedby should reference an element ID")

        return errors

    def validate_keyboard_navigation(self, component_type: str) -> List[str]:
        """Validate keyboard navigation support for a component type.

        Args:
            component_type: Type of UI component

        Returns:
            List of accessibility recommendations
        """
        recommendations = []

        # General keyboard navigation requirements
        if component_type in ["form", "dialog", "modal"]:
            recommendations.append("Ensure Tab order includes all interactive elements")
            recommendations.append("Provide Escape key to close/cancel")
            recommendations.append("Ensure focus is trapped within the component")

        if component_type in ["tabs", "accordion", "menu"]:
            recommendations.append("Provide arrow key navigation")
            recommendations.append("Ensure Enter/Space activates items")
            recommendations.append("Provide Home/End key support")

        if component_type in ["table", "list"]:
            recommendations.append("Provide arrow key navigation between items")
            recommendations.append("Ensure Enter activates items")
            recommendations.append("Provide Ctrl+Home/Ctrl+End for first/last item")

        return recommendations

    def generate_alt_text(self, image_type: str, context: Dict[str, Any]) -> str:
        """Generate appropriate alt text for images.

        Args:
            image_type: Type of image (chart, diagram, icon, etc.)
            context: Context information about the image

        Returns:
            Generated alt text
        """
        if image_type == "knowledge_graph":
            entity_count = context.get("entity_count", 0)
            relation_count = context.get("relation_count", 0)
            return f"Knowledge graph visualization showing {entity_count} entities and {relation_count} relationships"

        elif image_type == "metrics_chart":
            metrics = context.get("metrics", {})
            return f"Performance metrics chart showing CPU usage at {metrics.get('cpu_percent', 0):.1f}%, memory usage at {metrics.get('memory_percent', 0):.1f}%"

        elif image_type == "progress_indicator":
            progress = context.get("progress", 0)
            return f"Progress indicator showing {progress:.1%} completion"

        elif image_type == "icon":
            icon_type = context.get("icon_type", "generic")
            return f"Icon representing {icon_type}"

        else:
            return "Image visualization"

    def validate_semantic_structure(self, html_content: str) -> List[str]:
        """Validate semantic HTML structure.

        Args:
            html_content: HTML content to validate

        Returns:
            List of semantic structure issues
        """
        issues = []

        # Check for proper heading hierarchy
        heading_pattern = r"<h([1-6])[^>]*>(.*?)</h\1>"
        headings = re.findall(heading_pattern, html_content, re.IGNORECASE | re.DOTALL)

        if headings:
            prev_level = 0
            for level, content in headings:
                current_level = int(level)
                if current_level > prev_level + 1 and prev_level > 0:
                    issues.append(f"Heading level jump from h{prev_level} to h{current_level}")

                # Check for empty headings
                if not content.strip():
                    issues.append("Empty heading found")

                prev_level = current_level

        # Check for proper landmark usage
        landmarks = ["main", "nav", "aside", "header", "footer", "section", "article"]
        for landmark in landmarks:
            if f"<{landmark}" in html_content.lower():
                # Check if landmark has proper labeling
                if (
                    "aria-label" not in html_content.lower()
                    and "aria-labelledby" not in html_content.lower()
                ):
                    issues.append(
                        f"Landmark element <{landmark}> should have aria-label or aria-labelledby"
                    )

        # Check for form labels
        input_pattern = r'<input[^>]*type="([^"]*)"[^>]*>'
        inputs = re.findall(input_pattern, html_content, re.IGNORECASE)

        for input_type in inputs:
            if input_type not in ["submit", "button", "hidden"]:
                # Check for associated label or aria-label
                if (
                    "aria-label" not in html_content.lower()
                    and "<label" not in html_content.lower()
                ):
                    issues.append(f"Input of type '{input_type}' should have a label or aria-label")

        return issues


class AccessibilityEnhancer:
    """Provides accessibility enhancements for UI components."""

    def __init__(self) -> None:
        """Initialize the accessibility enhancer."""
        self._validator = AccessibilityValidator()

    def enhance_button(self, label: str, **kwargs: Any) -> Any:
        """Enhance a button with accessibility features."""
        # Add ARIA attributes if not present
        if "aria-label" not in kwargs and "aria-labelledby" not in kwargs:
            kwargs["aria-label"] = f"Button: {label}"

        # Add keyboard support hints
        if "help" not in kwargs:
            kwargs["help"] = "Press Enter or Space to activate"

        return st.button(label, **kwargs)

    def enhance_text_input(self, label: str, **kwargs: Any) -> Any:
        """Enhance a text input with accessibility features."""
        # Add ARIA attributes
        if "aria-label" not in kwargs and "aria-labelledby" not in kwargs:
            kwargs["aria-label"] = f"Text input: {label}"

        # Add placeholder as help text if not present
        if "placeholder" in kwargs and "help" not in kwargs:
            kwargs["help"] = f"Enter {kwargs['placeholder'].lower()}"

        return st.text_input(label, **kwargs)

    def enhance_selectbox(self, label: str, options: List[str], **kwargs: Any) -> Any:
        """Enhance a selectbox with accessibility features."""
        if "aria-label" not in kwargs and "aria-labelledby" not in kwargs:
            kwargs["aria-label"] = f"Select: {label}"

        if "help" not in kwargs:
            kwargs["help"] = f"Choose from {len(options)} options"

        return st.selectbox(label, options, **kwargs)

    def enhance_tabs(self, tab_names: List[str], **kwargs: Any) -> Any:
        """Enhance tabs with accessibility features."""
        if "aria-label" not in kwargs:
            kwargs["aria-label"] = "Navigation tabs"

        return st.tabs(tab_names, **kwargs)

    def create_accessible_chart(self, chart_data: Dict[str, Any], chart_type: str = "line") -> None:
        """Create an accessible chart with proper alt text and descriptions."""
        # Generate alt text based on chart type and data
        alt_text = self._generate_chart_alt_text(chart_data, chart_type)

        # Display alt text for screen readers
        st.markdown(
            f'<div aria-label="Chart: {alt_text}" role="img"></div>', unsafe_allow_html=True
        )

        # This would integrate with actual charting library
        # For now, just show the alt text
        st.info(f"Chart visualization: {alt_text}")

    def _generate_chart_alt_text(self, data: Dict[str, Any], chart_type: str) -> str:
        """Generate alt text for chart data."""
        if chart_type == "line":
            # For time series data
            if "time" in data and "cpu" in data and "memory" in data:
                return f"Line chart showing CPU usage over time, currently at {data['cpu'][-1]:.1f}%, and memory usage at {data['memory'][-1]:.1f}%"
        elif chart_type == "bar":
            # For categorical data
            if "categories" in data and "values" in data:
                return f"Bar chart with {len(data['categories'])} categories, highest value is {max(data['values'])}"

        return "Chart visualization of performance metrics"

    def create_skip_link(self, target_id: str, text: str = "Skip to main content") -> None:
        """Create a skip link for keyboard navigation."""
        st.markdown(
            f'<a href="#{target_id}" class="skip-link">{text}</a>',
            unsafe_allow_html=True,
        )

    def announce_to_screen_reader(self, message: str) -> None:
        """Announce a message to screen readers."""
        st.markdown(
            f'<div aria-live="polite" aria-atomic="true" class="sr-only">{message}</div>',
            unsafe_allow_html=True,
        )

    def create_aria_landmark(self, landmark_type: str, label: str, content: Any) -> None:
        """Create a semantic landmark with proper ARIA labeling."""
        st.markdown(
            f'<div role="{landmark_type}" aria-label="{label}">',
            unsafe_allow_html=True,
        )

        # Render the content
        if callable(content):
            content()
        else:
            st.write(content)

        st.markdown("</div>", unsafe_allow_html=True)


def apply_comprehensive_accessibility() -> None:
    """Apply comprehensive accessibility enhancements to the entire application."""
    # Add global accessibility CSS
    st.markdown(
        """
        <style>
        /* Enhanced focus indicators */
        *:focus {
            outline: 3px solid #ffbf00 !important;
            outline-offset: 2px !important;
        }

        /* Screen reader only content */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        /* Skip links */
        .skip-link {
            position: absolute;
            left: -1000px;
            top: auto;
            width: 1px;
            height: 1px;
            overflow: hidden;
            z-index: 1000;
        }

        .skip-link:focus {
            left: 1rem;
            top: 1rem;
            width: auto;
            height: auto;
            background: #fff;
            color: #000;
            padding: 0.5rem;
            border: 2px solid #000;
            text-decoration: none;
            font-weight: bold;
        }

        /* High contrast mode */
        @media (prefers-contrast: high) {
            * {
                border-color: #000 !important;
            }
            .stButton>button {
                border-width: 2px !important;
            }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* Focus trap for modals */
        .modal-focus-trap {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9998;
        }

        /* Accessible form styling */
        .accessible-form {
            border: 2px solid transparent;
            padding: 1rem;
            border-radius: 0.5rem;
        }

        .accessible-form:focus-within {
            border-color: #ffbf00;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Add ARIA live region for dynamic content
    st.markdown(
        '<div id="aria-live-region" aria-live="polite" aria-atomic="true" class="sr-only"></div>',
        unsafe_allow_html=True,
    )


def validate_current_accessibility() -> Dict[str, Any]:
    """Validate current accessibility state and return recommendations."""
    validator = AccessibilityValidator()
    issues = []

    # Check color contrast for common color combinations
    common_colors = [
        ("#000000", "#ffffff"),  # Black on white
        ("#ffffff", "#000000"),  # White on black
        ("#0066cc", "#ffffff"),  # Blue on white
        ("#28a745", "#ffffff"),  # Green on white
        ("#dc3545", "#ffffff"),  # Red on white
    ]

    for fg, bg in common_colors:
        is_compliant, ratio = validator.validate_color_contrast(fg, bg)
        if not is_compliant:
            issues.append(f"Color combination {fg} on {bg} fails WCAG AA (ratio: {ratio})")

    # Check for keyboard navigation support
    keyboard_issues = validator.validate_keyboard_navigation("main_app")
    issues.extend(keyboard_issues)

    return {
        "is_compliant": len(issues) == 0,
        "issues": issues,
        "recommendations": [
            "Ensure all interactive elements are keyboard accessible",
            "Provide meaningful alt text for all images",
            "Use proper heading hierarchy (h1, h2, h3, etc.)",
            "Add ARIA labels to form controls",
            "Test with screen reader software",
            "Provide skip links for keyboard users",
            "Ensure sufficient color contrast ratios",
            "Add focus indicators for all interactive elements",
        ],
    }
