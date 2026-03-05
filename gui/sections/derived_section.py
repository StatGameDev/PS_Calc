from PySide6.QtWidgets import QLabel
from gui.section import Section


class DerivedSection(Section):
    """Phase 1.3 — Derived stats (BATK, DEF, FLEE, HIT, CRI, ASPD, HP, SP)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 1.3 — Derived Stats")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
