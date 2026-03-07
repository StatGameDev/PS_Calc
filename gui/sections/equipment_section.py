from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from gui.section import Section

# Weapon types that occupy both hands (F5: disables left_hand slot).
# These use loc=EQP_ARMS in item_db and block the left hand entirely.
_TWO_HANDED_WEAPON_TYPES: frozenset[str] = frozenset({
    "2HSword", "2HSpear", "2HAxe", "2HStaff",
    "Bow", "MusicalInstrument", "Whip", "Katar", "Fuuma",
    "Revolver", "Rifle", "Gatling", "Shotgun", "Grenade",
})

# Jobs that may equip 1H weapons (dual-wield) in left hand (F6).
# All jobs can use shields; only these jobs additionally see 1H weapons in the browser.
_DUAL_WIELD_JOBS: frozenset[int] = frozenset({12, 24})  # Assassin, Assassin Cross

# (slot_key, display_label, has_refine)
_SLOTS: list[tuple[str, str, bool]] = [
    ("right_hand", "R. Hand",  True),
    ("left_hand",  "L. Hand",  True),
    ("ammo",       "Ammo",     False),
    ("armor",      "Armor",    True),
    ("garment",    "Garment",  True),
    ("footwear",   "Footwear", True),
    ("acc_l",      "Acc. L",   False),
    ("acc_r",      "Acc. R",   False),
    ("head_top",   "Head Top", True),
    ("head_mid",   "Head Mid", True),
    ("head_low",   "Head Low", True),
]

# Element names indexed by ID 0-9 (Hercules order)
_ELEMENT_NAMES = [
    "Neutral", "Water", "Earth", "Fire", "Wind",
    "Poison", "Holy", "Dark", "Ghost", "Undead",
]


def _resolve_item_name(item_id: Optional[int]) -> str:
    """Return display name for a slot item ID. Falls back gracefully."""
    if item_id is None:
        return "— Empty —"
    item = loader.get_item(item_id)
    if item is None:
        return f"Unknown (ID {item_id})"
    return item.get("name", item.get("aegis_name", f"ID {item_id}"))


def _resolve_card_label(card_id: Optional[int]) -> str:
    """Return short label for a card button (truncated name or dash)."""
    if card_id is None:
        return "—"
    item = loader.get_item(card_id)
    if item is None:
        return f"#{card_id}"
    name = item.get("name", item.get("aegis_name", f"#{card_id}"))
    # Strip trailing " Card" suffix to save button space
    if name.endswith(" Card"):
        name = name[:-5]
    return name[:10] if len(name) > 10 else name


