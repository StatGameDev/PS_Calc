from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from gui.section import Section
from gui.widgets.collapsible_sub_group import CollapsibleSubGroup

# ── Self Buffs ────────────────────────────────────────────────────────────────
# (sc_key, display_name, has_level, min_lv, max_lv, source_skill)
# All are job-filtered via update_job(). Show All overrides filtering.
# SC_ADRENALINE and SC_ASSNCROS are in support_buffs / song_state — not here.
_SELF_BUFFS: list[tuple] = [
    ("SC_AURABLADE",      "Aura Blade",         True,  1,  5,  "LK_AURABLADE"),
    ("SC_MAXIMIZEPOWER",  "Maximize Power",      False, 1,  1,  "BS_MAXIMIZE"),
    ("SC_OVERTHRUST",     "Overthrust",          True,  1,  10, "BS_OVERTHRUST"),
    ("SC_OVERTHRUSTMAX",  "Max. Overthrust",     True,  1,  5,  "WS_OVERTHRUSTMAX"),
    ("SC_TWOHANDQUICKEN", "Two-Hand Quicken",    False, 1,  1,  "KN_TWOHANDQUICKEN"),
    ("SC_SPEARQUICKEN",   "Spear Quicken",       True,  1,  10, "CR_SPEARQUICKEN"),
    ("SC_ONEHANDQUICKEN", "One-Hand Quicken*",   False, 1,  1,  "KN_ONEHAND"),
]


def _stub_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("passive_sub_header")
    return lbl


