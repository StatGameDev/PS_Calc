from __future__ import annotations

import json
import os
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import dataclasses

from core import build_applicator
from core.build_manager import BuildManager
from core.calculators.battle_pipeline import BattlePipeline
from core.calculators.incoming_magic_pipeline import IncomingMagicPipeline
from core.calculators.incoming_physical_pipeline import IncomingPhysicalPipeline
from core.calculators.status_calculator import StatusCalculator
from core.calculators import target_utils
from core.config import BattleConfig
from core.data_loader import loader
from core.gear_bonus_aggregator import GearBonusAggregator
from core.models.build import PlayerBuild
from core.models.damage import BattleResult
from core.models.skill import SkillInstance
from core.models.target import Target
from gui import app_config
from gui.panel_container import PanelContainer
from gui.sections.build_header import BuildHeaderSection
from gui.sections.combat_controls import CombatControlsSection
from gui.sections.derived_section import DerivedSection
from gui.sections.equipment_section import EquipmentSection
from gui.sections.active_items_section import ActiveItemsSection
from gui.sections.buffs_section import BuffsSection
from gui.sections.consumables_section import ConsumablesSection
from gui.sections.misc_section import MiscSection
from gui.sections.player_debuffs_section import PlayerDebuffsSection
from gui.sections.passive_section import PassiveSection
from gui.sections.stats_section import StatsSection
from gui.sections.incoming_damage import IncomingDamageSection
from gui.sections.step_breakdown import StepBreakdownSection
from gui.sections.summary_section import SummarySection
from gui.sections.target_section import TargetSection
from gui.sections.target_state_section import TargetStateSection
from gui.widgets import NoWheelCombo


