from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section

# (display_label, dict_key, min_val, max_val)
_STATS: list[tuple[str, str, int, int]] = [
    ("STR",       "str",      -99,  999),
    ("AGI",       "agi",      -99,  999),
    ("VIT",       "vit",      -99,  999),
    ("INT",       "int",      -99,  999),
    ("DEX",       "dex",      -99,  999),
    ("LUK",       "luk",      -99,  999),
    ("BATK",      "batk",  -9999, 9999),
    ("HIT",       "hit",    -500,  500),
    ("FLEE",      "flee",   -500,  500),
    ("CRI",       "cri",    -100,  100),
    ("Hard DEF",  "def",    -999,  999),
    ("Hard MDEF", "mdef",   -999,  999),
    ("ASPD%",     "aspd_pct", -100, 100),
    ("MaxHP",     "maxhp",  -9999, 9999),
    ("MaxSP",     "maxsp",  -9999, 9999),
]


class ManualAdjSection(Section):
    """
    G47 — Manual numeric bonus entry for any stat. Pure escape hatch for edge cases
    not covered by any other section. No source attribution required.

    Known game-mechanic bonuses (gear scripts, consumables, skill buffs) should be
    entered in their proper sections instead of here.
    """

    bonuses_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        note_lbl = QLabel(
            "Raw numeric adjustments for testing or uncategorised sources.\n"
            "Use Equipment / Passives / Active Items for known bonuses."
        )
        note_lbl.setObjectName("active_items_note")
        note_lbl.setWordWrap(True)
        self.add_content_widget(note_lbl)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)

        self._spins: dict[str, QSpinBox] = {}
        cols = 2  # stat pairs per row

        for i, (display, key_s, min_v, max_v) in enumerate(_STATS):
            row = i // cols
            col_base = (i % cols) * 3

            lbl = QLabel(display + ":")
            lbl.setObjectName("flat_bonus_label")
            grid.addWidget(lbl, row, col_base)

            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(0)
            spin.setFixedWidth(65)
            self._spins[key_s] = spin
            grid.addWidget(spin, row, col_base + 1)

            spin.valueChanged.connect(self._on_changed)

        self.add_content_widget(grid_widget)

    def _on_changed(self) -> None:
        self.bonuses_changed.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        for spin in self._spins.values():
            spin.blockSignals(True)
        bonuses = build.manual_adj_bonuses
        for key_s, spin in self._spins.items():
            spin.setValue(bonuses.get(key_s, 0))
        for spin in self._spins.values():
            spin.blockSignals(False)

    def collect_into(self, build: PlayerBuild) -> None:
        build.manual_adj_bonuses = {
            key_s: spin.value()
            for key_s, spin in self._spins.items()
            if spin.value() != 0
        }

    def get_bonuses(self) -> dict[str, int]:
        """Return current bonus dict (non-zero entries only)."""
        return {k: s.value() for k, s in self._spins.items() if s.value() != 0}
