from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section
from gui.widgets import LevelWidget


class PlayerDebuffsSection(Section):
    """
    Session R — debuffs the enemy has applied to the player.
    Affects StatusCalculator outputs (AGI/LUK/BATK/HIT/FLEE).
    All widgets write to build.player_active_scs.
    """

    changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1)

        row = 0
        grid.addWidget(_lbl("Curse"), row, 0)
        self._chk_curse = QCheckBox()
        grid.addWidget(self._chk_curse, row, 1)
        row += 1

        grid.addWidget(_lbl("Blind"), row, 0)
        self._chk_blind = QCheckBox()
        grid.addWidget(self._chk_blind, row, 1)
        row += 1

        grid.addWidget(_lbl("Decrease AGI"), row, 0)
        self._lw_decagi = LevelWidget(10, include_off=True, item_prefix="Lv ")
        grid.addWidget(self._lw_decagi, row, 1)

        container = QWidget()
        container.setLayout(grid)
        self.add_content_widget(container)

        self._chk_curse.stateChanged.connect(self._emit)
        self._chk_blind.stateChanged.connect(self._emit)
        self._lw_decagi.valueChanged.connect(self._emit)

    def _emit(self, *_) -> None:
        self.changed.emit()

    # ── Public API ─────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        scs = build.player_active_scs
        for w in (self._chk_curse, self._chk_blind, self._lw_decagi):
            w.blockSignals(True)
        self._chk_curse.setChecked(bool(scs.get("SC_CURSE", False)))
        self._chk_blind.setChecked(bool(scs.get("SC_BLIND", False)))
        self._lw_decagi.setValue(int(scs.get("SC_DECREASEAGI", 0)))
        for w in (self._chk_curse, self._chk_blind, self._lw_decagi):
            w.blockSignals(False)

    def collect_into(self, build: PlayerBuild) -> None:
        scs: dict[str, int] = {}
        if self._chk_curse.isChecked():
            scs["SC_CURSE"] = 1
        if self._chk_blind.isChecked():
            scs["SC_BLIND"] = 1
        decagi_lv = self._lw_decagi.value()
        if decagi_lv:
            scs["SC_DECREASEAGI"] = decagi_lv
        build.player_active_scs = scs


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("combat_field_label")
    return lbl