class MainWindow(QMainWindow):
    """
    Top-level window. Owns the top bar and PanelContainer.
    No business logic here — widgets emit signals; core handles calculation.
    """

    server_changed = Signal(str)
    result_updated = Signal(object)  # Optional[BattleResult]; object allows None

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS Calc — Pre-Renewal Damage Calculator")
        self.resize(1400, 900)
        self.setMinimumSize(1280, 720)

        self._current_build: PlayerBuild | None = None
        self._current_build_name: str = ""
        self._config = BattleConfig()
        self._pipeline = BattlePipeline(self._config)
        self._incoming_phys_pipeline = IncomingPhysicalPipeline(self._config)
        self._incoming_magic_pipeline = IncomingMagicPipeline(self._config)

        # Load layout config (file I/O outside widget constructors)
        with open("gui/layout_config.json", "r", encoding="utf-8") as f:
            layout_config = json.load(f)

        # ── Central widget ────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._panel_container = PanelContainer(layout_config=layout_config)

        root.addWidget(self._build_top_bar())
        root.addWidget(self._panel_container, stretch=1)

        # ── Typed section references — builder ────────────────────────────
        self._build_header:    BuildHeaderSection = self._panel_container.get_section("build_header")       # type: ignore[assignment]
        self._stats_section:   StatsSection       = self._panel_container.get_section("stats_section")     # type: ignore[assignment]
        self._derived_section: DerivedSection     = self._panel_container.get_section("derived_section")   # type: ignore[assignment]
        self._equip_section:   EquipmentSection   = self._panel_container.get_section("equipment_section") # type: ignore[assignment]
        self._passive_section:   PassiveSection       = self._panel_container.get_section("passive_section")        # type: ignore[assignment]
        self._buffs_section:     BuffsSection         = self._panel_container.get_section("buffs_section")          # type: ignore[assignment]
        self._player_debuffs:    PlayerDebuffsSection = self._panel_container.get_section("player_debuffs_section") # type: ignore[assignment]
        self._consumables:       ConsumablesSection   = self._panel_container.get_section("consumables_section")    # type: ignore[assignment]
        self._misc_section:      MiscSection          = self._panel_container.get_section("misc_section")           # type: ignore[assignment]
        self._active_items:      ActiveItemsSection   = self._panel_container.get_section("active_items_section")   # type: ignore[assignment]

        # ── Typed section references — combat ─────────────────────────────
        self._combat_controls:  CombatControlsSection  = self._panel_container.get_section("combat_controls")   # type: ignore[assignment]
        self._summary_section:  SummarySection         = self._panel_container.get_section("summary_section")   # type: ignore[assignment]
        self._step_breakdown:   StepBreakdownSection   = self._panel_container.get_section("step_breakdown")    # type: ignore[assignment]
        self._target_section:   TargetSection          = self._panel_container.get_section("target_section")    # type: ignore[assignment]
        self._incoming_damage:  IncomingDamageSection  = self._panel_container.get_section("incoming_damage")   # type: ignore[assignment]
        self._target_state:     TargetStateSection     = self._panel_container.get_section("target_state_section") # type: ignore[assignment]

        self._connect_builder_signals()
        self._connect_combat_signals()

        # Wire result_updated to combat sections
        self.result_updated.connect(self._summary_section.refresh)
        self.result_updated.connect(self._step_breakdown.refresh)
        self.result_updated.connect(self._panel_container.steps_bar.refresh)

        self._refresh_builds()

    # ── Top bar construction ───────────────────────────────────────────────

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("top_bar")
        bar.setFixedHeight(44)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        title = QLabel("PS Calc")
        title.setObjectName("app_title")
        layout.addWidget(title)
        layout.addSpacing(8)

        layout.addWidget(QLabel("Build:"))
        self._build_combo = NoWheelCombo()
        self._build_combo.setMinimumWidth(200)
        self._build_combo.currentIndexChanged.connect(self._on_build_index_changed)
        layout.addWidget(self._build_combo)

        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._on_new_build)
        layout.addWidget(new_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.clicked.connect(self._on_save_build)
        self._save_btn.setEnabled(False)
        layout.addWidget(self._save_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_builds)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        # Server toggle — exclusive button group
        self._server_group = QButtonGroup(self)
        self._server_group.setExclusive(True)

        std_btn = QPushButton("Standard")
        std_btn.setCheckable(True)
        std_btn.setChecked(True)
        std_btn.setObjectName("server_btn")

        ps_btn = QPushButton("Payon Stories")
        ps_btn.setCheckable(True)
        ps_btn.setObjectName("server_btn")

        self._server_group.addButton(std_btn, 0)
        self._server_group.addButton(ps_btn, 1)
        self._server_group.idToggled.connect(self._on_server_toggled)

        layout.addWidget(std_btn)
        layout.addWidget(ps_btn)

        layout.addStretch()

        builder_btn = QPushButton("◧ Builder")
        builder_btn.setObjectName("focus_btn")
        builder_btn.clicked.connect(self._focus_builder)
        layout.addWidget(builder_btn)

        combat_btn = QPushButton("◨ Combat")
        combat_btn.setObjectName("focus_btn")
        combat_btn.clicked.connect(self._focus_combat)
        layout.addWidget(combat_btn)

        return bar

    # ── Signal wiring ──────────────────────────────────────────────────────

    def _connect_builder_signals(self) -> None:
        """Wire all builder section change signals to _on_build_changed."""
        self._build_header.build_name_changed.connect(self._on_build_changed)
        self._build_header.job_changed.connect(self._on_build_changed)
        self._build_header.job_changed.connect(self._equip_section.update_for_job)
        self._build_header.job_changed.connect(self._passive_section.update_job)
        self._build_header.job_changed.connect(self._buffs_section.update_job)
        self._build_header.job_changed.connect(self._combat_controls.update_job)
        self._build_header.level_changed.connect(self._on_build_changed)
        self._build_header.bonuses_changed.connect(self._on_build_changed)
        self._stats_section.stats_changed.connect(self._on_build_changed)
        self._equip_section.equipment_changed.connect(self._on_build_changed)
        self._passive_section.passives_changed.connect(self._on_build_changed)
        self._buffs_section.changed.connect(self._on_build_changed)
        self._buffs_section.spirit_spheres_changed.connect(self._combat_controls.set_spirit_spheres)
        self._player_debuffs.changed.connect(self._on_build_changed)
        self._consumables.changed.connect(self._on_build_changed)
        self._active_items.bonuses_changed.connect(self._on_build_changed)
        self._target_state.state_changed.connect(self._on_build_changed)
        self._incoming_damage.config_changed.connect(self._run_battle_pipeline)

    def _connect_combat_signals(self) -> None:
        """Wire combat section change signals to _on_build_changed."""
        self._combat_controls.combat_settings_changed.connect(self._on_build_changed)
        self._combat_controls.spirit_spheres_changed.connect(self._buffs_section.set_spirit_spheres)

    # ── Build list helpers ─────────────────────────────────────────────────

    @staticmethod
    def _read_build_display_name(path: str) -> str:
        """Fast read of just the 'name' field from a build JSON. Returns stem on failure."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("name") or ""
        except Exception:
            return ""

    def _refresh_builds(self, select_name: str | None = None) -> None:
        """Populate combo with display names (item data = file stem).
        select_name can be a display name or a file stem — both are searched.
        """
        stems = sorted(BuildManager.list_builds(app_config.SAVES_DIR))
        # Prefer the display name of the currently selected build when no hint given
        want = select_name or self._build_combo.currentText()
        self._build_combo.blockSignals(True)
        self._build_combo.clear()
        for stem in stems:
            path = os.path.join(app_config.SAVES_DIR, f"{stem}.json")
            display = self._read_build_display_name(path) or stem
            self._build_combo.addItem(display, userData=stem)
        # Select by display name first, then by stem (item data)
        idx = self._build_combo.findText(want)
        if idx < 0:
            idx = self._build_combo.findData(want)
        if idx >= 0:
            self._build_combo.setCurrentIndex(idx)
        elif self._build_combo.count() > 0:
            self._build_combo.setCurrentIndex(0)
        self._build_combo.blockSignals(False)
        pairs = [(stem, self._read_build_display_name(os.path.join(app_config.SAVES_DIR, f"{stem}.json")) or stem)
                 for stem in stems]
        self._combat_controls.refresh_target_builds(pairs)
        # Load whichever build is now selected
        stem = self._build_combo.currentData()
        if stem:
            self._on_build_selected(stem)

    def _on_build_index_changed(self, index: int) -> None:
        stem = self._build_combo.itemData(index)
        if stem:
            self._on_build_selected(stem)

    def _on_new_build(self) -> None:
        from gui.dialogs.new_build_dialog import NewBuildDialog
        dlg = NewBuildDialog(app_config.SAVES_DIR, parent=self)
        if dlg.exec() == NewBuildDialog.DialogCode.Accepted:
            name = dlg.created_build_name()
            if name:
                self._refresh_builds(select_name=name)

    def _on_save_build(self) -> None:
        """Save using the current Name field value as the filename.
        _collect_build() is called first so build.name reflects what the user typed.
        If the name changed, refreshes the build combo and updates _current_build_name."""
        if self._current_build is None:
            return
        self._collect_build()
        build = self._current_build
        if not build.name:
            return
        path = os.path.join(app_config.SAVES_DIR, f"{build.name}.json")
        try:
            BuildManager.save_build(build, path)
        except Exception as exc:
            print(f"WARNING: Failed to save build '{build.name}': {exc}")
            return
        if self._current_build_name != build.name:
            self._current_build_name = build.name
            self._refresh_builds(select_name=build.name)

    def _on_build_selected(self, name: str) -> None:
        if not name:
            return
        self._current_build_name = name
        path = os.path.join(app_config.SAVES_DIR, f"{name}.json")
        try:
            build = BuildManager.load_build(path)
        except Exception as exc:
            print(f"WARNING: Failed to load build '{name}': {exc}")
            return

        # G15: legacy bonus_* fields from old saves are no longer user-editable.
        # Zero them on load so they don't stack on top of auto-computed gear bonuses.
        build.bonus_str = build.bonus_agi = build.bonus_vit = 0
        build.bonus_int = build.bonus_dex = build.bonus_luk = 0
        build.bonus_batk = build.bonus_hit = build.bonus_flee = build.bonus_cri = 0
        build.equip_def = build.equip_mdef = build.bonus_aspd_percent = 0
        self._current_build = build
        self._save_btn.setEnabled(True)
        self._load_build_into_sections(build)

        # Sync server toggle to the loaded build's server field
        self._server_group.blockSignals(True)
        is_payon = (build.server == "payon_stories")
        btn = self._server_group.button(1 if is_payon else 0)
        if btn:
            btn.setChecked(True)
        self._server_group.blockSignals(False)

        base_title = "PS Calc — Pre-Renewal Damage Calculator"
        self.setWindowTitle(base_title + (" — Payon Stories" if is_payon else ""))

        self._run_status_calc()
        self._run_battle_pipeline()

    def _load_build_into_sections(self, build: PlayerBuild) -> None:
        """Push build data to all sections (no change signals fired)."""
        self._build_header.load_build(build)
        self._stats_section.load_build(build)
        self._equip_section.load_build(build)
        self._passive_section.load_build(build)
        self._buffs_section.load_build(build)
        self._player_debuffs.load_build(build)
        self._consumables.load_build(build)
        self._misc_section.load_build(build)
        self._active_items.load_build(build)
        self._combat_controls.load_build(build)
        self._target_state.load_build(build)

    # ── Build-change pipeline ─────────────────────────────────────────────

    def _on_build_changed(self, *_args) -> None:
        """Called when any section changes. Collects build and recalculates."""
        if self._current_build is None:
            return
        self._collect_build()
        self._run_status_calc()
        self._run_battle_pipeline()

    def _collect_build(self) -> None:
        """Update self._current_build from all sections in-place."""
        build = self._current_build
        if build is None:
            return
        self._build_header.collect_into(build)
        self._stats_section.collect_into(build)
        self._equip_section.collect_into(build)
        self._passive_section.collect_into(build)
        self._buffs_section.collect_into(build)
        self._player_debuffs.collect_into(build)
        self._consumables.collect_into(build)
        self._misc_section.collect_into(build)
        self._active_items.collect_into(build)
        self._combat_controls.collect_into(build)
        self._target_state.collect_into(build)
        # G15: bonus_str–luk and flat bonus fields are now auto-computed from gear/AI/MA;
        # zero them so old loaded values don't double-stack on top of gear bonuses.
        build.bonus_str = 0
        build.bonus_agi = 0
        build.bonus_vit = 0
        build.bonus_int = 0
        build.bonus_dex = 0
        build.bonus_luk = 0
        build.bonus_batk = 0
        build.bonus_hit = 0
        build.bonus_flee = 0
        build.bonus_cri = 0
        build.equip_def = 0
        build.equip_mdef = 0
        build.bonus_aspd_percent = 0
        build.bonus_matk_flat = 0

    def _run_status_calc(self) -> None:
        """Run StatusCalculator and push results to DerivedSection."""
        build = self._current_build
        if build is None:
            return
        # Compute gear bonuses once — used for stats display and effective build.
        gb = GearBonusAggregator.compute(build.equipped, build.refine_levels)
        sc_bonuses = build_applicator.compute_sc_stat_bonuses(build.support_buffs)
        self._stats_section.update_from_bonuses(
            gb, build.active_items_bonuses, build.manual_adj_bonuses, sc_bonuses
        )
        eff_build = build_applicator.apply_gear_bonuses(build, gb)
        weapon = BuildManager.resolve_weapon(
            eff_build.equipped.get("right_hand"),
            eff_build.refine_levels.get("right_hand", 0),
            eff_build.weapon_element,
            is_forged=eff_build.is_forged,
            forge_sc_count=eff_build.forge_sc_count,
            forge_ranked=eff_build.forge_ranked,
            forge_element=eff_build.forge_element,
            script_atk_ele=gb.script_atk_ele,
        )
        resolved_armor_ele = build_applicator.resolve_armor_element(eff_build.armor_element, gb)
        status = StatusCalculator(self._config).calculate(eff_build, weapon)
        self._derived_section.refresh(status, atk_ele=weapon.element, def_ele=resolved_armor_ele)

    def _run_battle_pipeline(self) -> None:
        """Run BattlePipeline and push BattleResult to combat sections."""
        build = self._current_build
        if build is None:
            return
        gb = GearBonusAggregator.compute(build.equipped, build.refine_levels)
        GearBonusAggregator.apply_passive_bonuses(gb, build.mastery_levels)
        eff_build = build_applicator.apply_gear_bonuses(build, gb)
        weapon = BuildManager.resolve_weapon(
            eff_build.equipped.get("right_hand"),
            eff_build.refine_levels.get("right_hand", 0),
            eff_build.weapon_element,
            is_forged=eff_build.is_forged,
            forge_sc_count=eff_build.forge_sc_count,
            forge_ranked=eff_build.forge_ranked,
            forge_element=eff_build.forge_element,
            script_atk_ele=gb.script_atk_ele,
        )
        status = StatusCalculator(self._config).calculate(eff_build, weapon)
        skill = self._combat_controls.get_skill_instance()
        pvp_stem = self._combat_controls.get_target_pvp_stem()
        mob_id = None if pvp_stem else (
            self._combat_controls.get_target_mob_id() or eff_build.target_mob_id
        )

        # Resolve outgoing target
        if pvp_stem:
            pvp_path = os.path.join(app_config.SAVES_DIR, f"{pvp_stem}.json")
            try:
                pvp_build = BuildManager.load_build(pvp_path)
            except Exception as exc:
                print(f"WARNING: Failed to load PvP target build '{pvp_stem}': {exc}")
                pvp_build = None
            if pvp_build is not None:
                pvp_gb = GearBonusAggregator.compute(pvp_build.equipped, pvp_build.refine_levels)
                GearBonusAggregator.apply_passive_bonuses(pvp_gb, pvp_build.mastery_levels)
                pvp_eff = build_applicator.apply_gear_bonuses(pvp_build, pvp_gb)
                pvp_weapon = BuildManager.resolve_weapon(
                    pvp_eff.equipped.get("right_hand"),
                    pvp_eff.refine_levels.get("right_hand", 0),
                    pvp_eff.weapon_element,
                    is_forged=pvp_eff.is_forged,
                    forge_sc_count=pvp_eff.forge_sc_count,
                    forge_ranked=pvp_eff.forge_ranked,
                    forge_element=pvp_eff.forge_element,
                    script_atk_ele=pvp_gb.script_atk_ele,
                )
                # Merge stat-cascade debuffs into pvp_eff before StatusCalculator runs,
                # so effects like DECREASEAGI → AGI → FLEE/ASPD cascade correctly.
                target_scs = self._target_state.collect_target_player_scs()
                if target_scs:
                    pvp_eff = dataclasses.replace(
                        pvp_eff,
                        player_active_scs={**pvp_eff.player_active_scs, **target_scs},
                    )
                pvp_status = StatusCalculator(self._config).calculate(pvp_eff, pvp_weapon)
                target = BuildManager.player_build_to_target(pvp_eff, pvp_status, pvp_gb)
            else:
                pvp_stem = None
                target = Target()
        else:
            target = loader.get_monster(mob_id) if mob_id is not None else Target()

        # Apply target state debuffs after target is resolved.
        # apply_to_target() sets target_active_scs flags and element/strip overrides.
        # apply_mob_scs() applies stat mutations for mob targets (player targets get
        # these via StatusCalculator, fed from collect_target_player_scs() above).
        self._target_state.set_target_type(target.is_pc)
        self._target_state.set_is_boss(target.is_boss)
        self._target_state.apply_to_target(target)
        if not target.is_pc:
            target_utils.apply_mob_scs(target)

        # Always refresh target section — independent of pipeline success (B5).
        self._target_section.refresh_mob(mob_id)

        # Incoming damage pipelines — player as defender.
        # gb already computed at top of function (with passive bonuses applied).
        player_target = BuildManager.player_build_to_target(eff_build, status, gb)
        siegfried_lv = int(eff_build.support_buffs.get("SC_SIEGFRIED", 0))
        if siegfried_lv:
            resist = 55 + 5 * siegfried_lv
            for ele_key in ("Ele_Water", "Ele_Earth", "Ele_Fire", "Ele_Wind",
                            "Ele_Poison", "Ele_Holy", "Ele_Dark", "Ele_Ghost"):
                player_target.sub_ele[ele_key] = player_target.sub_ele.get(ele_key, 0) + resist
        phys_result = None
        magic_result = None
        is_ranged, ele_override, ratio_override = (
            self._incoming_damage.get_incoming_config()
        )
        if pvp_stem and pvp_build is not None:
            # PvP incoming: run the attacker's (pvp) pipeline against the current player as target
            try:
                pvp_battle = self._pipeline.calculate(pvp_status, pvp_weapon, SkillInstance(), player_target, pvp_eff)
                phys_result = pvp_battle.normal
            except Exception as exc:
                print(f"WARNING: PvP incoming pipeline error: {exc}")
        elif mob_id is not None:
            try:
                phys_result = self._incoming_phys_pipeline.calculate(
                    mob_id=mob_id,
                    player_target=player_target,
                    gear_bonuses=gb,
                    build=eff_build,
                    is_ranged=is_ranged,
                )
            except Exception as exc:
                print(f"WARNING: IncomingPhysicalPipeline error: {exc}")
            try:
                magic_result = self._incoming_magic_pipeline.calculate(
                    mob_id=mob_id,
                    player_target=player_target,
                    gear_bonuses=gb,
                    build=eff_build,
                    ele_override=ele_override,
                    ratio_override=ratio_override,
                    mob_matk_bonus_rate=target.matk_percent - 100,
                )
            except Exception as exc:
                print(f"WARNING: IncomingMagicPipeline error: {exc}")
        self._incoming_damage.refresh(phys_result, magic_result)

        try:
            result = self._pipeline.calculate(status, weapon, skill, target, eff_build)
        except Exception as exc:
            print(f"WARNING: BattlePipeline error: {exc}")
            result = None
        self.result_updated.emit(result)

    # ── Server toggle ──────────────────────────────────────────────────────

    def _on_server_toggled(self, btn_id: int, checked: bool) -> None:
        if not checked:
            return
        is_payon = (btn_id == 1)
        server_str = "payon_stories" if is_payon else "standard"

        if self._current_build is not None:
            self._current_build.server = server_str

        base_title = self.windowTitle().replace(" — Payon Stories", "")
        self.setWindowTitle(base_title + (" — Payon Stories" if is_payon else ""))

        self.server_changed.emit(server_str)

    # ── Focus buttons ──────────────────────────────────────────────────────

    def _focus_builder(self) -> None:
        self._panel_container.focus_builder()

    def _focus_combat(self) -> None:
        self._panel_container.focus_combat()
