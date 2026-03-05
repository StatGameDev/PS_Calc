from PySide6.QtWidgets import QLabel
from gui.section import Section


class IncomingDamageSection(Section):
    """Phase 3.2 — Incoming damage (player as defender)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 3.2 — Incoming Damage")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
