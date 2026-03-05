from PySide6.QtWidgets import QLabel
from gui.section import Section


class CombatControlsSection(Section):
    """Phase 2.1 — Skill dropdown, target search, environment radios."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 2.1 — Combat Controls")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
