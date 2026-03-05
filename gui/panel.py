from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models.damage import BattleResult
from gui.section import Section


class _VerticalBarLabel(QWidget):
    """Narrow 22px strip that draws rotated 'Steps ▶/◀' text via QPainter."""

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


class StepsBar(QWidget):
    """
    Vertical sidebar attached to the right edge of the combat panel.
    Hidden when combat is focused; shown (narrow) when builder is focused.
    Clicking the bar expands the step list horizontally.
    """

    _NARROW = 22
    _WIDE = 220

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = False
        self.setFixedWidth(self._NARROW)
        self.setVisible(False)

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Step list (hidden until bar is clicked)
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
        h.addWidget(self._scroll)

        # Vertical bar (always visible while StepsBar is shown)
        self._bar = _VerticalBarLabel()
        self._bar.clicked.connect(self._on_bar_clicked)
        h.addWidget(self._bar)

    # ── Toggle ─────────────────────────────────────────────────────────────

    def _on_bar_clicked(self) -> None:
        if self._expanded:
            self._scroll.setVisible(False)
            self._bar.set_expanded(False)
            self.setFixedWidth(self._NARROW)
            self._expanded = False
        else:
            self._scroll.setVisible(True)
            self._bar.set_expanded(True)
            self.setFixedWidth(self._WIDE)
            self._expanded = True

    # ── Public API ─────────────────────────────────────────────────────────

    def set_visible_bar(self, visible: bool) -> None:
        """Called by PanelContainer on focus state changes."""
        if not visible and self._expanded:
            self._scroll.setVisible(False)
            self._bar.set_expanded(False)
            self.setFixedWidth(self._NARROW)
            self._expanded = False
        self.setVisible(visible)

    def refresh(self, result: Optional[BattleResult]) -> None:
        """Rebuild step rows from BattleResult (connected to result_updated)."""
        # Clear rows, keep trailing stretch
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
    The combat panel adds a StepsBar on its right edge (hidden when
    combat is focused, shown when builder is focused).
    """

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = name
        self.setObjectName(f"panel_{name}")

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Scrollable sections area
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
        h.addWidget(self._scroll, stretch=1)

        # Steps bar — combat panel only
        self._steps_bar: Optional[StepsBar] = None
        if name == "combat":
            self._steps_bar = StepsBar()
            h.addWidget(self._steps_bar)

    @property
    def steps_bar(self) -> Optional[StepsBar]:
        return self._steps_bar

    def add_section(self, section: Section) -> None:
        """Insert section before the trailing QSpacerItem."""
        idx = self._layout.count() - 1
        self._layout.insertWidget(idx, section)
