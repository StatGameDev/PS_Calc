from PySide6.QtWidgets import QLabel
from gui.section import Section


class StepBreakdownSection(Section):
    """Phase 2.3 — Step-by-step pipeline table with formula/source toggles."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 2.3 — Step Breakdown")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
