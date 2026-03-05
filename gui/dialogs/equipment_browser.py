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

# Which item_db type to pull for each equipment slot key.
_SLOT_ITEM_TYPE: dict[str, str] = {
    "right_hand": "IT_WEAPON",
    "left_hand":  "IT_ARMOR",   # shields are IT_ARMOR
    "ammo":       "IT_AMMO",
    "armor":      "IT_ARMOR",
    "garment":    "IT_ARMOR",
    "footwear":   "IT_ARMOR",
    "acc_l":      "IT_ARMOR",
    "acc_r":      "IT_ARMOR",
    "head_top":   "IT_ARMOR",
    "head_mid":   "IT_ARMOR",
    "head_low":   "IT_ARMOR",
}

# Items matching a slot must have any of these EQP tags in their loc list.
_SLOT_EQP: dict[str, set[str]] = {
    "right_hand": {"EQP_WEAPON"},
    "left_hand":  {"EQP_SHIELD"},
    "ammo":       {"EQP_AMMO"},
    "armor":      {"EQP_ARMOR"},
    "garment":    {"EQP_GARMENT"},
    "footwear":   {"EQP_SHOES"},
    "acc_l":      {"EQP_ACC_L", "EQP_ACC_R"},
    "acc_r":      {"EQP_ACC_L", "EQP_ACC_R"},
    "head_top":   {"EQP_HEAD_TOP"},
    "head_mid":   {"EQP_HEAD_MID"},
    "head_low":   {"EQP_HEAD_LOW"},
}

_SLOT_LABELS: dict[str, str] = {
    "right_hand": "R. Hand",
    "left_hand":  "L. Hand",
    "ammo":       "Ammo",
    "armor":      "Armor",
    "garment":    "Garment",
    "footwear":   "Footwear",
    "acc_l":      "Acc. L",
    "acc_r":      "Acc. R",
    "head_top":   "Head Top",
    "head_mid":   "Head Mid",
    "head_low":   "Head Low",
}

# Columns: Name | ATK | DEF | Info | Slots | Ref?
# ATK: weapon atk or ammo atk; DEF: armor def; Info: weapon_type or ammo subtype.
_COLUMNS = ["Name", "ATK", "DEF", "Info", "Slots", "Ref?"]


def _item_row(item: dict) -> tuple[str, str, str, str, str, str]:
    """Return (name, atk, def, info, slots, refineable) display strings."""
    name = item.get("name") or item.get("aegis_name", "")
    slots = str(item.get("slots", 0))
    ref = "✓" if item.get("refineable", True) else "✗"

    itype = item.get("type", "")
    if itype == "IT_WEAPON":
        atk = str(item.get("atk", 0))
        def_ = "—"
        info = item.get("weapon_type", "")
    elif itype == "IT_AMMO":
        atk = str(item.get("atk", 0))
        def_ = "—"
        info = item.get("subtype", "").replace("A_", "")
    else:  # IT_ARMOR
        atk = "—"
        def_ = str(item.get("def", 0))
        info = ""

    return name, atk, def_, info, slots, ref


class EquipmentBrowserDialog(QDialog):
    """
    Filterable item browser for a single equipment slot.
    Returns the selected item_id or None (slot cleared).
    """

    def __init__(
        self,
        slot_key: str,
        current_item_id: Optional[int] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        slot_label = _SLOT_LABELS.get(slot_key, slot_key)
        self.setWindowTitle(f"Select Item — {slot_label}")
        self.setMinimumSize(680, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._result: Optional[int] = current_item_id

        # Load and filter items for this slot.
        item_type = _SLOT_ITEM_TYPE.get(slot_key, "IT_ARMOR")
        valid_eqp = _SLOT_EQP.get(slot_key, set())
        all_items = loader.get_items_by_type(item_type)
        self._items: list = [
            it for it in all_items
            if set(it.get("loc", [])) & valid_eqp
        ]

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Item name…")
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

        self._populate(self._items)

        if current_item_id is not None:
            self._select_row(current_item_id)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _make_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _populate(self, items: list) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(items))
        for row, it in enumerate(items):
            name, atk, def_, info, slots, ref = _item_row(it)
            name_item = self._make_item(name)
            name_item.setData(Qt.ItemDataRole.UserRole, it.get("id"))
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, self._make_item(atk))
            self._table.setItem(row, 2, self._make_item(def_))
            self._table.setItem(row, 3, self._make_item(info))
            self._table.setItem(row, 4, self._make_item(slots))
            self._table.setItem(row, 5, self._make_item(ref))

        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)

    def _select_row(self, item_id: int) -> None:
        for row in range(self._table.rowCount()):
            cell = self._table.item(row, 0)
            if cell and cell.data(Qt.ItemDataRole.UserRole) == item_id:
                self._table.selectRow(row)
                self._table.scrollToItem(cell)
                break

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_filter(self, text: str) -> None:
        query = text.strip().lower()
        filtered = self._items if not query else [
            it for it in self._items
            if query in (it.get("name") or it.get("aegis_name", "")).lower()
        ]
        self._populate(filtered)

    def _on_selection_changed(self) -> None:
        self._ok_btn.setEnabled(bool(self._table.selectedItems()))

    def _accept_selected(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        cell = self._table.item(rows[0].row(), 0)
        self._result = cell.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _clear(self) -> None:
        self._result = None
        self.accept()

    # ── Public API ─────────────────────────────────────────────────────────

    def selected_item_id(self) -> Optional[int]:
        return self._result
