from PySide6.QtWidgets import QLabel
from gui.section import Section


class PassiveSection(Section):
    """Phase 1.5 — Self Buffs, Party Buffs, Masteries, Flags sub-groups."""

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)
        lbl = QLabel("Coming in Phase 1.5 — Passives & Buffs")
        lbl.setObjectName("stub_label")
        self.add_content_widget(lbl)
