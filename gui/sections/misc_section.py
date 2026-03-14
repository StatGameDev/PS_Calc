from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.models.build import PlayerBuild
from gui.section import Section


class MiscSection(Section):
    """
    Active Effects — auto-computed conditional item bonuses.

    Framework stub. Auto-compute logic deferred to a future session.

    Design intent (from docs/consumables_design.md):
    - At pipeline run time, evaluate stat-threshold conditions on equipped weapon
      scripts against current StatusData / PlayerBuild stats.
    - Apply matching bonus effects (BATK, MATK%, ASPD%, etc.) to the pipeline.
    - Show which conditional bonus fired and why (tooltip).

    Confirmed candidates (docs/consumables_design.md):
      Doom Slayer (1370): STR ≥ 95 → BATK+340
      Krasnaya (1189):    STR ≥ 95 → BATK+20
      Vecer Axe (1311):   LUK ≥ 90 → BATK+20, DEX ≥ 90 → CRI+5
      Giant Axe (1387):   STR ≥ 95 → HIT+10, ASPD+5%
      Sage's Diary (1560): STR ≥ 50 → ASPD+5%, INT ≥ 70 → MATK+15%
      Veteran Sword (1188): SM_BASH lv10 → Bash ATK+50%
      Veteran Axe (1384): BS_DAGGER/SWORD/etc lv3 → BATK+10 each
    """

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)

        note = QLabel("Auto-computed conditional item bonuses — not yet implemented.")
        note.setObjectName("combat_field_label")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.add_content_widget(container)

    def load_build(self, build: PlayerBuild) -> None:
        pass

    def collect_into(self, build: PlayerBuild) -> None:
        pass
