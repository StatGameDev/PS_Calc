from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.calculators.modifiers.skill_ratio import (
    IMPLEMENTED_BF_MAGIC_SKILLS,
    IMPLEMENTED_BF_MISC_SKILLS,
    IMPLEMENTED_BF_WEAPON_SKILLS,
)
from core.data_loader import loader
from core.models.build import PlayerBuild
from core.models.skill import SkillInstance
from gui.section import Section
from gui.skill_param_defs import SKILL_PARAM_REGISTRY, SkillParamSpec
from gui.widgets import LevelWidget, NoWheelCombo, NoWheelSpin

_IMPLEMENTED_SKILLS: frozenset[str] = (
    IMPLEMENTED_BF_WEAPON_SKILLS | IMPLEMENTED_BF_MAGIC_SKILLS | IMPLEMENTED_BF_MISC_SKILLS
)

# Jobs that can use plagiarised skills from other jobs (Rogue=17, Stalker=34)
_PLAGIARISM_JOBS: frozenset[int] = frozenset({17, 34})


class _ParamWidget(QWidget):
    """Single skill-param input: label + input widget with uniform value()/set_value() API.

    Handles the three widget types declared in SkillParamSpec:
      "combo" — NoWheelCombo populated from spec.options [(label, value), ...]
      "spin"  — NoWheelSpin configured from spec.options (min, max, step, suffix)
      "check" — QCheckBox; spec.label becomes the checkbox text (no separate label)
    """

    changed = Signal()

    def __init__(self, spec: SkillParamSpec, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._spec = spec
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        if spec.widget == "combo":
            lbl = QLabel(spec.label)
            lbl.setObjectName("combat_field_label")
            row.addWidget(lbl)
            self._inner = NoWheelCombo()
            for text, val in spec.options:
                self._inner.addItem(text, userData=val)
            self._inner.currentIndexChanged.connect(self.changed)
            row.addWidget(self._inner)

        elif spec.widget == "spin":
            lbl = QLabel(spec.label)
            lbl.setObjectName("combat_field_label")
            row.addWidget(lbl)
            mn, mx, step, suffix = spec.options
            self._inner = NoWheelSpin()
            self._inner.setRange(mn, mx)
            self._inner.setSingleStep(step)
            if suffix:
                self._inner.setSuffix(suffix)
            self._inner.setFixedWidth(72)
            self._inner.valueChanged.connect(self.changed)
            row.addWidget(self._inner)

        elif spec.widget == "check":
            self._inner = QCheckBox(spec.label)
            self._inner.stateChanged.connect(self.changed)
            row.addWidget(self._inner)

        else:
            raise ValueError(f"Unknown SkillParamSpec widget type: {spec.widget!r}")

    def value(self) -> Any:
        if self._spec.widget == "combo":
            return self._inner.currentData()
        if self._spec.widget == "spin":
            return self._inner.value()
        if self._spec.widget == "check":
            return self._inner.isChecked()
        return None  # unreachable

    def set_value(self, v: Any) -> None:
        self._inner.blockSignals(True)
        try:
            if self._spec.widget == "combo":
                for i in range(self._inner.count()):
                    if self._inner.itemData(i) == v:
                        self._inner.setCurrentIndex(i)
                        break
            elif self._spec.widget == "spin":
                self._inner.setValue(int(v))
            elif self._spec.widget == "check":
                self._inner.setChecked(bool(v))
        finally:
            self._inner.blockSignals(False)


class CombatControlsSection(Section):
    """Phase 2.1 — Skill dropdown, unified target selector (mob or player), environment."""

    combat_settings_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_modes, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_modes, parent)

        # ── Target state ──────────────────────────────────────────────────
        self._target_type: str = "mob"           # "mob" | "player"
        self._selected_mob_id: Optional[int] = None
        self._target_pvp_stem: Optional[str] = None
        self._player_build_pairs: list[tuple[str, str]] = []  # (stem, display_name)
        self._all_mobs: list = loader.get_all_monsters()
        # ── Skill filter state ────────────────────────────────────────────
        self._all_skills: list = loader.get_all_skills()
        self._current_job_id: int = 0            # updated via update_job()

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

        self._skill_combo = NoWheelCombo()
        self._skill_combo.setMinimumWidth(160)
        skill_row.addWidget(self._skill_combo, stretch=1)

        self._level_widget = LevelWidget(10, include_off=False, item_prefix="Lv ")
        self._level_widget.setFixedWidth(68)
        skill_row.addWidget(self._level_widget)

        self._skill_show_all = QCheckBox("All")
        self._skill_show_all.setToolTip("Show skills for all jobs")
        skill_row.addWidget(self._skill_show_all)

        skill_browse_btn = QPushButton("List")
        skill_browse_btn.setFixedWidth(52)
        skill_browse_btn.setToolTip("Browse skills")
        skill_browse_btn.clicked.connect(self._open_skill_browser)
        skill_row.addWidget(skill_browse_btn)

        skill_widget = QWidget()
        skill_widget.setLayout(skill_row)
        grid.addWidget(skill_widget, 0, 1)

        # ── Row 1: Skill params (registry-driven, hidden unless needed) ───
        self._params_widget = QWidget()
        params_layout = QVBoxLayout(self._params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(4)

        # One container per skill; each container holds the skill's _ParamWidgets.
        self._skill_param_containers: dict[str, QWidget] = {}
        # Flat map key → _ParamWidget for value access in collect_into / load_build.
        self._param_rows: dict[str, _ParamWidget] = {}

        for skill_name, specs in SKILL_PARAM_REGISTRY.items():
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(12)
            for spec in specs:
                pw = _ParamWidget(spec)
                pw.changed.connect(self._emit_changed)
                self._param_rows[spec.key] = pw
                container_layout.addWidget(pw)
            container_layout.addStretch()
            container.setVisible(False)
            self._skill_param_containers[skill_name] = container
            params_layout.addWidget(container)

        self._params_widget.setVisible(False)
        grid.addWidget(self._params_widget, 1, 1)

        # ── Row 2: Target ─────────────────────────────────────────────────
        target_lbl = QLabel("Target")
        target_lbl.setObjectName("combat_field_label")
        grid.addWidget(target_lbl, 2, 0, alignment=Qt.AlignmentFlag.AlignTop)

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
        grid.addWidget(target_widget, 2, 1)

        # ── Row 3: Environment (reserved) ────────────────────────────────
        env_lbl = QLabel("Env")
        env_lbl.setObjectName("combat_field_label")
        grid.addWidget(env_lbl, 3, 0)

        env_placeholder = QLabel("— reserved for future map config —")
        env_placeholder.setObjectName("combat_env_placeholder")
        grid.addWidget(env_placeholder, 3, 1)

        container = QWidget()
        container.setLayout(grid)
        self.add_content_widget(container)

        # ── Initial skill combo population ────────────────────────────────
        self._repopulate_skill_combo(job_id=0, preserve_selection=False)

        # ── Connections ───────────────────────────────────────────────────
        self._skill_combo.currentIndexChanged.connect(self._on_skill_changed)
        self._level_widget.valueChanged.connect(self._emit_changed)
        self._skill_show_all.stateChanged.connect(self._on_show_all_toggled)
        self._mode_btn.toggled.connect(self._on_mode_toggled)
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._target_list.itemClicked.connect(self._on_target_selected)
        self._browse_btn.clicked.connect(self._open_browse)
        # Param widget connections are wired inside the registry loop above.

    # ── Skill filter ──────────────────────────────────────────────────────

    def _repopulate_skill_combo(self, job_id: int, preserve_selection: bool = True) -> None:
        """Rebuild skill combo filtered to job_id (or all skills if Show All is checked)."""
        # Remember current selection
        current_id = None
        if preserve_selection:
            idx = self._skill_combo.currentIndex()
            if idx >= 0:
                d = self._skill_combo.itemData(idx)
                current_id = d["id"] if d else None

        show_all = self._skill_show_all.isChecked()
        if show_all:
            allowed: frozenset | None = None   # None = no filter
        else:
            allowed = loader.get_skills_for_job(job_id)
            if job_id in _PLAGIARISM_JOBS:
                # Also include any skill with AllowPlagiarism in skill_info
                plagiarisable = frozenset(
                    s["name"] for s in self._all_skills
                    if "AllowPlagiarism" in s.get("skill_info", [])
                )
                allowed = allowed | plagiarisable

        self._skill_combo.blockSignals(True)
        self._skill_combo.clear()
        self._skill_combo.addItem("Normal Attack  (id=0)", userData={"id": 0, "name": "Normal Attack"})
        restore_idx = 0
        for s in self._all_skills:
            if s["name"] not in _IMPLEMENTED_SKILLS:
                continue
            if allowed is None or s["name"] in allowed:
                display = s.get("description") or s["name"]
                self._skill_combo.addItem(display, userData=s)
                if s["id"] == current_id:
                    restore_idx = self._skill_combo.count() - 1
        self._skill_combo.setCurrentIndex(restore_idx)
        self._skill_combo.blockSignals(False)
        self._sync_level_widget()
        # Only emit if the selected skill changed
        if preserve_selection:
            new_idx = self._skill_combo.currentIndex()
            new_d = self._skill_combo.itemData(new_idx)
            new_id = new_d["id"] if new_d else 0
            if new_id != current_id:
                self.combat_settings_changed.emit()

    def _on_show_all_toggled(self) -> None:
        self._repopulate_skill_combo(self._current_job_id)

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

    def _update_skill_params_ui(self) -> None:
        """Show the param container for the current skill; hide all others."""
        idx = self._skill_combo.currentIndex()
        s = self._skill_combo.itemData(idx) if idx >= 0 else None
        skill_name = s.get("name", "") if s else ""
        for name, container in self._skill_param_containers.items():
            container.setVisible(name == skill_name)
        self._params_widget.setVisible(skill_name in self._skill_param_containers)

    def _on_skill_changed(self) -> None:
        self._sync_level_widget()
        self._update_skill_params_ui()
        self._emit_changed()

    def _sync_level_widget(self) -> None:
        """Repopulate _level_widget based on the current skill's max_level."""
        idx = self._skill_combo.currentIndex()
        s = self._skill_combo.itemData(idx) if idx >= 0 else None
        max_lv = s.get("max_level", 1) if s and s.get("id", 0) != 0 else 1
        cur = self._level_widget.value() or 1
        self._level_widget.blockSignals(True)
        self._level_widget.clear()
        for lv in range(1, max_lv + 1):
            self._level_widget.addItem(f"Lv {lv}", lv)
        self._level_widget.blockSignals(False)
        self._level_widget.setValue(min(cur, max_lv))

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
        return SkillInstance(id=skill_id, level=self._level_widget.value() or 1)

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

        # Initialise each param widget from build state.
        # Specs with default_from_build use that callable; others restore from
        # build.skill_params (falling back to spec.default for fresh builds).
        for skill_name, specs in SKILL_PARAM_REGISTRY.items():
            for spec in specs:
                if spec.default_from_build is not None:
                    val = spec.default_from_build(build)
                else:
                    val = build.skill_params.get(spec.key, spec.default)
                self._param_rows[spec.key].set_value(val)

        self._repopulate_skill_combo(build.job_id, preserve_selection=False)

    def set_param_value(self, key: str, value: Any) -> None:
        """Set a param widget by key without triggering a recalc.

        Used by main_window to sync mirrored params (e.g. sphere count from
        Self Buffs) without causing a double-recalc.
        """
        pw = self._param_rows.get(key)
        if pw is not None:
            pw.set_value(value)

    def update_job(self, job_id: int) -> None:
        """Called by main_window when the job changes. Repopulates the skill combo."""
        self._current_job_id = job_id
        self._repopulate_skill_combo(job_id)

    def collect_into(self, build: PlayerBuild) -> None:
        build.target_mob_id = self._selected_mob_id if self._target_type == "mob" else None
        build.skill_params = {
            spec.key: self._param_rows[spec.key].value()
            for specs in SKILL_PARAM_REGISTRY.values()
            for spec in specs
        }
