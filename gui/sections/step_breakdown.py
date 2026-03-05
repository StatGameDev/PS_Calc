from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models.damage import BattleResult, DamageStep
from gui.section import Section

_DASH = "—"
_COL_NAME = 0
_COL_NORMAL = 1
_COL_CRIT = 2
_COL_SOURCE = 3


def _fmt_step(step: Optional[DamageStep]) -> str:
    if step is None:
        return _DASH
    if step.max_value == 0 or step.min_value == step.max_value:
        return str(step.value)
    return f"{step.min_value}–{step.value}–{step.max_value}"


class _VerticalBar(QWidget):
    """
    Narrow clickable vertical strip shown on the right edge of the compact
    widget. Draws rotated 'Steps ▶/◀' text. Emits clicked() on left press.
    """

    clicked = Signal()
    _WIDTH = 22

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = False
        self.setFixedWidth(self._WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setToolTip("Toggle step list")

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(self.rect(), QColor("#252830"))

        p.save()
        p.translate(self._WIDTH // 2, self.height() // 2)
        p.rotate(-90)

        font = QFont()
        font.setPointSize(9)
        p.setFont(font)
        p.setPen(QColor("#6a7383"))

        arrow = "◀" if self._expanded else "▶"
        text = f"Steps  {arrow}"
        fm = p.fontMetrics()
        br = fm.boundingRect(text)
        p.drawText(-br.width() // 2, br.height() // 3, text)
        p.restore()


class StepBreakdownSection(Section):
    """Phase 2.3 — Step-by-step pipeline table with formula/source toggles.

    Full view (combat focused): Normal/Crit table with Show Source toggle.
    Compact view (builder focused): vertical bar on right edge. Clicking the
    bar expands a scrollable step+value list; clicking again collapses it.
    Only one of {full table, compact bar} is ever visible at a time.
    """

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._result: Optional[BattleResult] = None
        self._compact_widget: Optional[QWidget] = None
        self._compact_bar: Optional[_VerticalBar] = None
        self._compact_rows_widget: Optional[QScrollArea] = None
        self._compact_rows_layout: Optional[QVBoxLayout] = None
        self._compact_rows_inner: Optional[QWidget] = None

        # ── Controls row ──────────────────────────────────────────────────
        ctrl_row = QHBoxLayout()
        ctrl_row.setContentsMargins(0, 0, 0, 4)

        self._show_source_btn = QPushButton("Show Source")
        self._show_source_btn.setCheckable(True)
        self._show_source_btn.setFixedWidth(100)
        self._show_source_btn.toggled.connect(self._on_source_toggled)
        ctrl_row.addWidget(self._show_source_btn)
        ctrl_row.addStretch()

        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_row)
        self.add_content_widget(ctrl_widget)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Step", "Normal", "Crit", "Source"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(_COL_NAME, 180)
        self._table.setColumnWidth(_COL_NORMAL, 120)
        self._table.setColumnWidth(_COL_CRIT, 120)
        self._table.setColumnHidden(_COL_SOURCE, True)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._table.setMinimumHeight(120)
        self.add_content_widget(self._table)

        self._set_placeholder()

    # ── Source toggle ──────────────────────────────────────────────────────

    def _on_source_toggled(self, checked: bool) -> None:
        self._table.setColumnHidden(_COL_SOURCE, not checked)
        self._show_source_btn.setText("Hide Source" if checked else "Show Source")

    # ── Table population ──────────────────────────────────────────────────

    def _set_placeholder(self) -> None:
        self._table.setRowCount(1)
        item = QTableWidgetItem("No data yet")
        item.setForeground(QColor("#4a5060"))
        self._table.setItem(0, _COL_NAME, item)
        for col in (_COL_NORMAL, _COL_CRIT, _COL_SOURCE):
            self._table.setItem(0, col, QTableWidgetItem(""))

    def _populate_table(self, result: BattleResult) -> None:
        normal_steps = result.normal.steps
        crit_by_name: dict[str, DamageStep] = {}
        crit_only_steps: list[DamageStep] = []
        if result.crit is not None:
            normal_names = {s.name for s in normal_steps}
            for s in result.crit.steps:
                if s.name in normal_names:
                    crit_by_name[s.name] = s
                else:
                    crit_only_steps.append(s)

        rows = list(normal_steps) + crit_only_steps
        self._table.setRowCount(len(rows))

        for row_idx, step in enumerate(rows):
            is_crit_only = step not in normal_steps

            name_item = QTableWidgetItem(step.name)
            tooltip = step.note
            if step.formula:
                tooltip += f"\n\nFormula: {step.formula}"
            name_item.setToolTip(tooltip)
            self._table.setItem(row_idx, _COL_NAME, name_item)

            if is_crit_only:
                normal_item = QTableWidgetItem(_DASH)
                crit_item = QTableWidgetItem(_fmt_step(step))
            else:
                normal_item = QTableWidgetItem(_fmt_step(step))
                crit_step = crit_by_name.get(step.name)
                crit_item = QTableWidgetItem(_fmt_step(crit_step))

            normal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            crit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if result.crit is not None:
                crit_item.setForeground(QColor("#f0a020"))

            self._table.setItem(row_idx, _COL_NORMAL, normal_item)
            self._table.setItem(row_idx, _COL_CRIT, crit_item)

            src_item = QTableWidgetItem(step.hercules_ref)
            src_item.setForeground(QColor("#6b7480"))
            self._table.setItem(row_idx, _COL_SOURCE, src_item)

        self._table.resizeRowsToContents()

    # ── Compact rows helper ───────────────────────────────────────────────

    def _rebuild_compact_rows(self, result: Optional[BattleResult]) -> None:
        if self._compact_rows_layout is None:
            return
        while self._compact_rows_layout.count():
            item = self._compact_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if result is None:
            return
        for i, step in enumerate(result.normal.steps):
            row_w = QWidget()
            row_w.setProperty("alt_row", str(i % 2 == 1).lower())
            row_layout = QHBoxLayout(row_w)
            row_layout.setContentsMargins(6, 2, 6, 2)

            name_lbl = QLabel(step.name)
            name_lbl.setObjectName("compact_step_name")
            val_lbl = QLabel(str(step.value))
            val_lbl.setObjectName("compact_step_val")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(name_lbl)
            row_layout.addWidget(val_lbl)
            self._compact_rows_layout.addWidget(row_w)

    # ── Compact view ──────────────────────────────────────────────────────

    def _build_compact_widget(self) -> None:
        w = QWidget()
        h_layout = QHBoxLayout(w)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Scrollable step list — hidden until bar is clicked
        rows_inner = QWidget()
        rows_layout = QVBoxLayout(rows_inner)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(rows_inner)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(300)
        scroll.setVisible(False)

        h_layout.addWidget(scroll)

        # Vertical bar — always visible while compact mode is active
        bar = _VerticalBar()
        bar.clicked.connect(self._on_bar_clicked)
        h_layout.addWidget(bar)

        self._compact_rows_inner = rows_inner
        self._compact_rows_layout = rows_layout
        self._compact_rows_widget = scroll
        self._compact_bar = bar

        w.setVisible(False)  # must be hidden before adding; shown by _enter_compact_view
        self.layout().addWidget(w)
        self._compact_widget = w

        self._rebuild_compact_rows(self._result)

    def _on_bar_clicked(self) -> None:
        """Toggle the step list open/closed and notify PanelContainer."""
        if self._compact_rows_widget.isVisible():
            self._compact_rows_widget.setVisible(False)
            self._compact_bar.set_expanded(False)
            self.collapse_requested.emit()
        else:
            self._compact_rows_widget.setVisible(True)
            self._compact_bar.set_expanded(True)
            self.expand_requested.emit()

    def _enter_compact_view(self) -> None:
        if self._compact_widget is None:
            self._build_compact_widget()
        self._pre_compact_collapsed = self._is_collapsed
        self._is_collapsed = True
        self._content_frame.setVisible(False)
        self._arrow.setText("▶")
        self._compact_widget.setVisible(True)

    def _exit_compact_view(self) -> None:
        if self._compact_widget is not None:
            # Collapse bar to its default state before hiding
            if self._compact_rows_widget is not None:
                self._compact_rows_widget.setVisible(False)
            if self._compact_bar is not None:
                self._compact_bar.set_expanded(False)
            self._compact_widget.setVisible(False)
        if self._pre_compact_collapsed is not None:
            self._is_collapsed = self._pre_compact_collapsed
            self._pre_compact_collapsed = None
            self._content_frame.setVisible(not self._is_collapsed)
            self._arrow.setText("▶" if self._is_collapsed else "▼")

    # ── Public API ────────────────────────────────────────────────────────

    def refresh(self, result: Optional[BattleResult]) -> None:
        self._result = result
        if result is None:
            self._set_placeholder()
        else:
            self._populate_table(result)
        if self._compact_widget is not None:
            self._rebuild_compact_rows(result)
