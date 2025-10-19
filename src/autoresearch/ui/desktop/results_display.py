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

from typing import Mapping, Optional

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget

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
                {self.markdown_to_html(markdown_content)}
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

    def markdown_to_html(self, markdown: str) -> str:
        """Convert basic Markdown to HTML (simplified implementation)."""
        if not markdown:
            return ""

        # This is a very basic Markdown converter
        # In a full implementation, you'd use a proper library like markdown
        html = markdown

        # Headers
        html = html.replace("### ", "</p><h3>").replace("## ", "</p><h2>").replace("# ", "</p><h1>")
        html = f"<p>{html}</p>"

        # Bold and italic (basic)
        html = html.replace("**", "<strong>").replace("**", "</strong>")
        html = html.replace("*", "<em>").replace("*", "</em>")

        # Lists (basic)
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('- '):
                lines[i] = f"<li>{line.strip()[2:]}</li>"
            elif line.strip().startswith('* '):
                lines[i] = f"<li>{line.strip()[2:]}</li>"

        html = '\n'.join(lines)

        # Wrap in ul if we have list items
        if '<li>' in html:
            # Find the start and end of list items
            start_idx = html.find('<li>')
            end_idx = html.rfind('</li>') + 5
            list_content = html[start_idx:end_idx]
            html = html[:start_idx] + f"<ul>{list_content}</ul>" + html[end_idx:]

        return html
