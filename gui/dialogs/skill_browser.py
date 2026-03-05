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

_COLUMNS = ["Name", "ID", "Type", "Element", "Max Lv"]


def _fmt_type(t: str) -> str:
    return t.replace("skill_type_", "").replace("_", " ").title() if t else "—"


def _fmt_element(e: str) -> str:
    return e.replace("Ele_", "") if e else "—"


class SkillBrowserDialog(QDialog):
    """Filterable skill list. Returns the selected skill ID string."""

    def __init__(self, current_skill_id: Optional[str] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Skill")
        self.setMinimumSize(600, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._result: Optional[str] = current_skill_id
        self._skills: list = loader.get_all_skills()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Skill name…")
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

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setEnabled(False)
        layout.addWidget(btn_box)

        self._search.textChanged.connect(self._on_filter)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.cellDoubleClicked.connect(lambda r, c: self._accept_selected())
        self._ok_btn.clicked.connect(self._accept_selected)
        btn_box.rejected.connect(self.reject)

        self._populate(self._skills)

        if current_skill_id is not None:
            self._select_row(current_skill_id)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _make_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _populate(self, skills: list) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(skills))
        for row, s in enumerate(skills):
            name_item = self._make_item(s.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, s.get("id"))
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, self._make_item(str(s.get("id", ""))))
            self._table.setItem(row, 2, self._make_item(_fmt_type(s.get("skill_type", ""))))
            self._table.setItem(row, 3, self._make_item(_fmt_element(s.get("element", ""))))
            self._table.setItem(row, 4, self._make_item(str(s.get("max_level", ""))))

        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)

    def _select_row(self, skill_id: str) -> None:
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == skill_id:
                self._table.selectRow(row)
                self._table.scrollToItem(item)
                break

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_filter(self, text: str) -> None:
        query = text.strip().lower()
        filtered = self._skills if not query else [
            s for s in self._skills if query in s.get("name", "").lower()
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

    # ── Public API ─────────────────────────────────────────────────────────

    def selected_skill_id(self) -> Optional[str]:
        return self._result
