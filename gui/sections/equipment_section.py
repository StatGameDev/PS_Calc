from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
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
_DUAL_WIELD_JOBS: frozenset[int] = frozenset({12, 4013})  # Assassin, Assassin Cross

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

# G39: slot → item type + valid EQP locs (mirrors equipment_browser logic)
_SLOT_TYPE: dict[str, str] = {
    "right_hand": "IT_WEAPON",
    "left_hand":  "IT_ARMOR",
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

_SLOT_LOC: dict[str, set[str]] = {
    "right_hand": {"EQP_WEAPON", "EQP_ARMS"},
    "left_hand":  {"EQP_SHIELD"},
    "ammo":       {"EQP_AMMO"},
    "armor":      {"EQP_ARMOR"},
    "garment":    {"EQP_GARMENT"},
    "footwear":   {"EQP_SHOES"},
    "acc_l":      {"EQP_ACC"},
    "acc_r":      {"EQP_ACC"},
    "head_top":   {"EQP_HEAD_TOP"},
    "head_mid":   {"EQP_HEAD_MID"},
    "head_low":   {"EQP_HEAD_LOW"},
}


def _load_slot_items(slot_key: str, job_id: Optional[int] = None) -> list[tuple[str, int]]:
    """Return [(display_name, item_id), ...] sorted alphabetically for the inline combo.
    job_id=None disables job filtering (used at widget construction time).
    For left_hand + Assassin dual-wield jobs, 1H weapons are included alongside shields."""
    item_type = _SLOT_TYPE.get(slot_key)
    valid_locs = set(_SLOT_LOC.get(slot_key, set()))
    if item_type is None:
        return []
    # Assassin dual-wield: include 1H weapons in the left_hand combo
    if slot_key == "left_hand" and job_id in _DUAL_WIELD_JOBS:
        valid_locs |= {"EQP_WEAPON"}
        items = loader.get_items_by_type("IT_ARMOR") + loader.get_items_by_type("IT_WEAPON")
    else:
        items = loader.get_items_by_type(item_type)
    filtered = [
        it for it in items
        if any(loc in valid_locs for loc in it.get("loc", []))
        and (job_id is None or not it.get("job") or job_id in it.get("job", []))
    ]
    filtered.sort(key=lambda it: it.get("name", it.get("aegis_name", "")))
    return [(it.get("name", it.get("aegis_name", f"ID {it['id']}")), it["id"]) for it in filtered]


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


class _NoWheelCombo(QComboBox):
    """QComboBox that never reacts to the scroll wheel (prevents accidental slot changes)."""

    def wheelEvent(self, event) -> None:
        event.ignore()


class EquipmentSection(Section):
    """Phase 1.4 — Equipment slots with item name, refine spinners, Edit button."""

    equipment_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_weapon_lbl: QLabel | None = None
        self._compact_summary_lbl: QLabel | None = None

        # Per-slot widget storage (keyed by slot_key)
        self._item_ids:      dict[str, Optional[int]] = {s: None for s, *_ in _SLOTS}
        self._inline_combos: dict[str, QComboBox]     = {}  # G39: quick-select combos
        self._refine_spins:  dict[str, QSpinBox]      = {}
        self._edit_btns:     dict[str, QPushButton]   = {}
        self._current_job_id: int = 0

        # G13: card sub-slot storage — list of card item IDs per slot (length = item's slots count)
        self._card_ids:  dict[str, list[Optional[int]]] = {s: [] for s, *_ in _SLOTS}
        self._card_btns: dict[str, list[QPushButton]]   = {s: [] for s, *_ in _SLOTS}
        # Container widgets for name+card area (col 1 of grid)
        self._name_containers: dict[str, QWidget] = {}
        self._card_rows:       dict[str, QWidget] = {}
        # G17: Forge controls (right_hand only)
        self._forge_toggle_chk: Optional[QCheckBox] = None
        self._forge_controls_row: Optional[QWidget] = None
        self._forge_sc_spin: Optional[QSpinBox] = None
        self._forge_ranked_chk: Optional[QCheckBox] = None
        self._forge_element_combo: Optional[QComboBox] = None

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

            # G39: inline quick-select combo (replaces static name label)
            combo = _NoWheelCombo()
            combo.setObjectName("equip_inline_combo")
            combo.addItem("— Empty —", None)
            for item_name, item_id in _load_slot_items(slot_key):  # no job filter at construction
                combo.addItem(item_name, item_id)
            combo.currentIndexChanged.connect(
                lambda _sig, k=slot_key: self._on_inline_changed(k)
            )
            self._inline_combos[slot_key] = combo
            name_col_layout.addWidget(combo)

            # G17: Forge toggle + controls (right_hand only)
            if slot_key == "right_hand":
                forge_toggle = QCheckBox("Forged")
                forge_toggle.setObjectName("forge_toggle_chk")
                forge_toggle.toggled.connect(self._on_forge_toggled)
                name_col_layout.addWidget(forge_toggle)
                self._forge_toggle_chk = forge_toggle

                forge_ctrl = QWidget()
                forge_layout = QHBoxLayout(forge_ctrl)
                forge_layout.setContentsMargins(0, 0, 0, 0)
                forge_layout.setSpacing(4)

                forge_layout.addWidget(QLabel("Crumbs:"))
                sc_spin = QSpinBox()
                sc_spin.setRange(0, 3)
                sc_spin.setFixedWidth(40)
                sc_spin.valueChanged.connect(self.equipment_changed)
                forge_layout.addWidget(sc_spin)
                self._forge_sc_spin = sc_spin

                ranked_chk = QCheckBox("Ranked")
                ranked_chk.toggled.connect(self.equipment_changed)
                forge_layout.addWidget(ranked_chk)
                self._forge_ranked_chk = ranked_chk

                forge_layout.addWidget(QLabel("Ele:"))
                ele_combo = _NoWheelCombo()
                for ele_idx, ele_name in enumerate(_ELEMENT_NAMES):
                    ele_combo.addItem(ele_name, ele_idx)
                ele_combo.currentIndexChanged.connect(self.equipment_changed)
                forge_layout.addWidget(ele_combo)
                self._forge_element_combo = ele_combo

                forge_layout.addStretch()
                forge_ctrl.setVisible(False)
                name_col_layout.addWidget(forge_ctrl)
                self._forge_controls_row = forge_ctrl

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
                refine_spin.setRange(0, 10)
                refine_spin.setValue(0)
                refine_spin.setFixedWidth(58)
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
        self._element_combo = _NoWheelCombo()
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
        self._armor_element_combo = _NoWheelCombo()
        for idx, name in enumerate(_ELEMENT_NAMES):
            self._armor_element_combo.addItem(name, idx)
        self._armor_element_combo.currentIndexChanged.connect(self.equipment_changed)
        armor_elem_layout.addWidget(self._armor_element_combo)
        armor_elem_layout.addStretch()
        self.add_content_widget(armor_elem_row)

    # ── Forge helpers ───────────────────────────────────────────────────────

    def _on_forge_toggled(self, checked: bool) -> None:
        """Show forge controls and hide card row (or vice versa) for right_hand."""
        if self._forge_controls_row is not None:
            self._forge_controls_row.setVisible(checked)
        card_row = self._card_rows.get("right_hand")
        if card_row is not None:
            if checked:
                card_row.setVisible(False)
            else:
                self._refresh_card_slots("right_hand")
        self.equipment_changed.emit()

    # ── Card slot helpers ───────────────────────────────────────────────────

    def _refresh_card_slots(self, slot_key: str) -> None:
        """Rebuild card sub-slot buttons for slot_key based on equipped item's slots count."""
        from gui.dialogs.equipment_browser import EquipmentBrowserDialog  # noqa: F401 (lazy)
        card_row = self._card_rows[slot_key]
        layout = card_row.layout()

        # G17: suppress card display when forge is active for right_hand
        if (slot_key == "right_hand"
                and self._forge_toggle_chk is not None
                and self._forge_toggle_chk.isChecked()):
            card_row.setVisible(False)
            return

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

    # ── Inline combo ────────────────────────────────────────────────────────

    def _repopulate_combo(self, slot_key: str) -> None:
        """Rebuild combo items filtered for current job, preserving selection if still valid."""
        combo = self._inline_combos.get(slot_key)
        if combo is None:
            return
        current_id: Optional[int] = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— Empty —", None)
        for item_name, item_id in _load_slot_items(slot_key, self._current_job_id):
            combo.addItem(item_name, item_id)
        idx = combo.findData(current_id)
        if idx < 0 and current_id is not None:
            combo.addItem(_resolve_item_name(current_id), current_id)
            idx = combo.count() - 1
        combo.setCurrentIndex(max(0, idx))
        combo.blockSignals(False)

    def _on_inline_changed(self, slot_key: str) -> None:
        """Handle quick-select combo change (G39)."""
        combo = self._inline_combos.get(slot_key)
        if combo is None:
            return
        new_id: Optional[int] = combo.currentData()
        self._item_ids[slot_key] = new_id
        if new_id is None and slot_key in self._refine_spins:
            self._refine_spins[slot_key].setValue(0)
        self._refresh_card_slots(slot_key)
        if slot_key == "right_hand":
            self._update_left_hand_state()
        if self._compact_widget is not None:
            self._update_compact_labels()
        self.equipment_changed.emit()

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
            combo = self._inline_combos.get(slot_key)
            if combo is not None:
                combo.blockSignals(True)
                idx = combo.findData(new_id)
                if idx < 0 and new_id is not None:
                    combo.addItem(_resolve_item_name(new_id), new_id)
                    idx = combo.count() - 1
                combo.setCurrentIndex(max(0, idx))
                combo.blockSignals(False)
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

        combo_lh = self._inline_combos.get("left_hand")
        if combo_lh is not None:
            combo_lh.setEnabled(enabled)
            combo_lh.setItemText(0, "— Empty —" if enabled else "— Blocked (2H) —")

        if not enabled:
            # Clear the slot when blocked by a 2H weapon
            self._item_ids["left_hand"] = None
            if combo_lh is not None:
                combo_lh.blockSignals(True)
                combo_lh.setCurrentIndex(0)
                combo_lh.blockSignals(False)
            if "left_hand" in self._refine_spins:
                self._refine_spins["left_hand"].setValue(0)

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
        """Repopulate inline combos filtered for the new job (G39)."""
        self._current_job_id = job_id
        for slot_key in list(self._inline_combos):
            self._repopulate_combo(slot_key)

    def load_build(self, build: PlayerBuild) -> None:
        """Populate all equipment widgets from build without emitting change signals."""
        for spin in self._refine_spins.values():
            spin.blockSignals(True)
        self._element_combo.blockSignals(True)

        self._current_job_id = build.job_id

        # G17: restore forge state BEFORE the slot loop so _refresh_card_slots
        # for right_hand already sees the correct forge toggle state.
        if self._forge_toggle_chk is not None:
            self._forge_toggle_chk.blockSignals(True)
            self._forge_toggle_chk.setChecked(build.is_forged)
            self._forge_toggle_chk.blockSignals(False)
        if self._forge_controls_row is not None:
            self._forge_controls_row.setVisible(build.is_forged)
        if self._forge_sc_spin is not None:
            self._forge_sc_spin.blockSignals(True)
            self._forge_sc_spin.setValue(build.forge_sc_count)
            self._forge_sc_spin.blockSignals(False)
        if self._forge_ranked_chk is not None:
            self._forge_ranked_chk.blockSignals(True)
            self._forge_ranked_chk.setChecked(build.forge_ranked)
            self._forge_ranked_chk.blockSignals(False)
        if self._forge_element_combo is not None:
            self._forge_element_combo.blockSignals(True)
            fe_idx = self._forge_element_combo.findData(build.forge_element)
            self._forge_element_combo.setCurrentIndex(fe_idx if fe_idx >= 0 else 0)
            self._forge_element_combo.blockSignals(False)

        # Repopulate inline combos for the loaded job before restoring selections
        for slot_key in list(self._inline_combos):
            c = self._inline_combos[slot_key]
            c.blockSignals(True)
            c.clear()
            c.addItem("— Empty —", None)
            for item_name, item_id in _load_slot_items(slot_key, build.job_id):
                c.addItem(item_name, item_id)
            c.blockSignals(False)

        for slot_key, _, has_refine in _SLOTS:
            item_id = build.equipped.get(slot_key)
            self._item_ids[slot_key] = item_id
            combo = self._inline_combos.get(slot_key)
            if combo is not None:
                combo.blockSignals(True)
                idx = combo.findData(item_id)
                if idx < 0 and item_id is not None:
                    combo.addItem(_resolve_item_name(item_id), item_id)
                    idx = combo.count() - 1
                combo.setCurrentIndex(max(0, idx))
                combo.blockSignals(False)

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
        combo_lh = self._inline_combos.get("left_hand")
        if edit_btn:
            edit_btn.setEnabled(not is_2h)
        if combo_lh:
            combo_lh.setEnabled(not is_2h)

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
        # G17: forge state (right_hand only)
        build.is_forged = self._forge_toggle_chk.isChecked() if self._forge_toggle_chk is not None else False
        build.forge_sc_count = self._forge_sc_spin.value() if self._forge_sc_spin is not None else 0
        build.forge_ranked = self._forge_ranked_chk.isChecked() if self._forge_ranked_chk is not None else False
        build.forge_element = (self._forge_element_combo.currentData() or 0) if self._forge_element_combo is not None else 0
