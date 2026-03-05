from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.data_loader import loader

_ELEMENT_NAMES = [
    "Neutral", "Water", "Earth", "Fire", "Wind",
    "Poison", "Holy", "Dark", "Ghost", "Undead",
]

_COLUMNS = ["Name", "ID", "Lv", "HP", "DEF", "Element", "Race", "Size", "Boss"]
_NUMERIC_COLS = {1, 2, 3, 4}  # ID, Lv, HP, DEF — sort as numbers


class _NumericItem(QTableWidgetItem):
    """QTableWidgetItem that sorts numerically when the text is a plain integer."""
    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return int(self.text()) < int(other.text())
        except ValueError:
            return super().__lt__(other)


class MonsterBrowserDialog(QDialog):
    """Filterable monster list. Returns the selected mob_id or None (cleared)."""

    def __init__(self, current_mob_id: Optional[int] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Target")
        self.setMinimumSize(760, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._result: Optional[int] = current_mob_id
        self._mobs: list = loader.get_all_monsters()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Monster name…")
        search_row.addWidget(self._search, stretch=1)
        layout.addLayout(search_row)

        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, stretch=1)

        btn_box = QDialogButtonBox()
        self._ok_btn = btn_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self._clear_btn = btn_box.addButton("Clear", QDialogButtonBox.ButtonRole.ResetRole)
        btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self._ok_btn.setEnabled(False)
        layout.addWidget(btn_box)

        self._search.textChanged.connect(self._on_filter)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.cellDoubleClicked.connect(lambda r, c: self._accept_selected())
        self._ok_btn.clicked.connect(self._accept_selected)
        self._clear_btn.clicked.connect(self._clear)
        btn_box.rejected.connect(self.reject)

        self._populate(self._mobs)

        if current_mob_id is not None:
            self._select_row(current_mob_id)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _make_item(self, text: str, numeric: bool = False) -> QTableWidgetItem:
        item = _NumericItem(text) if numeric else QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _populate(self, mobs: list) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(mobs))
        for row, m in enumerate(mobs):
            elem_int = m.get("element", 0)
            elem_lv = m.get("element_level", 1)
            elem_name = _ELEMENT_NAMES[elem_int] if 0 <= elem_int <= 9 else str(elem_int)

            name_item = self._make_item(m.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, m.get("id"))
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, self._make_item(str(m.get("id", "")),    numeric=True))
            self._table.setItem(row, 2, self._make_item(str(m.get("level", "")), numeric=True))
            self._table.setItem(row, 3, self._make_item(str(m.get("hp", "")),    numeric=True))
            self._table.setItem(row, 4, self._make_item(str(m.get("def_", "")),  numeric=True))
            self._table.setItem(row, 5, self._make_item(f"{elem_name}/{elem_lv}"))
            self._table.setItem(row, 6, self._make_item(m.get("race", "")))
            self._table.setItem(row, 7, self._make_item(m.get("size", "")))
            self._table.setItem(row, 8, self._make_item("✓" if m.get("is_boss") else ""))

        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)

    def _select_row(self, mob_id: int) -> None:
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == mob_id:
                self._table.selectRow(row)
                self._table.scrollToItem(item)
                break

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_filter(self, text: str) -> None:
        query = text.strip().lower()
        filtered = self._mobs if not query else [
            m for m in self._mobs if query in m.get("name", "").lower()
        ]
        self._populate(filtered)

    def _on_selection_changed(self) -> None:
        self._ok_btn.setEnabled(bool(self._table.selectedItems()))

    def _accept_selected(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        item = self._table.item(rows[0].row(), 0)
        self._result = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _clear(self) -> None:
        self._result = None
        self.accept()

    # ── Public API ─────────────────────────────────────────────────────────

    def selected_mob_id(self) -> Optional[int]:
        return self._result
