from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.models.build import PlayerBuild
from core.models.target import Target
from gui.section import Section
from gui.widgets import LevelWidget, NoWheelCombo

# Hercules element indices (ele_name order in db/const.hpp)
_ELEMENTS = [
    (0, "Neutral"),
    (1, "Water"),
    (2, "Earth"),
    (3, "Fire"),
    (4, "Wind"),
    (5, "Poison"),
    (6, "Holy"),
    (7, "Dark"),
    (8, "Ghost"),
    (9, "Undead"),
]


class TargetStateSection(Section):
    """
    Session R — debuffs/ailments applied by the player to the target.

    Two-method API (see docs/session_roadmap.md Session R):
      collect_into(build)     — writes SC_ETERNALCHAOS / SC_PROVOKE / SC_DECREASEAGI /
                                PR_LEXAETERNA to build.support_buffs. Called from
                                _collect_build() uniformly with all other sections.
      apply_to_target(target) — writes ailment/element effects directly to the resolved
                                Target (target_active_scs, element, DEF strip). Called
                                explicitly in _run_battle_pipeline() after target resolution.
                                No element restore needed — target is re-resolved each run.
    """

    state_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # ── Applied Debuffs ───────────────────────────────────────────────
        debuff_lbl = QLabel("Applied Debuffs")
        debuff_lbl.setObjectName("sub_group_title")
        outer.addWidget(debuff_lbl)

        debuff_grid = QGridLayout()
        debuff_grid.setHorizontalSpacing(8)
        debuff_grid.setVerticalSpacing(4)
        debuff_grid.setColumnStretch(1, 1)

        row = 0
        debuff_grid.addWidget(_lbl("Eternal Chaos"), row, 0)
        self._chk_chaos = QCheckBox()
        debuff_grid.addWidget(self._chk_chaos, row, 1)
        row += 1

        debuff_grid.addWidget(_lbl("Provoke"), row, 0)
        self._lw_provoke = LevelWidget(10, include_off=True, item_prefix="Lv ")
        debuff_grid.addWidget(self._lw_provoke, row, 1)
        row += 1

        debuff_grid.addWidget(_lbl("Decrease AGI"), row, 0)
        self._lw_decagi = LevelWidget(10, include_off=True, item_prefix="Lv ")
        debuff_grid.addWidget(self._lw_decagi, row, 1)
        row += 1

        debuff_grid.addWidget(_lbl("Lex Aeterna"), row, 0)
        self._chk_lex = QCheckBox()
        debuff_grid.addWidget(self._chk_lex, row, 1)

        outer.addLayout(debuff_grid)

        # ── Separator ─────────────────────────────────────────────────────
        outer.addWidget(_hline())

        # ── Status Ailments ───────────────────────────────────────────────
        ailment_lbl = QLabel("Status Ailments")
        ailment_lbl.setObjectName("sub_group_title")
        outer.addWidget(ailment_lbl)

        ailment_grid = QGridLayout()
        ailment_grid.setHorizontalSpacing(8)
        ailment_grid.setVerticalSpacing(4)
        ailment_grid.setColumnStretch(1, 1)

        row = 0
        ailment_grid.addWidget(_lbl("Stunned"), row, 0)
        self._chk_stun = QCheckBox()
        ailment_grid.addWidget(self._chk_stun, row, 1)
        row += 1

        ailment_grid.addWidget(_lbl("Frozen"), row, 0)
        self._chk_freeze = QCheckBox()
        ailment_grid.addWidget(self._chk_freeze, row, 1)
        row += 1

        ailment_grid.addWidget(_lbl("Petrified"), row, 0)
        self._chk_stone = QCheckBox()
        ailment_grid.addWidget(self._chk_stone, row, 1)
        row += 1

        ailment_grid.addWidget(_lbl("Poisoned"), row, 0)
        self._chk_poison = QCheckBox()
        ailment_grid.addWidget(self._chk_poison, row, 1)

        outer.addLayout(ailment_grid)

        # ── Separator ─────────────────────────────────────────────────────
        outer.addWidget(_hline())

        # ── Monster State (hidden for player targets) ──────────────────────
        self._monster_state_widget = QWidget()
        ms_layout = QVBoxLayout(self._monster_state_widget)
        ms_layout.setContentsMargins(0, 0, 0, 0)
        ms_layout.setSpacing(4)

        ms_lbl = QLabel("Monster State")
        ms_lbl.setObjectName("sub_group_title")
        ms_layout.addWidget(ms_lbl)

        ms_grid = QGridLayout()
        ms_grid.setHorizontalSpacing(8)
        ms_grid.setVerticalSpacing(4)
        ms_grid.setColumnStretch(1, 1)

        ms_row = 0
        ms_grid.addWidget(_lbl("Element"), ms_row, 0)
        ele_row_w = QWidget()
        ele_row = QHBoxLayout(ele_row_w)
        ele_row.setContentsMargins(0, 0, 0, 0)
        ele_row.setSpacing(4)
        self._ele_combo = NoWheelCombo()
        self._ele_combo.addItem("(default)", -1)
        for idx, name in _ELEMENTS:
            self._ele_combo.addItem(name, idx)
        ele_row.addWidget(self._ele_combo)
        ele_row.addWidget(QLabel("Lv"))
        self._ele_lv = LevelWidget(4, include_off=False, item_prefix="")
        self._ele_lv.setEnabled(False)
        ele_row.addWidget(self._ele_lv)
        ele_row.addStretch()
        ms_grid.addWidget(ele_row_w, ms_row, 1)
        ms_row += 1

        ms_grid.addWidget(_lbl("Strip"), ms_row, 0)
        strip_w = QWidget()
        strip_row = QHBoxLayout(strip_w)
        strip_row.setContentsMargins(0, 0, 0, 0)
        strip_row.setSpacing(8)
        self._chk_strip_weapon = QCheckBox("Weapon")
        self._chk_strip_armor  = QCheckBox("Armor")
        self._chk_strip_shield = QCheckBox("Shield")
        self._chk_strip_helm   = QCheckBox("Helm")
        for chk in (self._chk_strip_weapon, self._chk_strip_armor,
                    self._chk_strip_shield, self._chk_strip_helm):
            strip_row.addWidget(chk)
        strip_row.addStretch()
        ms_grid.addWidget(strip_w, ms_row, 1)
        ms_layout.addLayout(ms_grid)

        outer.addWidget(self._monster_state_widget)

        container = QWidget()
        container.setLayout(outer)
        self.add_content_widget(container)

        # ── Connections ───────────────────────────────────────────────────
        self._chk_chaos.stateChanged.connect(self._emit)
        self._lw_provoke.valueChanged.connect(self._emit)
        self._lw_decagi.valueChanged.connect(self._emit)
        self._chk_lex.stateChanged.connect(self._emit)
        self._chk_stun.stateChanged.connect(self._emit)
        self._chk_freeze.stateChanged.connect(self._on_freeze_changed)
        self._chk_stone.stateChanged.connect(self._on_stone_changed)
        self._chk_poison.stateChanged.connect(self._emit)
        self._ele_combo.currentIndexChanged.connect(self._on_ele_changed)
        self._ele_lv.valueChanged.connect(self._emit)
        self._chk_strip_weapon.stateChanged.connect(self._emit)
        self._chk_strip_armor.stateChanged.connect(self._emit)
        self._chk_strip_shield.stateChanged.connect(self._emit)
        self._chk_strip_helm.stateChanged.connect(self._emit)

    # ── Signal helpers ────────────────────────────────────────────────────

    def _emit(self, *_) -> None:
        self.state_changed.emit()

    def _on_freeze_changed(self, state: int) -> None:
        if state and self._chk_stone.isChecked():
            self._chk_stone.blockSignals(True)
            self._chk_stone.setChecked(False)
            self._chk_stone.blockSignals(False)
        self.state_changed.emit()

    def _on_stone_changed(self, state: int) -> None:
        if state and self._chk_freeze.isChecked():
            self._chk_freeze.blockSignals(True)
            self._chk_freeze.setChecked(False)
            self._chk_freeze.blockSignals(False)
        self.state_changed.emit()

    def _on_ele_changed(self) -> None:
        self._ele_lv.setEnabled(self._ele_combo.currentData() != -1)
        self.state_changed.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def set_target_type(self, is_player: bool) -> None:
        """Show/hide monster-specific controls when target type changes."""
        self._monster_state_widget.setVisible(not is_player)

    def collect_into(self, build: PlayerBuild) -> None:
        """Write debuffs that feed the pipeline via build.support_buffs.
        Called from _collect_build() uniformly with all other sections."""
        support = build.support_buffs
        for key in ("SC_ETERNALCHAOS", "SC_PROVOKE", "SC_DECREASEAGI", "PR_LEXAETERNA"):
            support.pop(key, None)
        if self._chk_chaos.isChecked():
            support["SC_ETERNALCHAOS"] = 1
        prov_lv = self._lw_provoke.value()
        if prov_lv:
            support["SC_PROVOKE"] = prov_lv
        decagi_lv = self._lw_decagi.value()
        if decagi_lv:
            support["SC_DECREASEAGI"] = decagi_lv
        if self._chk_lex.isChecked():
            support["PR_LEXAETERNA"] = 1
        build.support_buffs = support

    def apply_to_target(self, target: Target) -> None:
        """Write ailment/element effects directly to resolved Target.
        Called explicitly in _run_battle_pipeline() after target resolution.
        No element restore needed — target is re-resolved each pipeline run."""
        scs: dict[str, int] = {}

        # Monster State — element override (applied first; ailments below may overwrite)
        if not target.is_pc:
            ele = self._ele_combo.currentData()
            if ele != -1:
                target.element = ele
                target.element_level = self._ele_lv.value()

        # Status ailments → target_active_scs + element override for Freeze/Stone
        if self._chk_stun.isChecked():
            scs["SC_STUN"] = 1

        if self._chk_freeze.isChecked():
            scs["SC_FREEZE"] = 1
            target.element = 1        # Ele_Water (status.c:5880-5881, 5901-5902)
            target.element_level = 1

        if self._chk_stone.isChecked():
            scs["SC_STONE"] = 1
            target.element = 2        # Ele_Earth (status.c:5882-5883, 5901-5903)
            target.element_level = 1

        if self._chk_poison.isChecked():
            scs["SC_POISON"] = 1

        # SC_DECREASEAGI: agi -= 2+lv (status.c:7633, 4025-4026)
        decagi_lv = self._lw_decagi.value()
        if decagi_lv:
            scs["SC_DECREASEAGI"] = decagi_lv
            target.agi = max(0, target.agi - (2 + decagi_lv))

        target.target_active_scs = scs

        # Monster State — strip (only for mob targets)
        if not target.is_pc:
            if self._chk_strip_armor.isChecked():
                target.def_ = 0
            if self._chk_strip_shield.isChecked():
                target.def_ = target.def_ * 75 // 100
            if self._chk_strip_helm.isChecked():
                target.def_ = target.def_ * 75 // 100
            # Strip Weapon: no outgoing pipeline effect

    def load_build(self, build: PlayerBuild) -> None:
        """Restore persisted debuff levels from build.support_buffs.
        Ailments and Monster State are session-only and always reset."""
        support = build.support_buffs
        all_widgets = [
            self._chk_chaos, self._lw_provoke, self._lw_decagi, self._chk_lex,
            self._chk_stun, self._chk_freeze, self._chk_stone, self._chk_poison,
            self._ele_combo, self._ele_lv,
            self._chk_strip_weapon, self._chk_strip_armor,
            self._chk_strip_shield, self._chk_strip_helm,
        ]
        for w in all_widgets:
            w.blockSignals(True)

        # Persisted debuffs
        self._chk_chaos.setChecked(bool(support.get("SC_ETERNALCHAOS", False)))
        self._lw_provoke.setValue(int(support.get("SC_PROVOKE", 0)))
        self._lw_decagi.setValue(int(support.get("SC_DECREASEAGI", 0)))
        self._chk_lex.setChecked(bool(support.get("PR_LEXAETERNA", False)))

        # Session-only — always reset on build load
        self._chk_stun.setChecked(False)
        self._chk_freeze.setChecked(False)
        self._chk_stone.setChecked(False)
        self._chk_poison.setChecked(False)
        self._ele_combo.setCurrentIndex(0)   # (default)
        self._ele_lv.setValue(1)
        self._ele_lv.setEnabled(False)
        self._chk_strip_weapon.setChecked(False)
        self._chk_strip_armor.setChecked(False)
        self._chk_strip_shield.setChecked(False)
        self._chk_strip_helm.setChecked(False)

        for w in all_widgets:
            w.blockSignals(False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("combat_field_label")
    return lbl


def _hline() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setObjectName("section_separator")
    return sep