class EquipmentSection(Section):
    """Phase 1.4 — Equipment slots with item name, refine spinners, Edit button."""

    equipment_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_weapon_lbl: QLabel | None = None
        self._compact_summary_lbl: QLabel | None = None

        # Per-slot widget storage (keyed by slot_key)
        self._item_ids:     dict[str, Optional[int]] = {s: None for s, *_ in _SLOTS}
        self._name_labels:  dict[str, QLabel]        = {}
        self._refine_spins: dict[str, QSpinBox]      = {}
        self._edit_btns:    dict[str, QPushButton]   = {}
        self._current_job_id: int = 0

        # G13: card sub-slot storage — list of card item IDs per slot (length = item's slots count)
        self._card_ids:  dict[str, list[Optional[int]]] = {s: [] for s, *_ in _SLOTS}
        self._card_btns: dict[str, list[QPushButton]]   = {s: [] for s, *_ in _SLOTS}
        # Container widgets for name+card area (col 1 of grid)
        self._name_containers: dict[str, QWidget] = {}
        self._card_rows:       dict[str, QWidget] = {}

        # ── Slot grid ──────────────────────────────────────────────────────
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)

        for row_i, (slot_key, slot_label, has_refine) in enumerate(_SLOTS):
            slot_lbl = QLabel(slot_label)
            slot_lbl.setObjectName("equip_slot_label")
            slot_lbl.setFixedWidth(68)
            grid.addWidget(slot_lbl, row_i, 0)

            # Col 1: container with item name on top, card row below
            name_container = QWidget()
            name_col_layout = QVBoxLayout(name_container)
            name_col_layout.setContentsMargins(0, 0, 0, 0)
            name_col_layout.setSpacing(2)

            name_lbl = QLabel("— Empty —")
            name_lbl.setObjectName("equip_item_label")
            self._name_labels[slot_key] = name_lbl
            name_col_layout.addWidget(name_lbl)

            card_row = QWidget()
            card_row_layout = QHBoxLayout(card_row)
            card_row_layout.setContentsMargins(0, 0, 0, 0)
            card_row_layout.setSpacing(3)
            card_row_layout.addStretch()
            card_row.setVisible(False)
            self._card_rows[slot_key] = card_row
            self._name_containers[slot_key] = name_container
            name_col_layout.addWidget(card_row)

            grid.addWidget(name_container, row_i, 1)

            if has_refine:
                refine_spin = QSpinBox()
                refine_spin.setRange(0, 20)
                refine_spin.setValue(0)
                refine_spin.setFixedWidth(50)
                refine_spin.setPrefix("+")
                refine_spin.valueChanged.connect(self.equipment_changed)
                self._refine_spins[slot_key] = refine_spin
                grid.addWidget(refine_spin, row_i, 2)
            else:
                placeholder = QLabel("")
                grid.addWidget(placeholder, row_i, 2)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("equip_edit_btn")
            edit_btn.setFixedWidth(42)
            self._edit_btns[slot_key] = edit_btn
            edit_btn.clicked.connect(
                lambda checked=False, k=slot_key: self._open_browser(k)
            )
            grid.addWidget(edit_btn, row_i, 3)

        self.add_content_widget(grid_widget)

        # ── Weapon element override ────────────────────────────────────────
        elem_row = QWidget()
        elem_layout = QHBoxLayout(elem_row)
        elem_layout.setContentsMargins(0, 4, 0, 0)
        elem_layout.setSpacing(6)
        elem_layout.addWidget(QLabel("Weapon Element:"))
        self._element_combo = QComboBox()
        self._element_combo.addItem("From Item", None)
        for idx, name in enumerate(_ELEMENT_NAMES):
            self._element_combo.addItem(name, idx)
        self._element_combo.currentIndexChanged.connect(self.equipment_changed)
        elem_layout.addWidget(self._element_combo)
        elem_layout.addStretch()
        self.add_content_widget(elem_row)

        # ── Armor element override ─────────────────────────────────────────
        armor_elem_row = QWidget()
        armor_elem_layout = QHBoxLayout(armor_elem_row)
        armor_elem_layout.setContentsMargins(0, 0, 0, 0)
        armor_elem_layout.setSpacing(6)
        armor_elem_layout.addWidget(QLabel("Armor Element:"))
        self._armor_element_combo = QComboBox()
        for idx, name in enumerate(_ELEMENT_NAMES):
            self._armor_element_combo.addItem(name, idx)
        self._armor_element_combo.currentIndexChanged.connect(self.equipment_changed)
        armor_elem_layout.addWidget(self._armor_element_combo)
        armor_elem_layout.addStretch()
        self.add_content_widget(armor_elem_row)

    # ── Card slot helpers ───────────────────────────────────────────────────

    def _refresh_card_slots(self, slot_key: str) -> None:
        """Rebuild card sub-slot buttons for slot_key based on equipped item's slots count."""
        from gui.dialogs.equipment_browser import EquipmentBrowserDialog  # noqa: F401 (lazy)
        card_row = self._card_rows[slot_key]
        layout = card_row.layout()

        # Remove existing card buttons
        for btn in self._card_btns[slot_key]:
            layout.removeWidget(btn)
            btn.deleteLater()
        self._card_btns[slot_key] = []

        item_id = self._item_ids.get(slot_key)
        num_slots = 0
        if item_id is not None:
            item = loader.get_item(item_id)
            if item is not None:
                num_slots = item.get("slots", 0)

        # Resize card_ids list to match new slot count, preserving existing values
        old_ids = self._card_ids[slot_key]
        self._card_ids[slot_key] = [
            (old_ids[i] if i < len(old_ids) else None) for i in range(num_slots)
        ]

        if num_slots == 0:
            card_row.setVisible(False)
            return

        # Rebuild buttons (insert before the trailing stretch)
        stretch_idx = layout.count() - 1  # stretch is last item
        for i in range(num_slots):
            card_id = self._card_ids[slot_key][i]
            label = _resolve_card_label(card_id)
            btn = QPushButton(label)
            btn.setObjectName("card_slot_btn")
            btn.setFixedWidth(72)
            btn.clicked.connect(
                lambda checked=False, k=slot_key, idx=i: self._open_card_browser(k, idx)
            )
            layout.insertWidget(stretch_idx + i, btn)
            self._card_btns[slot_key].append(btn)

        card_row.setVisible(True)

    def _open_card_browser(self, slot_key: str, card_index: int) -> None:
        from gui.dialogs.equipment_browser import EquipmentBrowserDialog
        current = self._card_ids[slot_key][card_index] if card_index < len(self._card_ids[slot_key]) else None
        dlg = EquipmentBrowserDialog(
            slot_key, current,
            job_id=self._current_job_id,
            item_type_override="IT_CARD",
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_id = dlg.selected_item_id()
            self._card_ids[slot_key][card_index] = new_id
            self._card_btns[slot_key][card_index].setText(_resolve_card_label(new_id))
            self.equipment_changed.emit()

    # ── Browser ────────────────────────────────────────────────────────────

    def _open_browser(self, slot_key: str) -> None:
        from gui.dialogs.equipment_browser import EquipmentBrowserDialog
        dlg = EquipmentBrowserDialog(
            slot_key, self._item_ids.get(slot_key),
            job_id=self._current_job_id, parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_id = dlg.selected_item_id()
            self._item_ids[slot_key] = new_id
            self._name_labels[slot_key].setText(_resolve_item_name(new_id))
            if new_id is None and slot_key in self._refine_spins:
                self._refine_spins[slot_key].setValue(0)
            self._refresh_card_slots(slot_key)
            if slot_key == "right_hand":
                self._update_left_hand_state()
            if self._compact_widget is not None:
                self._update_compact_labels()
            self.equipment_changed.emit()

    def _is_right_hand_two_handed(self) -> bool:
        rh_id = self._item_ids.get("right_hand")
        if rh_id is None:
            return False
        item = loader.get_item(rh_id)
        if item is None:
            return False
        return item.get("weapon_type", "") in _TWO_HANDED_WEAPON_TYPES

    def _update_left_hand_state(self) -> None:
        """Enable or disable the left_hand slot (F5: blocked by 2H right-hand weapon)."""
        is_2h = self._is_right_hand_two_handed()
        enabled = not is_2h

        edit_btn = self._edit_btns.get("left_hand")
        if edit_btn:
            edit_btn.setEnabled(enabled)

        if not enabled:
            # Clear the slot when blocked by a 2H weapon
            self._item_ids["left_hand"] = None
            self._name_labels["left_hand"].setText("— Empty —")
            if "left_hand" in self._refine_spins:
                self._refine_spins["left_hand"].setValue(0)

        name_lbl = self._name_labels.get("left_hand")
        if name_lbl:
            name_lbl.setEnabled(enabled)

    # ── Compact API ────────────────────────────────────────────────────────

    def _build_compact_widget(self) -> None:
        w = QWidget()
        inner = QGridLayout(w)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.setSpacing(3)

        self._compact_weapon_lbl = QLabel("— Empty —")
        self._compact_weapon_lbl.setObjectName("compact_equip_weapon")
        inner.addWidget(self._compact_weapon_lbl, 0, 0)

        self._compact_summary_lbl = QLabel("0/11 slots filled")
        self._compact_summary_lbl.setObjectName("compact_equip_summary")
        inner.addWidget(self._compact_summary_lbl, 1, 0)

        w.setVisible(False)
        self._compact_widget = w
        self.layout().addWidget(w)

    def _update_compact_labels(self) -> None:
        if self._compact_weapon_lbl is None:
            return
        rh_id = self._item_ids.get("right_hand")
        rh_name = _resolve_item_name(rh_id)
        rh_refine_spin = self._refine_spins.get("right_hand")
        if rh_refine_spin and rh_refine_spin.value() > 0:
            weapon_text = f"{rh_name} +{rh_refine_spin.value()}"
        else:
            weapon_text = rh_name
        self._compact_weapon_lbl.setText(weapon_text)

        filled = sum(1 for v in self._item_ids.values() if v is not None)
        self._compact_summary_lbl.setText(f"{filled}/{len(_SLOTS)} slots filled")  # type: ignore[union-attr]

    def _enter_compact_view(self) -> None:
        self._pre_compact_collapsed = self._is_collapsed
        if self._compact_widget is None:
            self._build_compact_widget()
        self._update_compact_labels()
        self._content_frame.setVisible(False)
        self._compact_widget.setVisible(True)
        self._is_collapsed = False
        self._arrow.setText("▼")

    def _exit_compact_view(self) -> None:
        if self._compact_widget is not None:
            self._compact_widget.setVisible(False)
        restored = self._pre_compact_collapsed if self._pre_compact_collapsed is not None else False
        self._pre_compact_collapsed = None
        self._is_collapsed = restored
        self._content_frame.setVisible(not restored)
        self._arrow.setText("▶" if restored else "▼")

    # ── Public API ────────────────────────────────────────────────────────

    def update_for_job(self, job_id: int) -> None:
        """Track job for left_hand browser filtering (F6: Assassin dual-wield)."""
        self._current_job_id = job_id

    def load_build(self, build: PlayerBuild) -> None:
        """Populate all equipment widgets from build without emitting change signals."""
        for spin in self._refine_spins.values():
            spin.blockSignals(True)
        self._element_combo.blockSignals(True)

        self._current_job_id = build.job_id

        for slot_key, _, has_refine in _SLOTS:
            item_id = build.equipped.get(slot_key)
            self._item_ids[slot_key] = item_id
            self._name_labels[slot_key].setText(_resolve_item_name(item_id))

            if has_refine and slot_key in self._refine_spins:
                self._refine_spins[slot_key].setValue(
                    build.refine_levels.get(slot_key, 0)
                )

            # G13: restore card IDs from build.equipped before refreshing buttons
            item = loader.get_item(item_id) if item_id is not None else None
            num_slots = item.get("slots", 0) if item is not None else 0
            self._card_ids[slot_key] = [
                build.equipped.get(f"{slot_key}_card_{i}")
                for i in range(num_slots)
            ]
            self._refresh_card_slots(slot_key)

        # Weapon element combo: None → "From Item" (index 0), else match by data
        we = build.weapon_element
        if we is None:
            self._element_combo.setCurrentIndex(0)
        else:
            idx = self._element_combo.findData(we)
            self._element_combo.setCurrentIndex(idx if idx >= 0 else 0)

        # Armor element combo: int 0-9, default 0 (Neutral)
        self._armor_element_combo.blockSignals(True)
        ae_idx = self._armor_element_combo.findData(build.armor_element)
        self._armor_element_combo.setCurrentIndex(ae_idx if ae_idx >= 0 else 0)
        self._armor_element_combo.blockSignals(False)

        for spin in self._refine_spins.values():
            spin.blockSignals(False)
        self._element_combo.blockSignals(False)

        # Apply F5 state without emitting signals (2H right-hand blocks left hand)
        is_2h = self._is_right_hand_two_handed()
        edit_btn = self._edit_btns.get("left_hand")
        name_lbl = self._name_labels.get("left_hand")
        if edit_btn:
            edit_btn.setEnabled(not is_2h)
        if name_lbl:
            name_lbl.setEnabled(not is_2h)

        if self._compact_widget is not None:
            self._update_compact_labels()

    def collect_into(self, build: PlayerBuild) -> None:
        """Write section state into an existing PlayerBuild in-place."""
        # Base slot keys first (order matters for acc_l/acc_r round-trip stability)
        equipped: dict[str, Optional[int]] = {slot_key: self._item_ids[slot_key] for slot_key, *_ in _SLOTS}
        # G13: append card keys in slot order: {slot}_card_0 … {slot}_card_{N-1}
        for slot_key, *_ in _SLOTS:
            for i, card_id in enumerate(self._card_ids.get(slot_key, [])):
                equipped[f"{slot_key}_card_{i}"] = card_id
        build.equipped = equipped
        build.refine_levels = {
            slot_key: self._refine_spins[slot_key].value()
            for slot_key, _, has_refine in _SLOTS
            if has_refine and slot_key in self._refine_spins
        }
        build.weapon_element = self._element_combo.currentData()  # None or int 0-9
        build.armor_element = self._armor_element_combo.currentData() or 0  # int 0-9
