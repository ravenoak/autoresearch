"""Results display component with progressive disclosure and accessibility.

This module provides a sophisticated results display interface that handles:
- Progressive disclosure with depth controls
- Multiple result tabs (answer, citations, reasoning, etc.)
- Export functionality
- Accessibility features
- Knowledge graph visualization
- Claim verification interface
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping, cast

from ...models import QueryResponse
from ...output_format import OutputDepth, OutputFormatter
from ..provenance import (
    audit_status_rollup,
    depth_sequence,
    section_toggle_defaults,
)

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

        st = cast(Any, MockStreamlit())


class ResultsDisplayComponent:
    """Handles the display of query results with progressive disclosure."""

    def __init__(self) -> None:
        """Initialize the results display component."""
        self._depth_options = depth_sequence()
        self._toggle_widget = getattr(
            st, "toggle", lambda label, **kwargs: st.checkbox(label, **kwargs)
        )

    def render(self, result: QueryResponse) -> None:
        """Render the complete results display.

        Args:
            result: The query response to display
        """
        st.session_state.current_result = result
        if hasattr(result, "state_id") and result.state_id:
            st.session_state.current_state_id = result.state_id

        # Handle reverify notice
        notice = st.session_state.pop("reverify_notice", None)
        if notice:
            st.success(notice)

        # Depth selection controls
        self._render_depth_controls(result)

        # Main results display
        self._render_results_content(result)

    def _render_depth_controls(self, result: QueryResponse) -> None:
        """Render depth selection and toggle controls."""
        depth_values = [depth.value for depth in self._depth_options]
        stored_depth = st.session_state.get("ui_depth", OutputDepth.STANDARD.value)

        try:
            default_index = depth_values.index(stored_depth)
        except ValueError:
            default_index = depth_values.index(OutputDepth.STANDARD.value)

        selected_value = st.radio(
            "Detail depth",
            depth_values,
            index=default_index,
            format_func=lambda val: OutputDepth(val).label,
            horizontal=True,
            help="Choose how much detail to display, from TL;DR to full trace.",
        )

        selected_depth = OutputDepth(selected_value)
        st.session_state.ui_depth = selected_depth.value

        # Prepare payload for the selected depth
        payload = OutputFormatter.plan_response_depth(result, selected_depth)
        st.session_state.current_payload = payload
        if payload.state_id:
            st.session_state.current_state_id = payload.state_id

        # Set up toggle defaults for this depth
        self._setup_toggle_defaults(payload, selected_depth)

        # Render toggle controls
        self._render_toggle_controls(payload)

    def _setup_toggle_defaults(self, payload: Any, depth: OutputDepth) -> None:
        """Set up default toggle states for the current depth."""
        toggle_defaults = section_toggle_defaults(payload)
        depth_state_key = "last_selected_depth"

        if st.session_state.get(depth_state_key) != depth.value:
            for name, config in toggle_defaults.items():
                st.session_state[f"ui_toggle_{name}"] = (
                    config["value"] if config["available"] else False
                )
            st.session_state[depth_state_key] = depth.value

    def _render_toggle_controls(self, payload: Any) -> None:
        """Render section toggle controls."""
        toggle_defaults = section_toggle_defaults(payload)
        toggle_definitions = self._get_toggle_definitions()

        st.markdown("#### Depth controls")
        toggle_columns = st.columns(len(toggle_definitions))

        for column, (name, label, help_text) in zip(toggle_columns, toggle_definitions):
            config = toggle_defaults[name]
            state_key = f"ui_toggle_{name}"

            if state_key not in st.session_state:
                st.session_state[state_key] = config["value"] if config["available"] else False

            if not config["available"]:
                st.session_state[state_key] = False

            with column:
                self._toggle_widget(
                    label,
                    value=st.session_state[state_key],
                    help=help_text,
                    disabled=not config["available"],
                    key=state_key,
                )

        # Get toggle states
        toggle_states = self._get_toggle_states(toggle_defaults)

        # Handle graph exports if enabled
        if toggle_states.get("graph_exports"):
            self._handle_graph_exports(payload, payload)

    def _get_toggle_definitions(self) -> List[tuple[str, str, str]]:
        """Get toggle control definitions."""
        return [
            ("tldr", "Show TL;DR", "Display the auto-generated summary."),
            ("key_findings", "Show key findings", "Highlight the main evidence-backed points."),
            ("claim_audits", "Show claim table", "Inspect verification outcomes for each claim."),
            ("full_trace", "Show full trace", "Reveal reasoning steps and ReAct traces."),
            (
                "knowledge_graph",
                "Show knowledge graph",
                "Preview knowledge graph metrics and contradictions.",
            ),
            (
                "graph_exports",
                "Enable graph exports",
                "Expose download links for GraphML and JSON exports.",
            ),
        ]

    def _get_toggle_states(self, toggle_defaults: Dict[str, Dict[str, bool]]) -> Dict[str, bool]:
        """Get current toggle states."""
        return {
            name: st.session_state.get(f"ui_toggle_{name}", False)
            for name in [
                "tldr",
                "key_findings",
                "claim_audits",
                "full_trace",
                "knowledge_graph",
                "graph_exports",
            ]
        }

    def _handle_graph_exports(self, payload: Any, result: QueryResponse) -> None:
        """Handle graph export functionality."""
        available_formats = [fmt for fmt, available in payload.graph_exports.items() if available]

        if available_formats:
            payload = OutputFormatter.plan_response_depth(
                result,
                OutputDepth(st.session_state.ui_depth),
                graph_export_formats=available_formats,
                prefetch_graph_exports=True,
            )
            st.session_state.current_payload = payload

    def _render_results_content(self, result: QueryResponse) -> None:
        """Render the main results content with tabs."""
        toggle_states = self._get_toggle_states({})

        st.markdown(
            "<div role='region' aria-label='Query results' aria-live='polite'>",
            unsafe_allow_html=True,
        )

        # TL;DR section
        self._render_tldr_section(toggle_states)

        # Answer section
        self._render_answer_section(result)

        # Key findings section
        self._render_key_findings_section(toggle_states)

        # Export buttons
        self._render_export_section(result)

        # Main tabs
        self._render_main_tabs(result, toggle_states)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_tldr_section(self, toggle_states: Dict[str, bool]) -> None:
        """Render the TL;DR section."""
        st.markdown("<h2 class='subheader'>TL;DR</h2>", unsafe_allow_html=True)

        payload = st.session_state.get("current_payload", {})
        tldr_available = toggle_states.get("tldr", True)

        if tldr_available and payload.get("tldr"):
            st.write(payload["tldr"])
        elif tldr_available:
            st.info("No summary available.")
        elif payload.get("notes", {}).get("tldr"):
            st.info(payload["notes"]["tldr"])
        else:
            st.caption("Enable 'Show TL;DR' to surface the summary.")

    def _render_answer_section(self, result: QueryResponse) -> None:
        """Render the main answer section."""
        st.markdown("<h2 class='subheader'>Answer</h2>", unsafe_allow_html=True)

        payload = st.session_state.get("current_payload", {})
        st.markdown(payload.get("answer", "No answer available."), unsafe_allow_html=True)

    def _render_key_findings_section(self, toggle_states: Dict[str, bool]) -> None:
        """Render the key findings section."""
        st.markdown("<h3>Key Findings</h3>", unsafe_allow_html=True)

        payload = st.session_state.get("current_payload", {})
        key_findings_available = toggle_states.get("key_findings", False)

        if key_findings_available:
            if payload.get("key_findings"):
                for finding in payload["key_findings"]:
                    st.markdown(f"- {finding}")
            else:
                st.info("No key findings available.")

            if note := payload.get("notes", {}).get("key_findings"):
                st.caption(note)
        elif payload.get("notes", {}).get("key_findings"):
            st.info(payload["notes"]["key_findings"])
        else:
            st.caption("Enable 'Show key findings' to review highlights.")

    def _render_export_section(self, result: QueryResponse) -> None:
        """Render export functionality."""
        col1, col2 = st.columns(2)

        with col1:
            markdown_result = self._format_result_as_markdown(result)
            st.download_button(
                label="Export as Markdown",
                data=markdown_result,
                file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )

        with col2:
            json_result = self._format_result_as_json(result)
            st.download_button(
                label="Export as JSON",
                data=json_result,
                file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    def _render_main_tabs(self, result: QueryResponse, toggle_states: Dict[str, bool]) -> None:
        """Render the main results tabs."""
        tab_names = ["Citations", "Reasoning", "Provenance", "Metrics", "Knowledge Graph", "Trace"]
        tabs = st.tabs(tab_names)

        payload = st.session_state.get("current_payload", {})

        with tabs[0]:  # Citations
            self._render_citations_tab(payload)

        with tabs[1]:  # Reasoning
            self._render_reasoning_tab(payload, toggle_states)

        with tabs[2]:  # Provenance
            self._render_provenance_tab(result, payload, toggle_states)

        with tabs[3]:  # Metrics
            self._render_metrics_tab(payload)

        with tabs[4]:  # Knowledge Graph
            self._render_knowledge_graph_tab(result, payload, toggle_states)

        with tabs[5]:  # Trace
            self._render_trace_tab(payload, toggle_states)

    def _render_citations_tab(self, payload: Any) -> None:
        """Render the citations tab."""
        st.markdown("<h3>Citations</h3>", unsafe_allow_html=True)

        if payload.get("citations"):
            for citation in payload["citations"]:
                st.markdown(
                    f"<div class='citation' role='listitem'>{citation}</div>",
                    unsafe_allow_html=True,
                )
        elif note := payload.get("notes", {}).get("citations"):
            st.info(note)
        else:
            st.info("No citations provided")

    def _render_reasoning_tab(self, payload: Any, toggle_states: Dict[str, bool]) -> None:
        """Render the reasoning tab."""
        st.markdown("<h3>Reasoning</h3>", unsafe_allow_html=True)

        full_trace_available = toggle_states.get("full_trace", False)

        if full_trace_available:
            if payload.get("reasoning"):
                for idx, step in enumerate(payload["reasoning"], 1):
                    st.markdown(
                        f"<div class='reasoning-step' role='listitem'>{idx}. {step}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No reasoning steps provided")

            if note := payload.get("notes", {}).get("reasoning"):
                st.caption(note)
        elif payload.get("notes", {}).get("reasoning"):
            st.info(payload["notes"]["reasoning"])
        else:
            st.info("Enable 'Show full trace' to inspect agent reasoning.")

    def _render_provenance_tab(
        self, result: QueryResponse, payload: Any, toggle_states: Dict[str, bool]
    ) -> None:
        """Render the provenance tab with claim audits."""
        st.markdown("<h3>Claim Audits</h3>", unsafe_allow_html=True)

        claim_audits_available = toggle_states.get("claim_audits", False)

        if claim_audits_available:
            self._render_claim_audits(payload, result)
        elif payload.get("notes", {}).get("claim_audits"):
            st.info(payload["notes"]["claim_audits"])
        else:
            st.info("Enable 'Show claim table' to inspect verification details.")

    def _render_claim_audits(self, payload: Any, result: QueryResponse) -> None:
        """Render the claim audits interface."""
        if payload.get("claim_audits"):
            # Overview section
            self._render_claim_audit_overview(payload)

            # Detailed table
            self._render_claim_audit_table(payload)

            # Individual claim details
            self._render_claim_details(payload)

    def _render_claim_audit_overview(self, payload: Any) -> None:
        """Render claim audit overview with status rollup."""
        claim_audits_raw = payload.get("claim_audits", [])
        claim_audits = cast(List[Mapping[str, Any]], claim_audits_raw)
        rollup = audit_status_rollup(claim_audits)

        if rollup:
            st.markdown("**Claim status overview**")
            for status, count in rollup.items():
                st.markdown(
                    f"- {status.replace('_', ' ').title()}: {count}",
                    unsafe_allow_html=False,
                )
            st.caption(
                "Table columns map to claim ID, verification status, entailment score, "
                "and the top supporting snippet. Expand JSON export for full provenance."
            )

    def _render_claim_audit_table(self, payload: Any) -> None:
        """Render the claim audit table."""
        # Add CSS for the table
        st.markdown(
            """
            <style>
            .claim-audit-table {width:100%; border-collapse: collapse;}
            .claim-audit-table th, .claim-audit-table td {
                border: 1px solid rgba(151, 151, 151, 0.4);
                padding: 0.5rem;
            }
            .claim-audit-badge {
                border-radius: 0.5rem;
                padding: 0.25rem 0.6rem;
                color: #fff;
                font-size: 0.85rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        rows = []
        for audit in payload["claim_audits"]:
            status_raw = str(audit.get("status", "unknown")).lower()
            color = self._get_status_color(status_raw)
            badge = (
                f"<span class='claim-audit-badge' style='background-color:{color}'>"
                f"{status_raw.replace('_', ' ').title()}</span>"
            )
            entailment = audit.get("entailment_score")
            entailment_display = "—" if entailment is None else f"{entailment:.2f}"
            sources = audit.get("sources") or []
            primary = sources[0] if sources else {}
            label = primary.get("title") or primary.get("url") or primary.get("snippet") or ""
            if label and len(label) > 80:
                label = label[:77] + "..."

            rows.append(
                "<tr>"
                f"<td>{audit.get('claim_id', '')}</td>"
                f"<td>{badge}</td>"
                f"<td>{entailment_display}</td>"
                f"<td>{label}</td>"
                "</tr>"
            )

        table_html = (
            "<table class='claim-audit-table'>"
            "<thead><tr><th>Claim ID</th><th>Status</th><th>Entailment</th><th>Top Source</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

    def _render_claim_details(self, payload: Any) -> None:
        """Render individual claim details."""
        st.markdown("### Claim details", unsafe_allow_html=True)

        for index, audit in enumerate(payload["claim_audits"]):
            claim_id = str(audit.get("claim_id") or index + 1)
            toggle_key = f"ui_claim_details_{claim_id}_{index}"
            default_state = st.session_state.get(toggle_key, False)

            show_details = self._toggle_widget(
                f"Show details for claim {claim_id}",
                key=toggle_key,
                value=default_state,
                help="Reveal full provenance, notes, and Socratic follow-ups.",
            )

            if show_details:
                self._render_single_claim_details(audit)

    def _render_single_claim_details(self, audit: Dict[str, Any]) -> None:
        """Render details for a single claim."""
        status_label = str(audit.get("status", "unknown")).replace("_", " ").title()
        entailment_score = audit.get("entailment_score")
        entailment_display = "—" if entailment_score is None else f"{entailment_score:.2f}"

        st.markdown(f"- **Status:** {status_label}")
        st.markdown(f"- **Entailment:** {entailment_display}")

        if audit.get("notes"):
            st.markdown(f"- **Notes:** {audit['notes']}")

        sources = audit.get("sources") or []
        if sources:
            st.markdown("- **Sources:**")
            for source in sources:
                title = source.get("title") or source.get("url") or "Source"
                st.markdown(f"  - {title}")

        st.json(audit)

    def _get_status_color(self, status: str) -> str:
        """Get color for claim status badge."""
        colors = {
            "supported": "#0f5132",
            "unsupported": "#842029",
            "needs_review": "#664d03",
        }
        return colors.get(status, "#6c757d")

    def _render_metrics_tab(self, payload: Any) -> None:
        """Render the metrics tab."""
        st.markdown("<h3>Metrics</h3>", unsafe_allow_html=True)

        if payload.get("metrics"):
            with st.container():
                st.markdown(
                    "<div class='metrics-container' role='region' aria-label='Metrics'>",
                    unsafe_allow_html=True,
                )
                for key, value in payload["metrics"].items():
                    st.markdown(f"**{key}:** {value}")
                st.markdown("</div>", unsafe_allow_html=True)

            if note := payload.get("notes", {}).get("metrics"):
                st.caption(note)
        elif note := payload.get("notes", {}).get("metrics"):
            st.info(note)
        else:
            st.info("No metrics provided")

    def _render_knowledge_graph_tab(
        self, result: QueryResponse, payload: Any, toggle_states: Dict[str, bool]
    ) -> None:
        """Render the knowledge graph tab."""
        st.markdown("<h3>Knowledge Graph</h3>", unsafe_allow_html=True)

        knowledge_available = toggle_states.get("knowledge_graph", False)

        if knowledge_available:
            summary = payload.get("knowledge_graph", {})
            if summary:
                self._render_knowledge_graph_summary(summary, payload)
            else:
                st.info("Knowledge graph not generated yet.")

        # Graph visualization
        if (
            toggle_states.get("knowledge_graph")
            and payload.get("citations")
            and payload.get("reasoning")
        ):
            self._render_knowledge_graph_visualization(result)

        # Graph exports
        if toggle_states.get("graph_exports") and payload.get("graph_exports"):
            self._render_graph_exports(payload)

    def _render_knowledge_graph_summary(self, summary: Dict[str, Any], payload: Any) -> None:
        """Render knowledge graph summary."""
        counts_lines = []
        if (entities := summary.get("entity_count")) is not None:
            counts_lines.append(f"- **Entities:** {entities}")
        if (relations := summary.get("relation_count")) is not None:
            counts_lines.append(f"- **Relations:** {relations}")
        if (score := summary.get("contradiction_score")) is not None:
            counts_lines.append(f"- **Contradiction score:** {score:.2f}")

        if counts_lines:
            st.markdown("### Summary")
            st.markdown("\n".join(counts_lines))

        # Contradictions
        if contradictions := summary.get("contradictions"):
            self._render_contradictions(contradictions, payload)

        # Multi-hop paths
        if paths := summary.get("multi_hop_paths"):
            self._render_multi_hop_paths(paths, payload)

    def _render_contradictions(self, contradictions: List[Any], payload: Any) -> None:
        """Render knowledge graph contradictions."""
        st.markdown("### Contradictions")
        for item in contradictions:
            if isinstance(item, dict):
                subject = item.get("subject") or item.get("text")
                predicate = item.get("predicate")
                objects = item.get("objects") or []
                if subject and predicate and isinstance(objects, list):
                    joined = ", ".join(str(obj) for obj in objects if str(obj).strip())
                    st.markdown(f"- {subject} — {predicate} → {joined or '—'}")
                else:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"- {item}")

        if note := payload.get("notes", {}).get("knowledge_graph_contradictions"):
            st.caption(note)

    def _render_multi_hop_paths(self, paths: List[Any], payload: Any) -> None:
        """Render multi-hop paths."""
        st.markdown("### Multi-hop paths")
        for path in paths:
            if isinstance(path, list):
                labels = [str(node) for node in path if str(node).strip()]
                st.markdown(f"- {' → '.join(labels) if labels else '—'}")
            else:
                st.markdown(f"- {path}")

        if note := payload.get("notes", {}).get("knowledge_graph_paths"):
            st.caption(note)

    def _render_knowledge_graph_visualization(self, result: QueryResponse) -> None:
        """Render the knowledge graph visualization."""
        # This would need the actual graph creation logic from the original file
        # For now, just show a placeholder
        st.info("Knowledge graph visualization would be rendered here.")

    def _render_graph_exports(self, payload: Any) -> None:
        """Render graph export functionality."""
        st.markdown("### Graph exports")

        exports_data = payload.get("graph_export_payloads", {})
        if payload.get("graph_exports", {}).get("graphml"):
            graphml_data = exports_data.get("graphml")
            if graphml_data:
                st.download_button(
                    label="Download GraphML",
                    data=graphml_data,
                    file_name=f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.graphml",
                    mime="application/graphml+xml",
                )

        if payload.get("graph_exports", {}).get("graph_json"):
            graph_json_data = exports_data.get("graph_json")
            if graph_json_data:
                st.download_button(
                    label="Download Graph JSON",
                    data=graph_json_data,
                    file_name=f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

    def _render_trace_tab(self, payload: Any, toggle_states: Dict[str, bool]) -> None:
        """Render the trace tab."""
        st.markdown("<h3>Agent Trace</h3>", unsafe_allow_html=True)

        full_trace_available = toggle_states.get("full_trace", False)

        if full_trace_available:
            self._render_full_trace(payload)
        else:
            message = (
                payload.get("notes", {}).get("react_traces")
                or payload.get("notes", {}).get("reasoning")
                or "Increase depth to unlock detailed traces."
            )
            st.info(message)

    def _render_full_trace(self, payload: Any) -> None:
        """Render the full trace information."""
        if payload.get("reasoning"):
            # This would need the actual trace graph creation logic
            st.info("Agent trace visualization would be rendered here.")

        if payload.get("react_traces"):
            st.markdown("### ReAct events")
            st.json(payload["react_traces"])
        elif payload.get("notes", {}).get("react_traces"):
            st.info(payload["notes"]["react_traces"])
        elif not payload.get("react_traces"):
            st.caption("No ReAct events captured for this run.")

        # Progress metrics (placeholder)
        st.caption("Progress metrics visualization would be rendered here.")

    def _format_result_as_markdown(self, result: QueryResponse) -> str:
        """Format result as markdown."""
        depth = OutputDepth(st.session_state.get("ui_depth", OutputDepth.STANDARD.value))
        return OutputFormatter.render(result, "markdown", depth=depth)

    def _format_result_as_json(self, result: QueryResponse) -> str:
        """Format result as JSON."""
        depth = OutputDepth(st.session_state.get("ui_depth", OutputDepth.STANDARD.value))
        return OutputFormatter.render(result, "json", depth=depth)
