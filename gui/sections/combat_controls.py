from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from core.models.skill import SkillInstance
from gui.section import Section


class CombatControlsSection(Section):
    """Phase 2.1 — Skill dropdown, unified target selector (mob or player), environment."""

    combat_settings_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        # ── Target state ──────────────────────────────────────────────────
        self._target_type: str = "mob"           # "mob" | "player"
        self._selected_mob_id: Optional[int] = None
        self._target_pvp_stem: Optional[str] = None
        self._player_build_pairs: list[tuple[str, str]] = []  # (stem, display_name)
        self._all_mobs: list = loader.get_all_monsters()

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # ── Row 0: Skill ──────────────────────────────────────────────────
        skill_lbl = QLabel("Skill")
        skill_lbl.setObjectName("combat_field_label")
        grid.addWidget(skill_lbl, 0, 0)

        skill_row = QHBoxLayout()
        skill_row.setSpacing(6)

        self._skill_combo = QComboBox()
        self._skill_combo.setMinimumWidth(160)
        self._skill_combo.addItem("Normal Attack  (id=0)", userData={"id": 0, "name": "Normal Attack"})
        for s in loader.get_all_skills():
            self._skill_combo.addItem(f"{s['name']}  (id={s['id']})", userData=s)
        skill_row.addWidget(self._skill_combo, stretch=1)

        self._level_spin = QSpinBox()
        self._level_spin.setRange(1, 10)
        self._level_spin.setPrefix("Lv ")
        self._level_spin.setFixedWidth(60)
        skill_row.addWidget(self._level_spin)

        skill_browse_btn = QPushButton("…")
        skill_browse_btn.setFixedWidth(28)
        skill_browse_btn.setToolTip("Browse skills")
        skill_browse_btn.clicked.connect(self._open_skill_browser)
        skill_row.addWidget(skill_browse_btn)

        skill_widget = QWidget()
        skill_widget.setLayout(skill_row)
        grid.addWidget(skill_widget, 0, 1)

        # ── Row 1: Target ─────────────────────────────────────────────────
        target_lbl = QLabel("Target")
        target_lbl.setObjectName("combat_field_label")
        grid.addWidget(target_lbl, 1, 0, alignment=Qt.AlignmentFlag.AlignTop)

        target_col = QVBoxLayout()
        target_col.setSpacing(4)

        # Mode toggle + search row
        mode_row = QHBoxLayout()
        mode_row.setSpacing(4)

        self._mode_btn = QPushButton("Mob")
        self._mode_btn.setCheckable(True)
        self._mode_btn.setChecked(False)
        self._mode_btn.setFixedWidth(60)
        self._mode_btn.setObjectName("target_mode_btn")
        mode_row.addWidget(self._mode_btn)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search mob name…")
        mode_row.addWidget(self._search_edit, stretch=1)

        self._browse_btn = QPushButton("Browse…")
        mode_row.addWidget(self._browse_btn)

        target_col.addLayout(mode_row)

        self._target_list = QListWidget()
        self._target_list.setMaximumHeight(140)
        self._target_list.setVisible(False)
        target_col.addWidget(self._target_list)

        self._target_display = QLabel("None selected")
        self._target_display.setObjectName("combat_target_display")
        target_col.addWidget(self._target_display)

        target_widget = QWidget()
        target_widget.setLayout(target_col)
        grid.addWidget(target_widget, 1, 1)

        # ── Row 2: Environment (reserved) ────────────────────────────────
        env_lbl = QLabel("Env")
        env_lbl.setObjectName("combat_field_label")
        grid.addWidget(env_lbl, 2, 0)

        env_placeholder = QLabel("— reserved for future map config —")
        env_placeholder.setObjectName("combat_env_placeholder")
        grid.addWidget(env_placeholder, 2, 1)

        container = QWidget()
        container.setLayout(grid)
        self.add_content_widget(container)

        # ── Connections ───────────────────────────────────────────────────
        self._skill_combo.currentIndexChanged.connect(self._emit_changed)
        self._level_spin.valueChanged.connect(self._emit_changed)
        self._mode_btn.toggled.connect(self._on_mode_toggled)
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._target_list.itemClicked.connect(self._on_target_selected)
        self._browse_btn.clicked.connect(self._open_browse)

    # ── Mode toggle ───────────────────────────────────────────────────────

    def _on_mode_toggled(self, checked: bool) -> None:
        self._target_type = "player" if checked else "mob"
        self._mode_btn.setText("Player" if checked else "Mob")
        self._search_edit.setPlaceholderText(
            "Search build name…" if checked else "Search mob name…"
        )
        # Clear the search list without emitting a change signal
        self._search_edit.blockSignals(True)
        self._search_edit.clear()
        self._search_edit.blockSignals(False)
        self._target_list.clear()
        self._target_list.setVisible(False)
        self._update_target_display()
        self.combat_settings_changed.emit()

    # ── Search ────────────────────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        query = text.strip().lower()
        if len(query) < 2:
            self._target_list.setVisible(False)
            self._target_list.clear()
            return

        self._target_list.clear()
        if self._target_type == "mob":
            matches = [m for m in self._all_mobs
                       if query in m.get("name", "").lower()][:20]
            for m in matches:
                item = QListWidgetItem(f"{m['name']}  [{m['id']}]")
                item.setData(Qt.ItemDataRole.UserRole, m["id"])
                self._target_list.addItem(item)
        else:
            matches_p = [(stem, disp) for stem, disp in self._player_build_pairs
                         if query in disp.lower()][:20]
            for stem, disp in matches_p:
                item = QListWidgetItem(disp)
                item.setData(Qt.ItemDataRole.UserRole, stem)
                self._target_list.addItem(item)

        self._target_list.setVisible(self._target_list.count() > 0)

    def _on_target_selected(self, item: QListWidgetItem) -> None:
        if self._target_type == "mob":
            self._selected_mob_id = item.data(Qt.ItemDataRole.UserRole)
        else:
            self._target_pvp_stem = item.data(Qt.ItemDataRole.UserRole)

        self._search_edit.blockSignals(True)
        self._search_edit.clear()
        self._search_edit.blockSignals(False)
        self._target_list.clear()
        self._target_list.setVisible(False)
        self._update_target_display()
        self.combat_settings_changed.emit()

    # ── Browse ────────────────────────────────────────────────────────────

    def _open_browse(self) -> None:
        if self._target_type == "mob":
            self._open_monster_browser()
        else:
            self._open_player_browser()

    def _open_monster_browser(self) -> None:
        from gui.dialogs.monster_browser import MonsterBrowserDialog
        dlg = MonsterBrowserDialog(self._selected_mob_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            mob_id = dlg.selected_mob_id()
            self._selected_mob_id = mob_id
            self._update_target_display()
            self.combat_settings_changed.emit()

    def _open_player_browser(self) -> None:
        from gui import app_config
        from gui.dialogs.player_target_browser import PlayerTargetBrowserDialog
        dlg = PlayerTargetBrowserDialog(
            app_config.SAVES_DIR, self._target_pvp_stem, parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._target_pvp_stem = dlg.selected_build_stem()
            self._update_target_display()
            self.combat_settings_changed.emit()

    def _open_skill_browser(self) -> None:
        from gui.dialogs.skill_browser import SkillBrowserDialog
        current = None
        idx = self._skill_combo.currentIndex()
        if idx >= 0:
            s = self._skill_combo.itemData(idx)
            current = s["id"] if s else None
        dlg = SkillBrowserDialog(current, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            sid = dlg.selected_skill_id()
            for i in range(self._skill_combo.count()):
                data = self._skill_combo.itemData(i)
                if data and data.get("id") == sid:
                    self._skill_combo.setCurrentIndex(i)
                    break

    # ── Display update ────────────────────────────────────────────────────

    def _update_target_display(self) -> None:
        if self._target_type == "mob":
            if self._selected_mob_id is not None:
                data = loader.get_monster_data(self._selected_mob_id)
                self._target_display.setText(data["name"] if data else f"Mob #{self._selected_mob_id}")
            else:
                self._target_display.setText("None selected")
        else:
            if self._target_pvp_stem is not None:
                # Find display name from pairs
                disp = next(
                    (d for s, d in self._player_build_pairs if s == self._target_pvp_stem),
                    self._target_pvp_stem,
                )
                self._target_display.setText(f"Player: {disp}")
            else:
                self._target_display.setText("None selected")

    # ── Internal ──────────────────────────────────────────────────────────

    def _emit_changed(self) -> None:
        self.combat_settings_changed.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def get_skill_instance(self) -> SkillInstance:
        idx = self._skill_combo.currentIndex()
        if idx < 0:
            return SkillInstance(id=0, level=1)
        s = self._skill_combo.itemData(idx)
        skill_id = s["id"] if s else 0
        return SkillInstance(id=skill_id, level=self._level_spin.value())

    def get_target_mob_id(self) -> Optional[int]:
        """Return selected mob ID in mob mode, or None in player mode."""
        return self._selected_mob_id if self._target_type == "mob" else None

    def get_target_pvp_stem(self) -> Optional[str]:
        """Return selected build stem in player mode, or None in mob mode."""
        return self._target_pvp_stem if self._target_type == "player" else None

    def refresh_target_builds(self, pairs: list[tuple[str, str]]) -> None:
        """Repopulate the player build list. If the current pvp stem is no longer present, clear it."""
        self._player_build_pairs = list(pairs)
        stems = {s for s, _ in pairs}
        if self._target_pvp_stem is not None and self._target_pvp_stem not in stems:
            self._target_pvp_stem = None
            if self._target_type == "player":
                self._update_target_display()

    def load_build(self, build: PlayerBuild) -> None:
        # Always reset to mob mode on build load (pvp target is session-only)
        if self._mode_btn.isChecked():
            self._mode_btn.blockSignals(True)
            self._mode_btn.setChecked(False)
            self._mode_btn.setText("Mob")
            self._mode_btn.blockSignals(False)
            self._target_type = "mob"
            self._search_edit.setPlaceholderText("Search mob name…")

        mob_id = build.target_mob_id
        if mob_id is not None:
            self._selected_mob_id = mob_id
            data = loader.get_monster_data(mob_id)
            self._target_display.setText(data["name"] if data else f"Mob #{mob_id}")
        else:
            self._selected_mob_id = None
            self._target_display.setText("None selected")

    def collect_into(self, build: PlayerBuild) -> None:
        build.target_mob_id = self._selected_mob_id if self._target_type == "mob" else None
