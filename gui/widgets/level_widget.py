from __future__ import annotations

import time

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QSpinBox

_HOVER_DELAY = 0.1  # seconds before scroll wheel is accepted


class NoWheelCombo(QComboBox):
    """QComboBox that requires a brief hover before accepting scroll wheel input."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hover_start: float = 0.0

    def enterEvent(self, event) -> None:
        self._hover_start = time.monotonic()
        super().enterEvent(event)

    def wheelEvent(self, event) -> None:
        if time.monotonic() - self._hover_start >= _HOVER_DELAY:
            super().wheelEvent(event)
        else:
            event.ignore()


class NoWheelSpin(QSpinBox):
    """QSpinBox that requires a brief hover before accepting scroll wheel input."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hover_start: float = 0.0

    def enterEvent(self, event) -> None:
        self._hover_start = time.monotonic()
        super().enterEvent(event)

    def wheelEvent(self, event) -> None:
        if time.monotonic() - self._hover_start >= _HOVER_DELAY:
            super().wheelEvent(event)
        else:
            event.ignore()


class LevelWidget(NoWheelCombo):
    """
    Dropdown level selector with QSpinBox-compatible API (value/setValue/valueChanged).
    Populates Off (optional, data=0) + 1..max_lv items.
    """

    valueChanged = Signal(int)

    def __init__(self, max_lv: int, include_off: bool = True, item_prefix: str = ""):
        super().__init__()
        if include_off:
            self.addItem("Off", 0)
        for lv in range(1, max_lv + 1):
            self.addItem(f"{item_prefix}{lv}", lv)
        self.currentIndexChanged.connect(lambda _: self.valueChanged.emit(self.value()))

    def value(self) -> int:
        return self.currentData() or 0

    def setValue(self, v: int) -> None:
        idx = self.findData(v)
        self.setCurrentIndex(idx if idx >= 0 else 0)
