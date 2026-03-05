from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _ClickableFrame(QFrame):
    """QFrame that emits clicked() on left mouse press."""
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class Section(QWidget):
    """
    Collapsible panel unit. All visibility changes go through this class.
    PanelContainer and Panel never call setVisible() directly.

    compact_mode (from layout_config.json):
      "none"         → set_compact_mode is a no-op
      "hidden"       → setVisible(False/True)
      "collapsed"    → collapse to header only; user can re-expand
      "compact_view" → swap content via _enter_compact_view() / _exit_compact_view()
    """

    collapsed_changed = Signal(bool)
    expand_requested = Signal()
    collapse_requested = Signal()

    def __init__(
        self,
        key: str,
        display_name: str,
        default_collapsed: bool,
        compact_mode: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._key = key
        self._display_name = display_name
        self._compact_mode = compact_mode
        self._is_collapsed = default_collapsed
        self._is_compact = False
        self._pre_compact_collapsed: Optional[bool] = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        self._header = _ClickableFrame()
        self._header.setObjectName("section_header")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        h_layout = QHBoxLayout(self._header)
        h_layout.setContentsMargins(8, 5, 8, 5)
        h_layout.setSpacing(6)

        self._arrow = QLabel("▶" if default_collapsed else "▼")
        self._arrow.setObjectName("section_arrow")
        self._arrow.setFixedWidth(12)

        self._title = QLabel(display_name)
        self._title.setObjectName("section_title")

        h_layout.addWidget(self._arrow)
        h_layout.addWidget(self._title)
        h_layout.addStretch()

        self._header.clicked.connect(self.toggle_collapse)

        # ── Content Frame ─────────────────────────────────────────────────
        self._content_frame = QFrame()
        self._content_frame.setObjectName("section_content")
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(10, 6, 10, 10)
        self._content_layout.setSpacing(4)
        self._content_frame.setVisible(not default_collapsed)

        root.addWidget(self._header)
        root.addWidget(self._content_frame)

    # ── Content API ────────────────────────────────────────────────────────

    def add_content_widget(self, widget: QWidget) -> None:
        """Append widget to the full-size content frame's layout."""
        self._content_layout.addWidget(widget)

    # ── Collapse API ───────────────────────────────────────────────────────

    def set_collapsed(self, collapsed: bool) -> None:
        """Show/hide content frame. Updates arrow. Emits collapsed_changed."""
        if self._is_collapsed == collapsed:
            return
        self._is_collapsed = collapsed
        self._content_frame.setVisible(not collapsed)
        self._arrow.setText("▶" if collapsed else "▼")
        self.collapsed_changed.emit(collapsed)

    def toggle_collapse(self) -> None:
        self.set_collapsed(not self._is_collapsed)

    # ── Compact API ────────────────────────────────────────────────────────

    def set_compact_mode(self, compact: bool) -> None:
        """
        Idempotent. Entering compact (compact=True) / exiting (compact=False).
        Behaviour depends on self._compact_mode.
        """
        if self._is_compact == compact:
            return
        self._is_compact = compact

        if compact:
            if self._compact_mode == "none":
                return
            elif self._compact_mode == "hidden":
                self.setVisible(False)
            elif self._compact_mode == "collapsed":
                self._pre_compact_collapsed = self._is_collapsed
                self.set_collapsed(True)
            elif self._compact_mode == "compact_view":
                self._enter_compact_view()
        else:
            if self._compact_mode == "none":
                return
            elif self._compact_mode == "hidden":
                self.setVisible(True)
            elif self._compact_mode == "collapsed":
                if self._pre_compact_collapsed is not None:
                    self.set_collapsed(self._pre_compact_collapsed)
                    self._pre_compact_collapsed = None
            elif self._compact_mode == "compact_view":
                self._exit_compact_view()

    def _enter_compact_view(self) -> None:
        """
        Base fallback: collapse to header only (safe for Phase 0 stubs).
        Subclasses override to show a real compact widget instead.
        """
        self._pre_compact_collapsed = self._is_collapsed
        self._is_collapsed = True
        self._content_frame.setVisible(False)
        self._arrow.setText("▶")

    def _exit_compact_view(self) -> None:
        """Base fallback: restore pre-compact collapse state."""
        if self._pre_compact_collapsed is not None:
            self._is_collapsed = self._pre_compact_collapsed
            self._pre_compact_collapsed = None
            self._content_frame.setVisible(not self._is_collapsed)
            self._arrow.setText("▶" if self._is_collapsed else "▼")

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed

    @property
    def key(self) -> str:
        return self._key
