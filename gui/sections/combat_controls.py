from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from core.models.skill import SkillInstance
from gui.section import Section


class CombatControlsSection(Section):
    """Phase 2.1 — Skill dropdown, target search, environment radios."""

    combat_settings_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._selected_mob_id: Optional[int] = None
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
        for s in loader.get_all_skills():
            self._skill_combo.addItem(f"{s['name']}  (id={s['id']})", userData=s)
        skill_row.addWidget(self._skill_combo, stretch=1)

        self._level_spin = QSpinBox()
        self._level_spin.setRange(1, 10)
        self._level_spin.setPrefix("Lv ")
        self._level_spin.setFixedWidth(60)
        skill_row.addWidget(self._level_spin)

        skill_widget = QWidget()
        skill_widget.setLayout(skill_row)
        grid.addWidget(skill_widget, 0, 1)

        # ── Row 1: Target search ──────────────────────────────────────────
        target_lbl = QLabel("Target")
        target_lbl.setObjectName("combat_field_label")
        grid.addWidget(target_lbl, 1, 0, alignment=Qt.AlignmentFlag.AlignTop)

        target_col = QVBoxLayout()
        target_col.setSpacing(4)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search mob name…")
        target_col.addWidget(self._search_edit)

        self._mob_list = QListWidget()
        self._mob_list.setMaximumHeight(140)
        self._mob_list.setVisible(False)
        target_col.addWidget(self._mob_list)

        self._mob_selected_lbl = QLabel("None selected")
        self._mob_selected_lbl.setObjectName("combat_mob_selected")
        target_col.addWidget(self._mob_selected_lbl)

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
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._mob_list.itemClicked.connect(self._on_mob_selected)

    # ── Slots ─────────────────────────────────────────────────────────────

    def _emit_changed(self) -> None:
        self.combat_settings_changed.emit()

    def _on_search_changed(self, text: str) -> None:
        query = text.strip().lower()
        if len(query) < 2:
            self._mob_list.setVisible(False)
            self._mob_list.clear()
            return

        matches = [m for m in self._all_mobs
                   if query in m.get("name", "").lower()][:20]
        self._mob_list.clear()
        for m in matches:
            item = QListWidgetItem(f"{m['name']}  [{m['id']}]")
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            self._mob_list.addItem(item)

        self._mob_list.setVisible(bool(matches))

    def _on_mob_selected(self, item: QListWidgetItem) -> None:
        mob_id = item.data(Qt.ItemDataRole.UserRole)
        self._selected_mob_id = mob_id
        name = item.text().split("  [")[0]
        self._mob_selected_lbl.setText(name)
        self._search_edit.blockSignals(True)
        self._search_edit.clear()
        self._search_edit.blockSignals(False)
        self._mob_list.setVisible(False)
        self._mob_list.clear()
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
        return self._selected_mob_id

    def load_build(self, build: PlayerBuild) -> None:
        mob_id = build.target_mob_id
        if mob_id is not None:
            self._selected_mob_id = mob_id
            data = loader.get_monster_data(mob_id)
            name = data["name"] if data else f"Mob #{mob_id}"
            self._mob_selected_lbl.setText(name)
        else:
            self._selected_mob_id = None
            self._mob_selected_lbl.setText("None selected")

    def collect_into(self, build: PlayerBuild) -> None:
        build.target_mob_id = self._selected_mob_id
