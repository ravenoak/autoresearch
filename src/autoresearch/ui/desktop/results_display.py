"""
Results display component for the PySide6 desktop interface.

Displays query results in a tabbed interface with support for:
- Markdown-formatted answers
- Knowledge graph visualization
- Agent reasoning traces
- Performance metrics
- Citation management
"""

from __future__ import annotations

import re
from html import escape
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from markdown import markdown as markdown_to_html
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .knowledge_graph_view import KnowledgeGraphView
from .metrics_dashboard import MetricsDashboard

try:
    from ...models import QueryResponse
    from ...output_format import OutputFormatter, OutputDepth
except ImportError:
    # For standalone development
    QueryResponse = None
    OutputFormatter = None
    OutputDepth = None


class ResultsDisplay(QWidget):
    """
    Tabbed results display for query responses.

    Provides multiple views of the same query result:
    - Answer tab with formatted response
    - Knowledge Graph tab with interactive visualization
    - Trace tab with step-by-step reasoning
    - Metrics tab with performance data
    """

    def __init__(self) -> None:
        """Initialize the results display."""
        super().__init__()

        # UI components
        self.tab_widget: Optional[QTabWidget] = None
        self.answer_view: Optional[QWebEngineView] = None
        self.knowledge_graph_view: Optional[KnowledgeGraphView] = None
        self.trace_view: Optional[QTextEdit] = None
        self.metrics_dashboard: Optional[MetricsDashboard] = None
        self.citations_list: Optional[QListWidget] = None
        self.citations_placeholder: Optional[QLabel] = None
        self.open_source_button: Optional[QPushButton] = None
        self.copy_source_button: Optional[QPushButton] = None

        # Current result
        self.current_result: Optional[QueryResponse] = None

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Answer tab
        self.answer_view = QWebEngineView()
        answer_tab = QWidget()
        answer_layout = QVBoxLayout(answer_tab)
        answer_layout.addWidget(self.answer_view)
        self.tab_widget.addTab(answer_tab, "Answer")

        # Citations tab
        citations_tab = QWidget()
        citations_layout = QVBoxLayout(citations_tab)
        self.citations_list = QListWidget()
        self.citations_list.setSelectionMode(QListWidget.SingleSelection)
        self.citations_list.currentItemChanged.connect(self._update_citation_controls)
        citations_layout.addWidget(self.citations_list)

        placeholder = QLabel("No citations available.")
        placeholder.setWordWrap(True)
        placeholder.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        citations_layout.addWidget(placeholder)
        self.citations_placeholder = placeholder

        controls_layout = QHBoxLayout()
        open_button = QPushButton("Open Source")
        open_button.setEnabled(False)
        open_button.clicked.connect(self._open_selected_citation)
        controls_layout.addWidget(open_button)
        self.open_source_button = open_button

        copy_button = QPushButton("Copy Citation")
        copy_button.setEnabled(False)
        copy_button.clicked.connect(self._copy_selected_citation)
        controls_layout.addWidget(copy_button)
        self.copy_source_button = copy_button

        controls_layout.addStretch(1)
        citations_layout.addLayout(controls_layout)

        self.tab_widget.addTab(citations_tab, "Citations")

        # Knowledge Graph tab
        self.knowledge_graph_view = KnowledgeGraphView()
        kg_tab = QWidget()
        kg_layout = QVBoxLayout(kg_tab)
        kg_layout.addWidget(self.knowledge_graph_view)

        self.tab_widget.addTab(kg_tab, "Knowledge Graph")

        # Agent Trace tab
        self.trace_view = QTextEdit()
        self.trace_view.setReadOnly(True)
        self.trace_view.setFontFamily("Monospace")
        trace_tab = QWidget()
        trace_layout = QVBoxLayout(trace_tab)
        trace_layout.addWidget(self.trace_view)
        self.tab_widget.addTab(trace_tab, "Agent Trace")

        # Metrics tab
        self.metrics_dashboard = MetricsDashboard()
        metrics_tab = QWidget()
        metrics_layout = QVBoxLayout(metrics_tab)
        metrics_layout.addWidget(self.metrics_dashboard)
        self.tab_widget.addTab(metrics_tab, "Metrics")

        layout.addWidget(self.tab_widget)

    def display_results(self, result: QueryResponse) -> None:
        """Display query results in all tabs."""
        self.current_result = result

        # Display answer
        self.display_answer(result)

        # Display citations
        self.display_citations(result)

        # Display knowledge graph (placeholder for now)
        self.display_knowledge_graph(result)

        # Display agent trace
        self.display_trace(result)

        # Display metrics
        self.display_metrics(result)

    def display_answer(self, result: QueryResponse) -> None:
        """Display the main answer in Markdown format."""
        if not self.answer_view or not OutputFormatter:
            return

        try:
            # Format as Markdown
            markdown_content = OutputFormatter.render(result, "markdown", depth="standard")

            # Create HTML with styling
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: none;
                        margin: 0;
                        padding: 20px;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
                    h2 {{ font-size: 1.5em; }}
                    p {{ margin-bottom: 1em; }}
                    code {{
                        background-color: #f8f8f8;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        background-color: #f8f8f8;
                        padding: 1em;
                        border-radius: 5px;
                        overflow-x: auto;
                        margin: 1em 0;
                    }}
                    blockquote {{
                        border-left: 4px solid #ddd;
                        padding-left: 1em;
                        margin: 1em 0;
                        color: #666;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1em 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f5f5;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                {self.render_markdown(markdown_content)}
            </body>
            </html>
            """

            self.answer_view.setHtml(html_content)

        except Exception as e:
            error_html = f"""
            <html>
            <body style="font-family: sans-serif; color: #d32f2f; padding: 20px;">
                <h2>Error Displaying Results</h2>
                <p>Failed to format query results: {str(e)}</p>
            </body>
            </html>
            """
            self.answer_view.setHtml(error_html)

    def display_citations(self, result: QueryResponse) -> None:
        """Display citation entries and enable source management controls."""
        if not self.citations_list or not self.citations_placeholder:
            return

        self.citations_list.clear()

        citations = getattr(result, "citations", None)
        if not citations:
            self.citations_placeholder.setText("No citations available.")
            self.citations_placeholder.show()
            self._update_citation_controls()
            return

        self.citations_placeholder.hide()

        for citation in citations:
            label, url = self._normalize_citation(citation)
            item = QListWidgetItem(label or "Citation")
            item.setData(Qt.UserRole, {"url": url, "raw": citation, "text": label})
            self.citations_list.addItem(item)

        self.citations_list.setCurrentRow(0)
        self._update_citation_controls()

    def display_knowledge_graph(self, result: QueryResponse) -> None:
        """Display knowledge graph visualization."""
        if not self.knowledge_graph_view:
            return

        graph_payload: Mapping[str, object] | None = None

        if hasattr(result, "knowledge_graph"):
            candidate = getattr(result, "knowledge_graph")
            if isinstance(candidate, Mapping):
                graph_payload = candidate

        if graph_payload is None and hasattr(result, "metrics"):
            metrics = getattr(result, "metrics")
            if isinstance(metrics, Mapping):
                knowledge_metrics = metrics.get("knowledge_graph")
                if isinstance(knowledge_metrics, Mapping):
                    graph_candidate = knowledge_metrics.get("graph")
                    if isinstance(graph_candidate, Mapping):
                        graph_payload = graph_candidate
                    else:
                        data_candidate = knowledge_metrics.get("data")
                        if isinstance(data_candidate, Mapping):
                            graph_payload = data_candidate

        if graph_payload:
            self.knowledge_graph_view.set_graph_data(graph_payload)
        else:
            self.knowledge_graph_view.clear()

    def display_trace(self, result: QueryResponse) -> None:
        """Display agent reasoning trace."""
        if not self.trace_view:
            return

        trace_text = "Agent Reasoning Trace:\n\n"

        if hasattr(result, 'reasoning') and result.reasoning:
            for i, step in enumerate(result.reasoning, 1):
                trace_text += f"Step {i}:\n{step}\n\n"
        else:
            trace_text += "No reasoning steps available.\n"

        # Add metrics if available
        if hasattr(result, 'metrics') and result.metrics:
            trace_text += "\nQuery Metrics:\n"
            for key, value in result.metrics.items():
                trace_text += f"  {key}: {value}\n"

        self.trace_view.setPlainText(trace_text)

    def display_metrics(self, result: QueryResponse) -> None:
        """Display performance metrics."""
        if not self.metrics_dashboard:
            return

        metrics = getattr(result, "metrics", None)
        if isinstance(metrics, Mapping):
            self.metrics_dashboard.update_metrics(metrics)
        else:
            self.metrics_dashboard.clear()

    def render_markdown(self, markdown_text: str) -> str:
        """Convert Markdown into sanitized HTML suitable for web rendering."""
        if not markdown_text:
            return ""

        sanitized_source = escape(markdown_text, quote=False)
        html_output = markdown_to_html(
            sanitized_source,
            extensions=[
                "extra",
                "sane_lists",
                "smarty",
            ],
            output_format="html5",
        )
        return self._sanitize_links(html_output)

    def _sanitize_links(self, html_content: str) -> str:
        """Ensure anchor tags only contain safe URLs."""

        def replacer(match: re.Match[str]) -> str:
            href = match.group(1)
            text = match.group(2)
            safe_href = self._validate_url(href)
            if not safe_href:
                return text
            return f'<a href="{safe_href}" rel="noopener noreferrer">{text}</a>'

        return re.sub(
            r'<a\s+href="([^"]+)">(.*?)</a>',
            replacer,
            html_content,
            flags=re.IGNORECASE | re.DOTALL,
        )

    def _validate_url(self, candidate: Optional[str]) -> Optional[str]:
        """Return a safe URL if the candidate points to http(s), otherwise None."""
        if not candidate:
            return None

        parsed = urlparse(candidate)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return candidate
        return None

    def _normalize_citation(self, citation: Any) -> tuple[str, Optional[str]]:
        """Normalize a citation entry to label and optional URL."""
        if isinstance(citation, Mapping):
            url = citation.get("url") or citation.get("href") or citation.get("source")
            label = citation.get("title") or citation.get("label") or citation.get("text")
            if url and not label:
                label = url
            return str(label or ""), self._validate_url(str(url)) if url else None

        if isinstance(citation, str):
            url = self._extract_url(citation)
            return citation.strip(), url

        return str(citation), None

    def _extract_url(self, value: str) -> Optional[str]:
        """Extract the first valid URL from a citation string."""
        url_match = re.search(r"https?://[^\s]+", value or "")
        if not url_match:
            return None
        candidate = url_match.group(0).rstrip(".,);")
        return self._validate_url(candidate)

    def _open_selected_citation(self) -> None:
        """Open the currently selected citation in the system browser."""
        if not self.citations_list:
            return

        current_item = self.citations_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.UserRole) or {}
        url = data.get("url")
        if isinstance(url, str):
            QDesktopServices.openUrl(QUrl(url))

    def _copy_selected_citation(self) -> None:
        """Copy the currently selected citation to the clipboard."""
        if not self.citations_list:
            return

        current_item = self.citations_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.UserRole) or {}
        text = data.get("text") or current_item.text()
        clipboard = QGuiApplication.clipboard()
        if clipboard and isinstance(text, str):
            clipboard.setText(text)

    def _update_citation_controls(self) -> None:
        """Enable or disable citation management buttons based on selection."""
        if not self.citations_list:
            return

        current_item = self.citations_list.currentItem()
        data = current_item.data(Qt.UserRole) if current_item else None
        has_url = isinstance(data, dict) and isinstance(data.get("url"), str)
        has_text = isinstance(data, dict) and bool(data.get("text"))

        if self.open_source_button:
            self.open_source_button.setEnabled(bool(current_item) and has_url)
        if self.copy_source_button:
            self.copy_source_button.setEnabled(bool(current_item) and has_text)

        if self.citations_placeholder and self.citations_list.count() == 0:
            self.citations_placeholder.show()
        elif self.citations_placeholder:
            self.citations_placeholder.hide()
