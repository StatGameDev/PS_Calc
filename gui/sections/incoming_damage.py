from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from core.data_loader import loader
from core.models.status import StatusData
from gui.section import Section


class IncomingDamageSection(Section):
    """
    Phase 3.2 — Incoming damage display (player as defender).

    Display-only for Phase 3: shows mob ATK range and player DEF.
    compact_mode="hidden" — section is hidden when panel is compact.
    No compact_view override needed.
    """

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(3)

        # Row 0: Mob ATK
        grid.addWidget(QLabel("Mob ATK"), 0, 0)
        self._mob_atk_label = QLabel("—")
        self._mob_atk_label.setObjectName("incoming_value")
        grid.addWidget(self._mob_atk_label, 0, 1)

        # Row 1: Player DEF
        grid.addWidget(QLabel("Player DEF"), 1, 0)
        self._player_def_label = QLabel("—")
        self._player_def_label.setObjectName("incoming_value")
        grid.addWidget(self._player_def_label, 1, 1)

        self.add_content_widget(grid_widget)

    # ── Public API ─────────────────────────────────────────────────────────

    def refresh_mob(self, mob_id: Optional[int]) -> None:
        """Update mob ATK row from mob_db."""
        if mob_id is None:
            self._mob_atk_label.setText("—")
            return
        data = loader.get_monster_data(mob_id)
        if data is None:
            self._mob_atk_label.setText("—")
            return
        atk_min = data.get("atk_min", "?")
        atk_max = data.get("atk_max", "?")
        self._mob_atk_label.setText(f"{atk_min} – {atk_max}")

    def refresh_status(self, status: Optional[StatusData]) -> None:
        """Update player DEF row from StatusData."""
        if status is None:
            self._player_def_label.setText("—")
            return
        self._player_def_label.setText(f"{status.def_} / {status.def2}")
