from PySide6.QtWidgets import QLabel
from gui.section import Section


class SummarySection(Section):
    """Phase 2.2 — Damage summary card (normal range, crit range, hit%)."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 2.2 — Summary")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
