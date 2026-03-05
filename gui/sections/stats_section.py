from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section

# (display_label, spinbox_key, build_base_attr, build_bonus_attr)
_STATS: list[tuple[str, str, str, str]] = [
    ("STR", "str", "base_str",  "bonus_str"),
    ("AGI", "agi", "base_agi",  "bonus_agi"),
    ("VIT", "vit", "base_vit",  "bonus_vit"),
    ("INT", "int", "base_int",  "bonus_int"),
    ("DEX", "dex", "base_dex",  "bonus_dex"),
    ("LUK", "luk", "base_luk",  "bonus_luk"),
]

# (display_label, spinbox_key, build_attr, min_val, max_val)
_FLAT_BONUSES: list[tuple[str, str, str, int, int]] = [
    ("BATK+",     "batk",      "bonus_batk",        -9999, 9999),
    ("HIT+",      "hit",       "bonus_hit",          -500,  500),
    ("FLEE+",     "flee",      "bonus_flee",         -500,  500),
    ("CRI+",      "cri",       "bonus_cri",          -100,  100),
    ("Hard DEF",  "def",       "equip_def",           0,    999),
    ("Soft DEF+", "def2",      "bonus_def2",         -500,  500),
    ("ASPD%",     "aspd_pct",  "bonus_aspd_percent", -100,  100),
]


