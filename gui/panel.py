from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from gui.section import Section


class Panel(QScrollArea):
    """
    Scrollable container for an ordered list of Section widgets.
    Maps to one side of the QSplitter (builder or combat).
    """

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = name

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setObjectName(f"panel_{name}")

        self._inner = QWidget()
        self._inner.setObjectName("panel_inner")
        self._inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()  # trailing spacer — sections inserted before it

        self.setWidget(self._inner)

    def add_section(self, section: Section) -> None:
        """Insert section before the trailing QSpacerItem."""
        idx = self._layout.count() - 1
        self._layout.insertWidget(idx, section)
