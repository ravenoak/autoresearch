"""Table model and view classes for presenting structured search hits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QTableView


@dataclass(frozen=True, slots=True)
class SearchResultRow:
    """Container for a single structured search result.

    Attributes:
        rank: One-based position for the result.
        title: Human-readable description of the hit.
        source: URL or origin reference associated with the hit.
    """

    rank: int
    title: str
    source: str


class SearchResultsModel(QAbstractTableModel):
    """Qt table model for presenting structured search results.

    Attributes:
        _rows: Internal list of :class:`SearchResultRow` entries powering the
            view.
    """

    _HEADERS: tuple[str, ...] = ("Rank", "Title", "Source")

    def __init__(self, parent: QTableView | None = None) -> None:
        super().__init__(parent)
        self._rows: list[SearchResultRow] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature
        if parent.isValid():
            return 0
        return len(self._HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # noqa: D401 - Qt signature
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None

        row = self._rows[index.row()]
        column = index.column()

        if role in {Qt.DisplayRole, Qt.EditRole}:
            if column == 0:
                return row.rank
            if column == 1:
                return row.title
            if column == 2:
                return row.source

        if role == Qt.ToolTipRole and column == 2 and row.source:
            return row.source

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:  # noqa: D401 - Qt signature
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and 0 <= section < len(self._HEADERS):
            return self._HEADERS[section]

        if orientation == Qt.Vertical and 0 <= section < len(self._rows):
            return str(self._rows[section].rank)

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # noqa: D401 - Qt signature
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def set_results(self, results: Iterable[SearchResultRow]) -> None:
        """Replace the table contents with ``results``.

        Args:
            results: Iterable of :class:`SearchResultRow` entries to display.
        """
        normalized = list(results)

        self.beginResetModel()
        self._rows = normalized
        self.endResetModel()

    def clear(self) -> None:
        """Remove all rows from the model."""
        self.set_results([])

    def row_at(self, row_index: int) -> SearchResultRow | None:
        """Return the row at ``row_index`` if available.

        Args:
            row_index: Zero-based index of the desired row.

        Returns:
            The requested :class:`SearchResultRow` if it exists, otherwise ``None``.
        """
        if 0 <= row_index < len(self._rows):
            return self._rows[row_index]
        return None


class SearchResultsTableView(QTableView):
    """Preconfigured ``QTableView`` for displaying ``SearchResultsModel`` data."""

    def __init__(self, parent: Any | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("results-display-search-table")
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabKeyNavigation(True)
        self.setWordWrap(False)
        self.setAccessibleName("Structured search results")

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        vertical_header = self.verticalHeader()
        vertical_header.setVisible(False)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setDefaultSectionSize(24)

        self.setSortingEnabled(False)

    def model(self) -> SearchResultsModel:  # type: ignore[override]
        model = super().model()
        assert isinstance(model, SearchResultsModel)
        return model

    def setModel(self, model: QAbstractTableModel) -> None:  # noqa: N802 - Qt override
        assert isinstance(model, SearchResultsModel)
        super().setModel(model)
        if model.rowCount():
            self.selectRow(0)
