from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.models.damage import BattleResult
from gui.section import Section

# Width of the narrow collapsed bar (px)
_BAR_W = 22
# Width of the expanded step list including the bar (px)
_EXPANDED_W = 220


class _VerticalBarLabel(QWidget):
    """Narrow 22px strip with rotated 'Steps ▶/◀' label drawn via QPainter."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = False
        self.setFixedWidth(_BAR_W)
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
        p.translate(_BAR_W // 2, self.height() // 2)
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


class StepsBar(QWidget):
    """
    Vertical sidebar for the compact combat panel.
    Layout: [bar (left, always visible)] [step list scroll (right, toggle)].

    The bar acts as a visual divider between the sections QScrollArea and the
    step list. Expanding/collapsing is delegated to Panel via signals so that
    the Panel's inner QSplitter can handle the resize reliably.
    """

    expand_requested = Signal()
    collapse_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = False
        self.setVisible(False)

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Bar on LEFT — acts as divider between sections and step list
        self._bar = _VerticalBarLabel()
        self._bar.clicked.connect(self._on_bar_clicked)
        h.addWidget(self._bar)

        # Step list on RIGHT — hidden until expanded
        self._rows_inner = QWidget()
        self._rows_inner.setObjectName("panel_inner")
        self._rows_layout = QVBoxLayout(self._rows_inner)
        self._rows_layout.setContentsMargins(4, 4, 4, 4)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch()

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._rows_inner)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVisible(False)
        h.addWidget(self._scroll, stretch=1)

    # ── Toggle ─────────────────────────────────────────────────────────────

    def _on_bar_clicked(self) -> None:
        if self._expanded:
            self._expanded = False
            self._scroll.setVisible(False)
            self._bar.set_expanded(False)
            self.collapse_requested.emit()
        else:
            self._expanded = True
            self._scroll.setVisible(True)
            self._bar.set_expanded(True)
            self.expand_requested.emit()

    # ── Public API ─────────────────────────────────────────────────────────

    def set_visible_bar(self, visible: bool) -> None:
        """Called by PanelContainer on focus state changes."""
        if not visible and self._expanded:
            self._expanded = False
            self._scroll.setVisible(False)
            self._bar.set_expanded(False)
        self.setVisible(visible)

    def refresh(self, result: Optional[BattleResult]) -> None:
        """Rebuild step rows from BattleResult (wired to result_updated)."""
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
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
            self._rows_layout.insertWidget(i, row_w)


class Panel(QWidget):
    """
    Container for an ordered list of Section widgets.

    The combat panel adds a StepsBar via an inner QSplitter so that expanding
    the steps list reliably pushes the sections QScrollArea to the left.
    The builder panel uses a plain QScrollArea with no splitter overhead.
    """

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = name
        self.setObjectName(f"panel_{name}")

        self._steps_bar: Optional[StepsBar] = None
        self._inner_splitter: Optional[QSplitter] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scrollable sections area ──────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setObjectName(f"panel_scroll_{name}")

        self._inner = QWidget()
        self._inner.setObjectName("panel_inner")
        self._inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()

        self._scroll.setWidget(self._inner)

        if name == "combat":
            # Inner QSplitter handles sections ↔ steps resize reliably
            self._inner_splitter = QSplitter(Qt.Orientation.Horizontal)
            self._inner_splitter.setHandleWidth(1)
            self._inner_splitter.setChildrenCollapsible(False)
            self._inner_splitter.addWidget(self._scroll)

            self._steps_bar = StepsBar()
            self._steps_bar.expand_requested.connect(self._on_steps_expand)
            self._steps_bar.collapse_requested.connect(self._on_steps_collapse)
            self._inner_splitter.addWidget(self._steps_bar)

            outer.addWidget(self._inner_splitter)
        else:
            outer.addWidget(self._scroll)

    # ── Steps expand/collapse (combat panel only) ─────────────────────────

    def _on_steps_expand(self) -> None:
        if self._inner_splitter is None:
            return
        total = sum(self._inner_splitter.sizes())
        self._inner_splitter.setSizes([max(0, total - _EXPANDED_W), _EXPANDED_W])

    def _on_steps_collapse(self) -> None:
        if self._inner_splitter is None:
            return
        total = sum(self._inner_splitter.sizes())
        self._inner_splitter.setSizes([total - _BAR_W, _BAR_W])

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def steps_bar(self) -> Optional[StepsBar]:
        return self._steps_bar

    # ── Section management ────────────────────────────────────────────────

    def add_section(self, section: Section) -> None:
        """Insert section before the trailing QSpacerItem."""
        idx = self._layout.count() - 1
        self._layout.insertWidget(idx, section)
