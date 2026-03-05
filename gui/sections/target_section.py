from PySide6.QtWidgets import QLabel
from gui.section import Section


class TargetSection(Section):
    """Phase 3.1 — Target mob info (name, DEF, VIT, element, size, race)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 3.1 — Target Info")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