class BuffsSection(Section):
    """
    Session M0 skeleton — 8 CollapsibleSubGroups for player buffs.
    Self Buffs sub-group is fully wired (migrated from passive_section).
    All other sub-groups are stubbed pending Sessions M, M2, N, O.
    """

    changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_summary_lbl: QLabel | None = None
        self._current_job_id: int = 0

        # Storage for Self Buffs
        self._sc_checks: dict[str, QCheckBox] = {}
        self._sc_spins: dict[str, QSpinBox] = {}
        self._self_buff_widgets: dict[str, list[QWidget]] = {}

        # ── 1. Self Buffs ─────────────────────────────────────────────────
        self._sub_self = CollapsibleSubGroup("Self Buffs", default_collapsed=False)

        # "Show All" checkbox in sub-group header
        self._show_all_chk = QCheckBox("Show All")
        self._show_all_chk.setObjectName("passive_show_all")
        self._show_all_chk.toggled.connect(self._on_show_all_toggled)
        self._sub_self.add_header_widget(self._show_all_chk)

        buffs_widget = QWidget()
        buffs_grid = QGridLayout(buffs_widget)
        buffs_grid.setContentsMargins(0, 0, 0, 0)
        buffs_grid.setHorizontalSpacing(6)
        buffs_grid.setVerticalSpacing(3)

        for row_i, (sc_key, display, has_lv, min_lv, max_lv, source_skill) in enumerate(_SELF_BUFFS):
            chk = QCheckBox(display)
            chk.setObjectName("passive_sc_check")
            self._sc_checks[sc_key] = chk
            buffs_grid.addWidget(chk, row_i, 0)

            row_widgets: list[QWidget] = [chk]
            if has_lv:
                spin = QSpinBox()
                spin.setRange(min_lv, max_lv)
                spin.setValue(min_lv)
                spin.setFixedWidth(52)
                spin.setEnabled(False)
                self._sc_spins[sc_key] = spin
                buffs_grid.addWidget(spin, row_i, 1)
                row_widgets.append(spin)
                chk.toggled.connect(spin.setEnabled)

            chk.toggled.connect(self._on_changed)
            self._self_buff_widgets[sc_key] = row_widgets

        for spin in self._sc_spins.values():
            spin.valueChanged.connect(self._on_changed)

        self._sub_self.add_content_widget(buffs_widget)
        self.add_content_widget(self._sub_self)

        # ── 2. Party Buffs (stub) ─────────────────────────────────────────
        self._sub_party = CollapsibleSubGroup("Party Buffs", default_collapsed=False)
        self._sub_party.add_content_widget(_stub_label("(Priest/Blacksmith buffs — Session M)"))
        self.add_content_widget(self._sub_party)

        # ── 3. Ground Effects (stub) ──────────────────────────────────────
        self._sub_ground = CollapsibleSubGroup("Ground Effects", default_collapsed=False)
        self._sub_ground.add_content_widget(_stub_label("(Sage ground buffs — Session O)"))
        self.add_content_widget(self._sub_ground)

        # ── 4. Bard Songs (stub) ──────────────────────────────────────────
        self._sub_bard = CollapsibleSubGroup("Bard Songs", default_collapsed=False)
        self._sub_bard.add_content_widget(_stub_label("(Bard songs — Session M2)"))
        self.add_content_widget(self._sub_bard)

        # ── 5. Dancer Dances (stub) ───────────────────────────────────────
        self._sub_dancer = CollapsibleSubGroup("Dancer Dances", default_collapsed=False)
        self._sub_dancer.add_content_widget(_stub_label("(Dancer dances — Session M2)"))
        self.add_content_widget(self._sub_dancer)

        # ── 6. Ensembles (stub) ───────────────────────────────────────────
        self._sub_ensemble = CollapsibleSubGroup("Ensembles", default_collapsed=False)
        self._sub_ensemble.add_content_widget(_stub_label("(Bard+Dancer ensembles — Session M2)"))
        self.add_content_widget(self._sub_ensemble)

        # ── 7. Guild Buffs (stub) ─────────────────────────────────────────
        self._sub_guild = CollapsibleSubGroup("Guild Buffs", default_collapsed=True)
        self._sub_guild.add_content_widget(_stub_label("(Guild skills — Session M)"))
        self.add_content_widget(self._sub_guild)

        # ── 8. Miscellaneous Effects (stub) ───────────────────────────────
        self._sub_misc = CollapsibleSubGroup("Miscellaneous Effects", default_collapsed=False)
        self._sub_misc.add_content_widget(_stub_label("(Item proc / pet buffs — future session)"))
        self.add_content_widget(self._sub_misc)

    # ── Job filtering ──────────────────────────────────────────────────────

    def update_job(self, job_id: int) -> None:
        self._current_job_id = job_id
        show_all = self._show_all_chk.isChecked()
        job_skills = loader.get_skills_for_job(job_id)
        for sc_key, _disp, _has_lv, _min, _max, source_skill in _SELF_BUFFS:
            visible = show_all or (source_skill in job_skills)
            for w in self._self_buff_widgets.get(sc_key, []):
                w.setVisible(visible)
            if not visible and sc_key in self._sc_checks:
                chk = self._sc_checks[sc_key]
                chk.blockSignals(True)
                chk.setChecked(False)
                chk.blockSignals(False)
                if sc_key in self._sc_spins:
                    self._sc_spins[sc_key].blockSignals(True)
                    self._sc_spins[sc_key].setValue(1)
                    self._sc_spins[sc_key].blockSignals(False)

    # ── Internal ───────────────────────────────────────────────────────────

    def _on_show_all_toggled(self, _: bool) -> None:
        self.update_job(self._current_job_id)

    def _on_changed(self) -> None:
        self.changed.emit()
        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def _build_summary(self) -> str:
        parts: list[str] = []
        for sc_key, display, has_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks.get(sc_key)
            if chk and chk.isChecked():
                if has_lv and sc_key in self._sc_spins:
                    parts.append(f"{display} {self._sc_spins[sc_key].value()}")
                else:
                    parts.append(display)
        return "  ·  ".join(parts) if parts else "No active buffs"

    # ── Compact API ────────────────────────────────────────────────────────

    def _build_compact_widget(self) -> None:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)
        self._compact_summary_lbl = QLabel(self._build_summary())
        self._compact_summary_lbl.setObjectName("passive_compact_summary")
        self._compact_summary_lbl.setWordWrap(True)
        layout.addWidget(self._compact_summary_lbl)
        w.setVisible(False)
        self._compact_widget = w
        self.layout().addWidget(w)

    def _enter_compact_view(self) -> None:
        self._pre_compact_collapsed = self._is_collapsed
        if self._compact_widget is None:
            self._build_compact_widget()
        self._compact_summary_lbl.setText(self._build_summary())  # type: ignore[union-attr]
        self._content_frame.setVisible(False)
        self._compact_widget.setVisible(True)
        self._is_collapsed = False
        self._arrow.setText("▼")

    def _exit_compact_view(self) -> None:
        if self._compact_widget is not None:
            self._compact_widget.setVisible(False)
        restored = self._pre_compact_collapsed if self._pre_compact_collapsed is not None else False
        self._pre_compact_collapsed = None
        self._is_collapsed = restored
        self._content_frame.setVisible(not restored)
        self._arrow.setText("▶" if restored else "▼")

    # ── Public API ─────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        for chk in self._sc_checks.values():
            chk.blockSignals(True)
        for spin in self._sc_spins.values():
            spin.blockSignals(True)

        active = build.active_status_levels
        for sc_key, _, has_lv, min_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks[sc_key]
            is_active = sc_key in active
            chk.setChecked(is_active)
            if has_lv and sc_key in self._sc_spins:
                spin = self._sc_spins[sc_key]
                spin.setValue(active.get(sc_key, min_lv))
                spin.setEnabled(is_active)

        for chk in self._sc_checks.values():
            chk.blockSignals(False)
        for spin in self._sc_spins.values():
            spin.blockSignals(False)

        self._current_job_id = build.job_id
        self.update_job(build.job_id)

        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def collect_into(self, build: PlayerBuild) -> None:
        active: dict[str, int] = build.active_status_levels.copy()
        # Remove any keys we own, then re-add active ones
        for sc_key, *_ in _SELF_BUFFS:
            active.pop(sc_key, None)

        for sc_key, _, has_lv, min_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks[sc_key]
            if chk.isChecked():
                if has_lv and sc_key in self._sc_spins:
                    active[sc_key] = self._sc_spins[sc_key].value()
                else:
                    active[sc_key] = min_lv

        build.active_status_levels = active
