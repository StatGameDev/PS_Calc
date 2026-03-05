from PySide6.QtWidgets import QLabel
from gui.section import Section


class StatsSection(Section):
    """Phase 1.2 — Base stat spinboxes (STR/AGI/VIT/INT/DEX/LUK)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 1.2 — Base Stats")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
