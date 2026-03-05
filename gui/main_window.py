from __future__ import annotations

import json
import os

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

from core.build_manager import BuildManager
from core.calculators.status_calculator import StatusCalculator
from core.config import BattleConfig
from core.models.build import PlayerBuild
from gui import app_config
from gui.panel_container import PanelContainer
from gui.sections.build_header import BuildHeaderSection
from gui.sections.derived_section import DerivedSection
from gui.sections.equipment_section import EquipmentSection
from gui.sections.passive_section import PassiveSection
from gui.sections.stats_section import StatsSection


class MainWindow(QMainWindow):
    """
    Top-level window. Owns the top bar and PanelContainer.
    No business logic here — widgets emit signals; core handles calculation.
    """

    server_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS Calc — Pre-Renewal Damage Calculator")
        self.resize(1400, 900)
        self.setMinimumSize(1280, 720)

        self._current_build: PlayerBuild | None = None
        self._current_build_name: str = ""
        self._config = BattleConfig()

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

        # ── Typed section references ──────────────────────────────────────
        self._build_header:    BuildHeaderSection = self._panel_container.get_section("build_header")      # type: ignore[assignment]
        self._stats_section:   StatsSection       = self._panel_container.get_section("stats_section")    # type: ignore[assignment]
        self._derived_section: DerivedSection     = self._panel_container.get_section("derived_section")  # type: ignore[assignment]
        self._equip_section:   EquipmentSection   = self._panel_container.get_section("equipment_section")# type: ignore[assignment]
        self._passive_section: PassiveSection     = self._panel_container.get_section("passive_section")  # type: ignore[assignment]

        self._connect_builder_signals()
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
        self._build_combo = QComboBox()
        self._build_combo.setMinimumWidth(200)
        self._build_combo.currentTextChanged.connect(self._on_build_selected)
        layout.addWidget(self._build_combo)

        new_btn = QPushButton("New")
        new_btn.setEnabled(False)  # enabled in Phase 4
        layout.addWidget(new_btn)

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
        self._build_header.level_changed.connect(self._on_build_changed)
        self._stats_section.stats_changed.connect(self._on_build_changed)
        self._equip_section.equipment_changed.connect(self._on_build_changed)
        self._passive_section.passives_changed.connect(self._on_build_changed)

    # ── Build list helpers ─────────────────────────────────────────────────

    def _refresh_builds(self) -> None:
        names = sorted(BuildManager.list_builds(app_config.SAVES_DIR))
        current = self._build_combo.currentText()
        self._build_combo.blockSignals(True)
        self._build_combo.clear()
        self._build_combo.addItems(names)
        if current in names:
            self._build_combo.setCurrentText(current)
        elif names:
            self._build_combo.setCurrentIndex(0)
        self._build_combo.blockSignals(False)
        # Load the currently visible build
        name = self._build_combo.currentText()
        if name:
            self._on_build_selected(name)

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

        self._current_build = build
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

    def _load_build_into_sections(self, build: PlayerBuild) -> None:
        """Push build data to all builder sections (no change signals fired)."""
        self._build_header.load_build(build)
        self._stats_section.load_build(build)
        self._equip_section.load_build(build)
        self._passive_section.load_build(build)

    # ── Build-change pipeline ─────────────────────────────────────────────

    def _on_build_changed(self, *_args) -> None:
        """Called when any builder section changes. Collects build and recalculates."""
        if self._current_build is None:
            return
        self._collect_build()
        self._run_status_calc()

    def _collect_build(self) -> None:
        """Update self._current_build from all builder sections in-place."""
        build = self._current_build
        if build is None:
            return
        self._build_header.collect_into(build)
        self._stats_section.collect_into(build)
        self._equip_section.collect_into(build)
        self._passive_section.collect_into(build)

    def _run_status_calc(self) -> None:
        """Run StatusCalculator and push results to DerivedSection."""
        build = self._current_build
        if build is None:
            return
        weapon = BuildManager.resolve_weapon(
            build.equipped.get("right_hand"),
            build.refine_levels.get("right_hand", 0),
            build.weapon_element,
        )
        status = StatusCalculator(self._config).calculate(build, weapon)
        self._derived_section.refresh(status)

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
