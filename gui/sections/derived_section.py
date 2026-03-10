from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from core.models.status import StatusData
from gui.section import Section


class DerivedSection(Section):
    """
    Phase 1.3 — Read-only derived stats driven by StatusCalculator.

    Call refresh(status) whenever the build changes; no user-editable widgets here.
    compact_view: compact block with ATK / DEF / FLEE / HIT / CRI.
    """

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_values: dict[str, QLabel] = {}

        # ── Full grid: label + value ───────────────────────────────────────
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(3)

        self._value_labels: dict[str, QLabel] = {}

        rows = [
            ("BATK",  "batk",  "—"),
            ("MATK",  "matk",  "—"),   # shown as "min–max range"
            ("DEF",   "def",   "—"),   # shown as "hard + soft"
            ("MDEF",  "mdef",  "—"),   # shown as "hard + soft"
            ("FLEE",  "flee",  "—"),   # shown as "flee + perfect_dodge"
            ("HIT",   "hit",   "—"),
            ("CRI",   "cri",   "—"),
            ("ASPD",  "aspd",  "—"),
            ("HP",       "hp",       "—"),
            ("HP Regen", "hp_regen", "—"),
            ("SP",       "sp",       "—"),
            ("SP Regen", "sp_regen", "—"),
            # SC_POEMBRAGI / SC_SERVICEFORYU — hidden when 0
            ("Cast Red.",  "cast_red",  "—"),
            ("ACD Red.",   "acd_red",   "—"),
            ("SP Cost Red.", "sp_cost_red", "—"),
        ]

        # Keys for rows that should be hidden when value is zero
        self._optional_rows: set[str] = {"cast_red", "acd_red", "sp_cost_red"}
        self._row_name_labels: dict[str, QLabel] = {}

        for row_i, (display, key_s, default) in enumerate(rows):
            name_lbl = QLabel(display)
            name_lbl.setObjectName("derived_stat_label")
            grid.addWidget(name_lbl, row_i, 0)
            self._row_name_labels[key_s] = name_lbl

            val_lbl = QLabel(default)
            val_lbl.setObjectName("derived_stat_value")
            self._value_labels[key_s] = val_lbl
            grid.addWidget(val_lbl, row_i, 1)

            if key_s in self._optional_rows:
                name_lbl.setVisible(False)
                val_lbl.setVisible(False)

        self.add_content_widget(grid_widget)

    # ── Compact API ────────────────────────────────────────────────────────

    def _build_compact_widget(self) -> None:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(3)

        compact_rows = [("BATK", "batk"), ("DEF", "def"), ("FLEE", "flee"),
                        ("HIT", "hit"), ("CRI", "cri")]
        for row_i, (display, key_s) in enumerate(compact_rows):
            name_lbl = QLabel(display)
            name_lbl.setObjectName("derived_stat_label")
            grid.addWidget(name_lbl, row_i, 0)

            val_lbl = QLabel("—")
            val_lbl.setObjectName("derived_stat_value")
            self._compact_values[key_s] = val_lbl
            grid.addWidget(val_lbl, row_i, 1)

        w.setVisible(False)
        self._compact_widget = w
        self.layout().addWidget(w)

    def _enter_compact_view(self) -> None:
        self._pre_compact_collapsed = self._is_collapsed
        if self._compact_widget is None:
            self._build_compact_widget()
        for key_s, clbl in self._compact_values.items():
            full_lbl = self._value_labels.get(key_s)
            if full_lbl:
                clbl.setText(full_lbl.text())
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

    def refresh(self, status: StatusData) -> None:
        """Update all displayed values from a freshly computed StatusData."""
        cri_pct = status.cri / 10.0  # cri stored in 0.1% units

        self._value_labels["batk"].setText(str(status.batk))
        self._value_labels["matk"].setText(f"{status.matk_min}–{status.matk_max}")
        self._value_labels["def"].setText(f"{status.def_} + {status.def2}")
        self._value_labels["mdef"].setText(f"{status.mdef} + {status.mdef2}")
        flee_str = str(status.flee)
        if status.flee2:
            flee_str += f" + {status.flee2}"
        self._value_labels["flee"].setText(flee_str)
        self._value_labels["hit"].setText(str(status.hit))
        self._value_labels["cri"].setText(f"{cri_pct:.1f}%")
        self._value_labels["aspd"].setText(f"{status.aspd:.1f}")
        self._value_labels["hp"].setText(str(status.max_hp))
        self._value_labels["hp_regen"].setText(f"{status.hp_regen}/tick")
        self._value_labels["sp"].setText(str(status.max_sp))
        self._value_labels["sp_regen"].setText(f"{status.sp_regen}/tick")

        # Optional rows: show only when non-zero (SC_POEMBRAGI / SC_SERVICEFORYU)
        self._set_optional("cast_red",    status.cast_time_reduction_pct,        f"{status.cast_time_reduction_pct}%")
        self._set_optional("acd_red",     status.after_cast_delay_reduction_pct,  f"{status.after_cast_delay_reduction_pct}%")
        self._set_optional("sp_cost_red", status.sp_cost_reduction_pct,           f"{status.sp_cost_reduction_pct}%")

        # Keep compact labels in sync
        for key_s, clbl in self._compact_values.items():
            full_lbl = self._value_labels.get(key_s)
            if full_lbl:
                clbl.setText(full_lbl.text())

    def _set_optional(self, key_s: str, value: int, text: str) -> None:
        visible = value != 0
        self._row_name_labels[key_s].setVisible(visible)
        lbl = self._value_labels[key_s]
        lbl.setVisible(visible)
        if visible:
            lbl.setText(text)
