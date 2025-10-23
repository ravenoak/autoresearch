"""Live metrics dashboard for the desktop interface."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING, Any, Callable, Mapping

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:  # pragma: no cover - optional dependency import guard
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
except ImportError:  # pragma: no cover - handled via accessibility fallback
    FigureCanvasQTAgg = None  # type: ignore[assignment]
    Figure = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - static type checking only
    from matplotlib.backends.backend_qtagg import (  # noqa: F401
        FigureCanvasQTAgg as _FigureCanvasQTAgg,
    )
    from matplotlib.figure import Figure as _Figure  # noqa: F401


class MetricsDashboard(QWidget):
    """Display runtime metrics with live plots and accessible summaries."""

    _MAX_POINTS = 600

    def __init__(self) -> None:
        super().__init__()
        self._metrics: Mapping[str, Any] | None = None
        self._metrics_provider: Callable[[], Mapping[str, Any] | None] | None = None
        self._start_time: float | None = None
        self._timestamps: list[float] = []
        self._cpu_percent: list[float] = []
        self._memory_percent: list[float] = []
        self._token_counts: list[float] = []
        self._last_snapshot: dict[str, float | None] = {}

        self._title = QLabel("Runtime Metrics")
        self._title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._title.setObjectName("metrics-dashboard-title")

        self._toggle_button = QPushButton("Show Text Summary")
        self._toggle_button.setCheckable(True)
        self._toggle_button.setObjectName("metrics-dashboard-toggle")
        self._toggle_button.setAccessibleName("Toggle metrics chart and text summary")
        self._toggle_button.toggled.connect(self._handle_toggle)

        self._stack = QStackedWidget()
        self._stack.setObjectName("metrics-dashboard-stack")

        self._summary_label = QLabel("Metrics not available yet.")
        self._summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._summary_label.setWordWrap(True)
        self._summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._summary_label.setObjectName("metrics-summary")
        self._summary_label.setAccessibleDescription(
            "Textual summary of CPU, memory, and token usage over time."
        )

        self._chart_available = bool(FigureCanvasQTAgg and Figure)
        self._figure = None
        self._canvas = None
        self._chart_ax = None
        self._token_ax = None
        self._cpu_line = None
        self._memory_line = None
        self._token_line = None

        if self._chart_available:
            self._figure = Figure(figsize=(6.0, 3.5))
            self._chart_ax = self._figure.add_subplot(111)
            self._chart_ax.set_xlabel("Time (s)")
            self._chart_ax.set_ylabel("Usage (%)")
            self._chart_ax.set_title("Resource usage over time")
            self._chart_ax.grid(True, linestyle="--", alpha=0.3)
            self._token_ax = self._chart_ax.twinx()
            self._token_ax.set_ylabel("Tokens")

            self._cpu_line = self._chart_ax.plot(
                [], [], label="CPU %", color="#1f77b4"
            )[0]
            self._memory_line = self._chart_ax.plot(
                [], [], label="Memory %", color="#2ca02c"
            )[0]
            self._token_line = self._token_ax.plot(
                [], [], label="Tokens", color="#ff7f0e", linestyle="--"
            )[0]
            lines = [self._cpu_line, self._memory_line, self._token_line]
            labels = [line.get_label() for line in lines]
            self._chart_ax.legend(lines, labels, loc="upper left")

            self._canvas = FigureCanvasQTAgg(self._figure)  # type: ignore[misc]
            self._canvas.setObjectName("metrics-dashboard-canvas")
            self._stack.addWidget(self._canvas)
            self._stack.addWidget(self._summary_label)
            self._stack.setCurrentWidget(self._canvas)
            self._set_chart_defaults()
        else:
            self._toggle_button.setEnabled(False)
            self._toggle_button.setText("Charts unavailable")
            self._toggle_button.setAccessibleDescription(
                "Charts require matplotlib. Text summary is shown instead."
            )
            self._stack.addWidget(self._summary_label)
            self._stack.setCurrentWidget(self._summary_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._toggle_button)
        layout.addWidget(self._stack)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_metrics_provider)

        self._update_summary(no_data=True)

    def update_metrics(self, metrics: Mapping[str, Any] | None) -> None:
        """Update the dashboard with the provided metrics mapping.

        Args:
            metrics: Mapping of metric names to raw values collected from the
                orchestrator or monitoring subsystem.
        """

        self._metrics = metrics or {}
        if not metrics:
            self._update_summary(no_data=True)
            self._render_chart()
            return

        snapshot = self._extract_snapshot(self._metrics)
        if all(value is None for value in snapshot.values()):
            self._update_summary()
            return

        self._append_snapshot(snapshot)
        self._render_chart()
        self._update_summary()

    def bind_metrics_provider(
        self,
        provider: Callable[[], Mapping[str, Any] | None] | None,
        *,
        interval_ms: int = 1000,
    ) -> None:
        """Bind a provider callable that supplies live metrics.

        Args:
            provider: Callable that returns the latest metrics snapshot.
                Pass ``None`` to stop automatic refreshing.
            interval_ms: Polling interval for the provider in milliseconds.
        """

        if provider is None:
            self._metrics_provider = None
            self._timer.stop()
            self._update_summary()
            return

        self._metrics_provider = provider
        self._timer.setInterval(max(200, interval_ms))
        if not self._timer.isActive():
            self._timer.start()

    def clear(self) -> None:
        """Clear stored metrics and reset the visualization."""

        self._metrics = None
        self._timestamps.clear()
        self._cpu_percent.clear()
        self._memory_percent.clear()
        self._token_counts.clear()
        self._start_time = None
        self._last_snapshot = {}
        self._update_summary(no_data=True)
        self._render_chart()

    def _handle_toggle(self, checked: bool) -> None:
        if not self._chart_available or self._canvas is None:
            self._toggle_button.setChecked(False)
            self._stack.setCurrentWidget(self._summary_label)
            return

        if checked:
            self._toggle_button.setText("Show Chart")
            self._stack.setCurrentWidget(self._summary_label)
        else:
            self._toggle_button.setText("Show Text Summary")
            self._stack.setCurrentWidget(self._canvas)

    def _poll_metrics_provider(self) -> None:
        if self._metrics_provider is None:
            if self._timer.isActive():
                self._timer.stop()
            return

        metrics = self._metrics_provider()
        if metrics is None:
            self._update_summary()
            return

        self.update_metrics(metrics)

    def _append_snapshot(self, snapshot: Mapping[str, float | None]) -> None:
        now = time.monotonic()
        if self._start_time is None:
            self._start_time = now
        elapsed = now - self._start_time

        self._timestamps.append(elapsed)
        self._cpu_percent.append(self._to_series_value(snapshot.get("cpu_percent")))
        self._memory_percent.append(self._to_series_value(snapshot.get("memory_percent")))
        self._token_counts.append(self._to_series_value(snapshot.get("tokens_total")))
        self._last_snapshot = {
            "cpu_percent": snapshot.get("cpu_percent"),
            "memory_percent": snapshot.get("memory_percent"),
            "tokens_total": snapshot.get("tokens_total"),
        }

        self._trim_series()

    def _render_chart(self) -> None:
        if (
            not self._chart_available
            or self._canvas is None
            or self._chart_ax is None
            or self._token_ax is None
            or self._cpu_line is None
            or self._memory_line is None
            or self._token_line is None
        ):
            return

        if not self._timestamps:
            self._set_chart_defaults()
            return

        self._cpu_line.set_data(self._timestamps, self._cpu_percent)
        self._memory_line.set_data(self._timestamps, self._memory_percent)
        self._token_line.set_data(self._timestamps, self._token_counts)

        usage_vals = self._finite_values(self._cpu_percent + self._memory_percent)
        if usage_vals:
            upper = max(usage_vals) * 1.1
            self._chart_ax.set_ylim(0.0, max(upper, 100.0))
        else:
            self._chart_ax.set_ylim(0.0, 100.0)

        token_vals = self._finite_values(self._token_counts)
        if token_vals:
            upper_tokens = max(token_vals) * 1.1
            self._token_ax.set_ylim(0.0, max(upper_tokens, 1.0))
        else:
            self._token_ax.set_ylim(0.0, 1.0)

        end_time = max(self._timestamps[-1], 1.0)
        self._chart_ax.set_xlim(0.0, end_time)
        self._token_ax.set_xlim(0.0, end_time)

        self._canvas.draw_idle()

    def _update_summary(self, *, no_data: bool = False) -> None:
        if no_data or not self._timestamps:
            message = "Metrics not available yet. Run a query to collect performance data."
            if not self._chart_available:
                message = (
                    "Charts unavailable: install matplotlib to enable plotting.\n"
                    f"{message}"
                )
            self._summary_label.setText(message)
            return

        latest_cpu = self._last_snapshot.get("cpu_percent")
        latest_memory = self._last_snapshot.get("memory_percent")
        latest_tokens = self._last_snapshot.get("tokens_total")

        avg_cpu = self._series_average(self._cpu_percent)
        avg_memory = self._series_average(self._memory_percent)
        max_tokens = self._series_max(self._token_counts)
        token_rate = self._token_rate()

        lines = ["Latest metrics snapshot:"]
        lines.append(
            f"- CPU usage: {self._format_percent(latest_cpu)}"
            f" (avg {self._format_percent(avg_cpu)})"
        )
        lines.append(
            f"- Memory usage: {self._format_percent(latest_memory)}"
            f" (avg {self._format_percent(avg_memory)})"
        )
        lines.append(
            f"- Tokens processed: {self._format_tokens(latest_tokens)}"
            f" (peak {self._format_tokens(max_tokens)})"
        )
        if token_rate is not None:
            lines.append(f"- Estimated token rate: {token_rate:.1f} tokens/s")

        if self._timer.isActive():
            refresh = self._timer.interval() / 1000.0
            lines.append(f"- Auto-refresh enabled every {refresh:.1f}s")

        if not self._chart_available:
            lines.append("- Charts unavailable: install matplotlib to enable plotting")

        self._summary_label.setText("\n".join(lines))

    def _extract_snapshot(self, metrics: Mapping[str, Any]) -> Mapping[str, float | None]:
        cpu_percent = self._extract_number(
            metrics,
            (
                ("system", "cpu_percent"),
                ("cpu", "percent"),
                ("cpu_usage", "percent"),
                ("cpu_percent",),
                ("cpu_usage",),
            ),
        )

        memory_percent = self._extract_number(
            metrics,
            (
                ("system", "memory_percent"),
                ("memory", "percent"),
                ("memory_percent",),
                ("memory_usage", "percent"),
            ),
        )

        if memory_percent is None:
            used_mb = self._extract_number(
                metrics,
                (
                    ("memory", "used_mb"),
                    ("system", "memory_used_mb"),
                ),
            )
            total_mb = self._extract_number(
                metrics,
                (
                    ("memory", "total_mb"),
                    ("system", "memory_total_mb"),
                ),
            )
            if used_mb is not None and total_mb:
                memory_percent = (used_mb / total_mb) * 100.0

        tokens_total = self._extract_tokens(metrics)

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "tokens_total": tokens_total,
        }

    def _extract_number(
        self,
        metrics: Mapping[str, Any],
        paths: tuple[tuple[str, ...], ...],
    ) -> float | None:
        for path in paths:
            value: Any = metrics
            for key in path:
                if not isinstance(value, Mapping) or key not in value:
                    break
                value = value[key]
            else:
                if isinstance(value, (int, float)):
                    return float(value)
        return None

    def _extract_tokens(self, metrics: Mapping[str, Any]) -> float | None:
        tokens_section = self._extract_mapping(metrics, ("tokens",))
        if tokens_section is None:
            tokens_section = self._extract_mapping(metrics, ("usage", "tokens"))
        if tokens_section is None:
            total = self._extract_number(
                metrics,
                (("token_usage",), ("total_tokens",), ("tokens_total",)),
            )
            return total

        total = 0.0
        found = False
        for value in tokens_section.values():
            if isinstance(value, Mapping):
                for sub_value in value.values():
                    if isinstance(sub_value, (int, float)):
                        total += float(sub_value)
                        found = True
                continue
            if isinstance(value, (int, float)):
                total += float(value)
                found = True
        return total if found else None

    def _extract_mapping(
        self, metrics: Mapping[str, Any], path: tuple[str, ...]
    ) -> Mapping[str, Any] | None:
        value: Any = metrics
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                return None
            value = value[key]
        return value if isinstance(value, Mapping) else None

    def _to_series_value(self, value: float | None) -> float:
        return float(value) if value is not None else math.nan

    def _trim_series(self) -> None:
        while len(self._timestamps) > self._MAX_POINTS:
            self._timestamps.pop(0)
            self._cpu_percent.pop(0)
            self._memory_percent.pop(0)
            self._token_counts.pop(0)

    def _finite_values(self, values: list[float]) -> list[float]:
        return [value for value in values if not math.isnan(value)]

    def _series_average(self, values: list[float]) -> float | None:
        finite = self._finite_values(values)
        if not finite:
            return None
        return sum(finite) / len(finite)

    def _series_max(self, values: list[float]) -> float | None:
        finite = self._finite_values(values)
        if not finite:
            return None
        return max(finite)

    def _token_rate(self) -> float | None:
        if len(self._timestamps) < 2:
            return None
        finite = self._finite_values(self._token_counts)
        if len(finite) < 2:
            return None
        latest_tokens = finite[-1]
        prev_tokens = finite[-2]
        latest_time = self._timestamps[-1]
        prev_time = self._timestamps[-2]
        elapsed = latest_time - prev_time
        if elapsed <= 0:
            return None
        return (latest_tokens - prev_tokens) / elapsed

    def _format_percent(self, value: float | None) -> str:
        if value is None or math.isnan(value):
            return "N/A"
        return f"{value:.1f}%"

    def _format_tokens(self, value: float | None) -> str:
        if value is None or math.isnan(value):
            return "N/A"
        if value >= 1000:
            return f"{value/1000:.1f}k"
        return f"{value:.0f}"

    def _set_chart_defaults(self) -> None:
        if (
            not self._chart_available
            or self._canvas is None
            or self._chart_ax is None
            or self._token_ax is None
            or self._cpu_line is None
            or self._memory_line is None
            or self._token_line is None
        ):
            return

        self._cpu_line.set_data([], [])
        self._memory_line.set_data([], [])
        self._token_line.set_data([], [])
        self._chart_ax.set_xlim(0.0, 1.0)
        self._chart_ax.set_ylim(0.0, 100.0)
        self._token_ax.set_xlim(0.0, 1.0)
        self._token_ax.set_ylim(0.0, 1.0)
        self._canvas.draw_idle()