class StatsSection(Section):
    """Phase 1.2 — Base stat spinboxes (STR/AGI/VIT/INT/DEX/LUK) + flat bonuses."""

    stats_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_labels: dict[str, QLabel] = {}

        # ── Stat point counter ────────────────────────────────────────────
        self._points_label = QLabel("Base Stat Total: 6")
        self._points_label.setObjectName("stat_points_label")
        self.add_content_widget(self._points_label)

        # ── Main stats grid ───────────────────────────────────────────────
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)

        # Column headers
        for col, header in enumerate(("", "Base", "+", "Bonus", "=", "Total"), start=0):
            if header:
                lbl = QLabel(header)
                lbl.setObjectName("stat_col_header")
                grid.addWidget(lbl, 0, col)

        self._base_spins:  dict[str, QSpinBox] = {}
        self._bonus_spins: dict[str, QSpinBox] = {}
        self._total_labels: dict[str, QLabel]  = {}

        for row, (display, key_s, _base_attr, _bonus_attr) in enumerate(_STATS, start=1):
            name_lbl = QLabel(display)
            name_lbl.setObjectName("stat_row_label")
            grid.addWidget(name_lbl, row, 0)

            base_spin = QSpinBox()
            base_spin.setRange(1, 99)
            base_spin.setValue(1)
            base_spin.setFixedWidth(58)
            self._base_spins[key_s] = base_spin
            grid.addWidget(base_spin, row, 1)

            plus_lbl = QLabel("+")
            plus_lbl.setObjectName("stat_operator")
            grid.addWidget(plus_lbl, row, 2)

            bonus_spin = QSpinBox()
            bonus_spin.setRange(-99, 999)
            bonus_spin.setValue(0)
            bonus_spin.setFixedWidth(65)
            self._bonus_spins[key_s] = bonus_spin
            grid.addWidget(bonus_spin, row, 3)

            eq_lbl = QLabel("=")
            eq_lbl.setObjectName("stat_operator")
            grid.addWidget(eq_lbl, row, 4)

            total_lbl = QLabel("1")
            total_lbl.setObjectName("stat_total")
            total_lbl.setFixedWidth(38)
            self._total_labels[key_s] = total_lbl
            grid.addWidget(total_lbl, row, 5)

            base_spin.valueChanged.connect(self._on_stat_changed)
            bonus_spin.valueChanged.connect(self._on_stat_changed)

        self.add_content_widget(grid_widget)

        # ── Flat bonuses sub-group ────────────────────────────────────────
        bonus_header = QLabel("— Flat Bonuses —")
        bonus_header.setObjectName("stat_sub_header")
        self.add_content_widget(bonus_header)

        bonus_grid_widget = QWidget()
        bonus_grid = QGridLayout(bonus_grid_widget)
        bonus_grid.setContentsMargins(0, 0, 0, 0)
        bonus_grid.setHorizontalSpacing(6)
        bonus_grid.setVerticalSpacing(3)

        self._flat_spins: dict[str, QSpinBox] = {}
        cols_per_row = 4  # label+spin pairs per row

        for i, (display, key_s, _attr, min_v, max_v) in enumerate(_FLAT_BONUSES):
            row = i // (cols_per_row // 2)
            col_base = (i % (cols_per_row // 2)) * 2

            lbl = QLabel(display + ":")
            lbl.setObjectName("flat_bonus_label")
            bonus_grid.addWidget(lbl, row, col_base)

            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(0)
            spin.setFixedWidth(65)
            self._flat_spins[key_s] = spin
            bonus_grid.addWidget(spin, row, col_base + 1)

            spin.valueChanged.connect(self._on_stat_changed)

        self.add_content_widget(bonus_grid_widget)

    # ── Internal ──────────────────────────────────────────────────────────

    def _on_stat_changed(self) -> None:
        self._update_totals()
        self.stats_changed.emit()

    def _update_totals(self) -> None:
        total_base = 0
        for key_s, *_ in [(k, ) for k in self._base_spins]:
            base = self._base_spins[key_s].value()
            bonus = self._bonus_spins[key_s].value()
            self._total_labels[key_s].setText(str(base + bonus))
            total_base += base
        self._points_label.setText(f"Base Stat Total: {total_base}")
        if self._compact_widget is not None:
            self._update_compact_labels()

    def _update_compact_labels(self) -> None:
        for display, key_s, *_ in _STATS:
            lbl = self._compact_labels.get(key_s)
            if lbl is not None:
                base = self._base_spins[key_s].value()
                bonus = self._bonus_spins[key_s].value()
                lbl.setText(f"{display}: {base}+{bonus}")

    def _build_compact_widget(self) -> None:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        for i, (display, key_s, *_) in enumerate(_STATS):
            row = i // 3
            col = i % 3
            lbl = QLabel()
            lbl.setObjectName("compact_stat_label")
            self._compact_labels[key_s] = lbl
            grid.addWidget(lbl, row, col)

        w.setVisible(False)
        self._compact_widget = w
        self.layout().addWidget(w)
        self._update_compact_labels()

    # ── Compact API ────────────────────────────────────────────────────────

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

    def load_build(self, build: PlayerBuild) -> None:
        """Populate spinboxes from build without emitting change signals."""
        all_spins = (
            list(self._base_spins.values())
            + list(self._bonus_spins.values())
            + list(self._flat_spins.values())
        )
        for spin in all_spins:
            spin.blockSignals(True)

        self._base_spins["str"].setValue(build.base_str)
        self._base_spins["agi"].setValue(build.base_agi)
        self._base_spins["vit"].setValue(build.base_vit)
        self._base_spins["int"].setValue(build.base_int)
        self._base_spins["dex"].setValue(build.base_dex)
        self._base_spins["luk"].setValue(build.base_luk)

        self._bonus_spins["str"].setValue(build.bonus_str)
        self._bonus_spins["agi"].setValue(build.bonus_agi)
        self._bonus_spins["vit"].setValue(build.bonus_vit)
        self._bonus_spins["int"].setValue(build.bonus_int)
        self._bonus_spins["dex"].setValue(build.bonus_dex)
        self._bonus_spins["luk"].setValue(build.bonus_luk)

        self._flat_spins["batk"].setValue(build.bonus_batk)
        self._flat_spins["hit"].setValue(build.bonus_hit)
        self._flat_spins["flee"].setValue(build.bonus_flee)
        self._flat_spins["cri"].setValue(build.bonus_cri)
        self._flat_spins["def"].setValue(build.equip_def)
        self._flat_spins["def2"].setValue(build.bonus_def2)
        self._flat_spins["aspd_pct"].setValue(build.bonus_aspd_percent)

        for spin in all_spins:
            spin.blockSignals(False)
        self._update_totals()

    def collect_into(self, build: PlayerBuild) -> None:
        """Write section state into an existing PlayerBuild in-place."""
        build.base_str = self._base_spins["str"].value()
        build.base_agi = self._base_spins["agi"].value()
        build.base_vit = self._base_spins["vit"].value()
        build.base_int = self._base_spins["int"].value()
        build.base_dex = self._base_spins["dex"].value()
        build.base_luk = self._base_spins["luk"].value()

        build.bonus_str = self._bonus_spins["str"].value()
        build.bonus_agi = self._bonus_spins["agi"].value()
        build.bonus_vit = self._bonus_spins["vit"].value()
        build.bonus_int = self._bonus_spins["int"].value()
        build.bonus_dex = self._bonus_spins["dex"].value()
        build.bonus_luk = self._bonus_spins["luk"].value()

        build.bonus_batk = self._flat_spins["batk"].value()
        build.bonus_hit  = self._flat_spins["hit"].value()
        build.bonus_flee = self._flat_spins["flee"].value()
        build.bonus_cri  = self._flat_spins["cri"].value()
        build.equip_def  = self._flat_spins["def"].value()
        build.bonus_def2 = self._flat_spins["def2"].value()
        build.bonus_aspd_percent = self._flat_spins["aspd_pct"].value()
