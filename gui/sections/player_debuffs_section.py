from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)

from core.models.build import PlayerBuild
from gui.section import Section
from gui.widgets.collapsible_sub_group import CollapsibleSubGroup


class PlayerDebuffsSection(Section):
    """
    Session M0 skeleton — debuffs applied to the player by enemies.
    Used for incoming damage calculations.
    Content is stubbed; actual debuff rows added in Session R.
    """

    changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        self._compact_widget: QWidget | None = None
        self._compact_summary_lbl: QLabel | None = None

        # ── Player Debuffs sub-group ──────────────────────────────────────
        self._sub_debuffs = CollapsibleSubGroup("Player Debuffs", default_collapsed=False)
        self._sub_debuffs.add_content_widget(
            _note("Debuffs the enemy has applied to you.\n(SC toggles added in Session R)")
        )
        self.add_content_widget(self._sub_debuffs)

    # ── Compact API ────────────────────────────────────────────────────────

    def _build_compact_widget(self) -> None:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        self._compact_summary_lbl = QLabel("No active debuffs")
        self._compact_summary_lbl.setObjectName("passive_compact_summary")
        self._compact_summary_lbl.setWordWrap(True)
        layout.addWidget(self._compact_summary_lbl)
        w.setVisible(False)
        self._compact_widget = w
        self.layout().addWidget(w)

    def _enter_slim(self) -> None:
        if self._compact_widget is None:
            self._build_compact_widget()
        self._compact_widget.setVisible(True)

    def _exit_slim(self) -> None:
        if self._compact_widget is not None:
            self._compact_widget.setVisible(False)

    # ── Public API ─────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        # No widgets yet — nothing to restore
        pass

    def collect_into(self, build: PlayerBuild) -> None:
        # No widgets yet — nothing to collect
        build.player_active_scs = dict(getattr(build, "player_active_scs", {}))


def _note(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("active_items_note")
    lbl.setWordWrap(True)
    return lbl
