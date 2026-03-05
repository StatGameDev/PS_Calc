from PySide6.QtWidgets import QLabel
from gui.section import Section


class EquipmentSection(Section):
    """Phase 1.4 — Equipment slots with refine spinners and item browser."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 1.4 — Equipment")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
