from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section
from gui.widgets import NoWheelSpin

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


class ActiveItemsSection(Section):
    """
    G46 — Temporary catch-all section for consumable item effects (foods, potions,
    triggered item script bonuses) that do not yet have dedicated tracking sections.

    NOTE: This section is intentionally a temporary measure. As proper subsections
    for specific consumable/item effect categories are implemented, entries will be
    migrated out and this section will be narrowed or removed.
    """

    bonuses_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        note_lbl = QLabel(
            "Temporary catch-all for consumable effects (foods, potions, etc.).\n"
            "Known script bonuses belong in Equipment / Passives & Buffs."
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

            spin = NoWheelSpin()
            spin.setRange(min_v, max_v)
            spin.setValue(0)
            spin.setFixedWidth(65)
            self._spins[key_s] = spin
            grid.addWidget(spin, row, col_base + 1)

            spin.valueChanged.connect(self._on_changed)

        self.add_content_widget(grid_widget)

        source_lbl = QLabel("Source / Notes:")
        source_lbl.setObjectName("flat_bonus_label")
        self.add_content_widget(source_lbl)

        self._source_edit = QLineEdit()
        self._source_edit.setPlaceholderText("e.g. Poring Coin food +10 STR")
        self._source_edit.setObjectName("active_items_source")
        self.add_content_widget(self._source_edit)

    def _on_changed(self) -> None:
        self.bonuses_changed.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        for spin in self._spins.values():
            spin.blockSignals(True)
        bonuses = build.active_items_bonuses
        for key_s, spin in self._spins.items():
            spin.setValue(bonuses.get(key_s, 0))
        for spin in self._spins.values():
            spin.blockSignals(False)

    def collect_into(self, build: PlayerBuild) -> None:
        build.active_items_bonuses = {
            key_s: spin.value()
            for key_s, spin in self._spins.items()
            if spin.value() != 0
        }

    def get_bonuses(self) -> dict[str, int]:
        """Return current bonus dict (non-zero entries only)."""
        return {k: s.value() for k, s in self._spins.items() if s.value() != 0}
