from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QWidget,
)

from core.models.damage import BattleResult
from gui.section import Section

_DASH = "—"


class SummarySection(Section):
    """Phase 2.2 — Damage summary card (normal range, crit range, hit%)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(5)

        # Column headers
        for col, text in enumerate(("", "Min", "Avg", "Max"), start=0):
            hdr = QLabel(text)
            hdr.setObjectName("summary_col_header")
            hdr.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(hdr, 0, col)

        # Normal row (row 1)
        normal_lbl = QLabel("Normal")
        normal_lbl.setObjectName("summary_label")
        grid.addWidget(normal_lbl, 1, 0)

        self._n_min = self._make_val()
        self._n_avg = self._make_val()
        self._n_max = self._make_val()
        grid.addWidget(self._n_min, 1, 1)
        grid.addWidget(self._n_avg, 1, 2)
        grid.addWidget(self._n_max, 1, 3)

        # Crit row (row 2)
        crit_lbl = QLabel("Crit")
        crit_lbl.setObjectName("summary_label")
        grid.addWidget(crit_lbl, 2, 0)

        self._c_min = self._make_val()
        self._c_avg = self._make_val()
        self._c_max = self._make_val()
        grid.addWidget(self._c_min, 2, 1)
        grid.addWidget(self._c_avg, 2, 2)
        grid.addWidget(self._c_max, 2, 3)

        self._crit_pct = QLabel(_DASH)
        self._crit_pct.setObjectName("summary_crit_pct")
        self._crit_pct.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self._crit_pct, 2, 4)

        # Double-hit proc row (row 3) — hidden until a proc branch is present
        self._double_lbl = QLabel("Double")
        self._double_lbl.setObjectName("summary_label")
        grid.addWidget(self._double_lbl, 3, 0)

        self._d_min = self._make_val()
        self._d_avg = self._make_val()
        self._d_max = self._make_val()
        grid.addWidget(self._d_min, 3, 1)
        grid.addWidget(self._d_avg, 3, 2)
        grid.addWidget(self._d_max, 3, 3)

        self._proc_pct = QLabel(_DASH)
        self._proc_pct.setObjectName("summary_crit_pct")
        self._proc_pct.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self._proc_pct, 3, 4)

        self._double_row_widgets = [
            self._double_lbl, self._d_min, self._d_avg, self._d_max, self._proc_pct,
        ]
        for w in self._double_row_widgets:
            w.setVisible(False)

        # Hit row (row 4)
        hit_lbl = QLabel("Hit")
        hit_lbl.setObjectName("summary_label")
        grid.addWidget(hit_lbl, 4, 0)

        self._hit_pct = QLabel(_DASH)
        self._hit_pct.setObjectName("summary_hit_pct")
        grid.addWidget(self._hit_pct, 4, 1, 1, 2)

        self._pdodge_pct = QLabel(_DASH)
        self._pdodge_pct.setObjectName("summary_hit_pct")
        self._pdodge_pct.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self._pdodge_pct, 4, 3, 1, 2)

        # DPS row (row 5) — always visible
        dps_lbl = QLabel("DPS")
        dps_lbl.setObjectName("summary_label")
        grid.addWidget(dps_lbl, 5, 0)

        self._dps_val = QLabel(_DASH)
        self._dps_val.setObjectName("summary_value")
        self._dps_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self._dps_val, 5, 1, 1, 3)

        grid.setColumnStretch(5, 1)

        container = QWidget()
        container.setLayout(grid)
        self.add_content_widget(container)

    @staticmethod
    def _make_val() -> QLabel:
        lbl = QLabel(_DASH)
        lbl.setObjectName("summary_value")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    # ── Public API ────────────────────────────────────────────────────────

    def refresh(self, result: Optional[BattleResult]) -> None:
        if result is None:
            self._n_min.setText(_DASH)
            self._n_avg.setText(_DASH)
            self._n_max.setText(_DASH)
            self._c_min.setText(_DASH)
            self._c_avg.setText(_DASH)
            self._c_max.setText(_DASH)
            self._crit_pct.setText(_DASH)
            for w in self._double_row_widgets:
                w.setVisible(False)
            self._hit_pct.setText(_DASH)
            self._pdodge_pct.setText(_DASH)
            self._dps_val.setText(_DASH)
            return

        n = result.normal
        # G16: Katar second hit — show "first + second" when present
        if result.katar_second is not None:
            k = result.katar_second
            self._n_min.setText(f"{n.min_damage} + {k.min_damage}")
            self._n_avg.setText(f"{n.avg_damage} + {k.avg_damage}")
            self._n_max.setText(f"{n.max_damage} + {k.max_damage}")
        else:
            self._n_min.setText(str(n.min_damage))
            self._n_avg.setText(str(n.avg_damage))
            self._n_max.setText(str(n.max_damage))

        if result.crit is not None:
            c = result.crit
            if result.katar_second_crit is not None:
                kc = result.katar_second_crit
                self._c_min.setText(f"{c.min_damage} + {kc.min_damage}")
                self._c_avg.setText(f"{c.avg_damage} + {kc.avg_damage}")
                self._c_max.setText(f"{c.max_damage} + {kc.max_damage}")
            else:
                self._c_min.setText(str(c.min_damage))
                self._c_avg.setText(str(c.avg_damage))
                self._c_max.setText(str(c.max_damage))
            # Effective crit%: crit and proc are mutually exclusive (battle.c:4926).
            eff_crit = result.crit_chance * (1.0 - result.proc_chance / 100.0)
            self._crit_pct.setText(f"{eff_crit:.1f}% crit")
        else:
            self._c_min.setText(_DASH)
            self._c_avg.setText(_DASH)
            self._c_max.setText(_DASH)
            self._crit_pct.setText("—")

        # G54: Double-hit proc row — show only when proc branch is present
        if result.double_hit is not None:
            d = result.double_hit
            self._d_min.setText(str(d.min_damage))
            self._d_avg.setText(str(d.avg_damage))
            self._d_max.setText(str(d.max_damage))
            self._proc_pct.setText(f"{result.proc_chance:.1f}% proc")
            for w in self._double_row_widgets:
                w.setVisible(True)
        else:
            for w in self._double_row_widgets:
                w.setVisible(False)

        self._hit_pct.setText(f"{result.hit_chance:.1f}%")
        self._pdodge_pct.setText(f"pdodge {result.perfect_dodge:.1f}%")

        # DPS row — always shown; 0.0 before first calculation
        self._dps_val.setText(f"{result.dps:.1f}")
