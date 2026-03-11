from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section
from gui.widgets import NoWheelCombo, NoWheelSpin
from gui.widgets.collapsible_sub_group import CollapsibleSubGroup

# Pre-renewal job IDs — Hercules constants.conf Job_* values.
_JOB_NAMES: list[tuple[int, str]] = [
    (0,    "Novice"),
    (1,    "Swordman"),
    (2,    "Mage"),
    (3,    "Archer"),
    (4,    "Acolyte"),
    (5,    "Merchant"),
    (6,    "Thief"),
    (7,    "Knight"),
    (8,    "Priest"),
    (9,    "Wizard"),
    (10,   "Blacksmith"),
    (11,   "Hunter"),
    (12,   "Assassin"),
    (14,   "Crusader"),
    (15,   "Monk"),
    (16,   "Sage"),
    (17,   "Rogue"),
    (18,   "Alchemist"),
    (19,   "Bard"),
    (20,   "Dancer"),
    (23,   "Super Novice"),
    (24,   "Gunslinger"),
    (25,   "Ninja"),
    (4008, "Lord Knight"),
    (4009, "High Priest"),
    (4010, "High Wizard"),
    (4011, "Mastersmith"),
    (4012, "Sniper"),
    (4013, "Assassin Cross"),
    (4015, "Paladin"),
    (4016, "Champion"),
    (4017, "Scholar"),
    (4018, "Stalker"),
    (4019, "Creator"),
    (4020, "Clown"),
    (4021, "Gypsy"),
]


# Manual Adjustments — same stat set as the old ManualAdjSection.
# Pure numeric escape hatch for uncategorised bonuses.
_MANUAL_ADJ_STATS: list[tuple[str, str, int, int]] = [
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


class BuildHeaderSection(Section):
    """Phase 1.1 — Build name, job, base level, job level + Manual Adjustments sub-group."""

    build_name_changed = Signal(str)
    job_changed = Signal(int)
    level_changed = Signal()
    bonuses_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        # ── Name row ──────────────────────────────────────────────────────
        name_row = QWidget()
        name_layout = QHBoxLayout(name_row)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(6)
        name_layout.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Build name…")
        self._name_edit.textChanged.connect(self.build_name_changed)
        name_layout.addWidget(self._name_edit, stretch=1)
        self.add_content_widget(name_row)

        # ── Job / Level row ───────────────────────────────────────────────
        job_row = QWidget()
        job_layout = QHBoxLayout(job_row)
        job_layout.setContentsMargins(0, 0, 0, 0)
        job_layout.setSpacing(6)

        job_layout.addWidget(QLabel("Job:"))
        self._job_combo = NoWheelCombo()
        for job_id, job_name in _JOB_NAMES:
            self._job_combo.addItem(job_name, job_id)
        self._job_combo.currentIndexChanged.connect(self._emit_job_changed)
        job_layout.addWidget(self._job_combo, stretch=1)

        job_layout.addSpacing(8)
        job_layout.addWidget(QLabel("Base Lv:"))
        self._base_lv = NoWheelSpin()
        self._base_lv.setRange(1, 99)
        self._base_lv.setFixedWidth(55)
        self._base_lv.valueChanged.connect(self.level_changed)
        job_layout.addWidget(self._base_lv)

        job_layout.addSpacing(8)
        job_layout.addWidget(QLabel("Job Lv:"))
        self._job_lv = NoWheelSpin()
        self._job_lv.setRange(1, 70)
        self._job_lv.setFixedWidth(55)
        self._job_lv.valueChanged.connect(self.level_changed)
        job_layout.addWidget(self._job_lv)

        self.add_content_widget(job_row)

        # ── Manual Adjustments sub-group ──────────────────────────────────
        self._manual_adj_sub = CollapsibleSubGroup("Manual Adjustments", default_collapsed=True)

        note_lbl = QLabel(
            "Raw numeric adjustments for testing or uncategorised sources.\n"
            "Use Equipment / Passives / Buffs for known bonuses."
        )
        note_lbl.setObjectName("active_items_note")
        note_lbl.setWordWrap(True)
        self._manual_adj_sub.add_content_widget(note_lbl)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)

        self._manual_adj_spins: dict[str, QSpinBox] = {}
        cols = 2
        for i, (display, key_s, min_v, max_v) in enumerate(_MANUAL_ADJ_STATS):
            row = i // cols
            col_base = (i % cols) * 3
            lbl = QLabel(display + ":")
            lbl.setObjectName("flat_bonus_label")
            grid.addWidget(lbl, row, col_base)
            spin = NoWheelSpin()
            spin.setRange(min_v, max_v)
            spin.setValue(0)
            spin.setFixedWidth(65)
            self._manual_adj_spins[key_s] = spin
            grid.addWidget(spin, row, col_base + 1)
            spin.valueChanged.connect(self._on_manual_adj_changed)

        self._manual_adj_sub.add_content_widget(grid_widget)
        self.add_content_widget(self._manual_adj_sub)

    # ── Internal ──────────────────────────────────────────────────────────

    def _emit_job_changed(self) -> None:
        self.job_changed.emit(self._job_combo.currentData() or 0)

    def _on_manual_adj_changed(self) -> None:
        self.bonuses_changed.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        """Populate all widgets from build without emitting change signals."""
        for w in (self._name_edit, self._job_combo, self._base_lv, self._job_lv):
            w.blockSignals(True)
        self._name_edit.setText(build.name)
        idx = self._job_combo.findData(build.job_id)
        if idx >= 0:
            self._job_combo.setCurrentIndex(idx)
        self._base_lv.setValue(build.base_level)
        self._job_lv.setValue(build.job_level)
        for w in (self._name_edit, self._job_combo, self._base_lv, self._job_lv):
            w.blockSignals(False)

        bonuses = build.manual_adj_bonuses
        for spin in self._manual_adj_spins.values():
            spin.blockSignals(True)
        for key_s, spin in self._manual_adj_spins.items():
            spin.setValue(bonuses.get(key_s, 0))
        for spin in self._manual_adj_spins.values():
            spin.blockSignals(False)

    def collect_into(self, build: PlayerBuild) -> None:
        """Write section state into an existing PlayerBuild in-place."""
        build.name = self._name_edit.text()
        build.job_id = self._job_combo.currentData() or 0
        build.base_level = self._base_lv.value()
        build.job_level = self._job_lv.value()
        build.manual_adj_bonuses = {
            key_s: spin.value()
            for key_s, spin in self._manual_adj_spins.items()
            if spin.value() != 0
        }
