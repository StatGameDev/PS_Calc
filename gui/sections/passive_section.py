from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from gui.section import Section

# ── Self buffs and party buffs that feed active_status_levels ─────────────────
# (sc_key, display_name, has_level, min_lv, max_lv, source_skill, buff_type)
# buff_type:
#   "self"  — active skill; show only when job has source_skill in its skill tree
#   "party" — received from party member; always visible regardless of job
#
# *SC_ONEHANDQUICKEN: KN_ONEHAND is a Knight/LK skill normally accessible
#  via Soul Linker buff. Treated as "self" (visible for Knight/LK); others
#  use Show All to enable it when received via Soul Link.
_SELF_BUFFS: list[tuple] = [
    ("SC_AURABLADE",      "Aura Blade",           True,  1,  5,  "LK_AURABLADE",      "self"),
    ("SC_MAXIMIZEPOWER",  "Maximize Power",        False, 1,  1,  "BS_MAXIMIZE",       "self"),
    ("SC_OVERTHRUST",     "Overthrust",            True,  1,  10, "BS_OVERTHRUST",     "self"),
    ("SC_OVERTHRUSTMAX",  "Max. Overthrust",       True,  1,  5,  "WS_OVERTHRUSTMAX",  "self"),
    ("SC_TWOHANDQUICKEN", "Two-Hand Quicken",      False, 1,  1,  "KN_TWOHANDQUICKEN", "self"),
    ("SC_SPEARQUICKEN",   "Spear Quicken",         True,  1,  10, "CR_SPEARQUICKEN",   "self"),
    ("SC_ONEHANDQUICKEN", "One-Hand Quicken*",     False, 1,  1,  "KN_ONEHAND",        "self"),
    # Party buffs — always visible; source_skill is the caster's skill
    ("SC_ADRENALINE",     "Adrenaline Rush",       False, 1,  1,  "BS_ADRENALINE",     "party"),
    ("SC_ASSNCROS",       "Assassin Cross (Song)", False, 1,  1,  "BA_ASSASSINCROSS",  "party"),
]

# ── Passives (masteries and other passive skills) ─────────────────────────────
# (skill_key, display_name, max_lv, source_skill)
# skill_key used as key in build.mastery_levels (must match mastery_fix.json).
# source_skill is the skill tree name for job-visibility lookup.
# All are buff_type="passive"; shown only when job has source_skill in skill tree.
_PASSIVES: list[tuple] = [
    ("SM_SWORD",         "Sword",          10, "SM_SWORD"),
    ("SM_TWOHANDSWORD",  "Two-Hand Sword", 10, "SM_TWOHAND"),
    ("KN_SPEARMASTERY",  "Spear Mastery",  10, "KN_SPEARMASTERY"),
    ("AM_AXEMASTERY",    "Axe Mastery",    10, "AM_AXEMASTERY"),
    ("PR_MACEMASTERY",   "Mace Mastery",   10, "PR_MACEMASTERY"),
    ("MO_IRONHAND",      "Iron Hand",      10, "MO_IRONHAND"),
    ("BA_MUSICALLESSON", "Musical Lesson", 10, "BA_MUSICALLESSON"),
    ("DC_DANCINGLESSON", "Dancing Lesson", 10, "DC_DANCINGLESSON"),
    ("SA_ADVANCEDBOOK",  "Advanced Book",  10, "SA_ADVANCEDBOOK"),
    ("TF_DOUBLE",        "Double Attack",  10, "TF_DOUBLE"),
    ("AS_KATAR",         "Katar",          10, "AS_KATAR"),
    ("ASC_KATAR",        "Adv. Katar",     10, "ASC_KATAR"),
    ("AL_DEMONBANE",     "Demon Bane",     10, "AL_DEMONBANE"),
    ("HT_BEASTBANE",     "Beast Bane",     10, "HT_BEASTBANE"),
    ("BS_HILTBINDING",   "Hilt Binding",   1,  "BS_HILTBINDING"),
]


def _make_sub_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("passive_sub_header")
    return lbl


class PassiveSection(Section):
    """Phase 1.5 — Self Buffs, Party Buffs, Passives, Flags sub-groups."""

    passives_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_summary_lbl: QLabel | None = None

        # Storage
        self._sc_checks:  dict[str, QCheckBox] = {}
        self._sc_spins:   dict[str, QSpinBox]  = {}
        self._mastery_spins:  dict[str, QSpinBox] = {}
        self._mastery_labels: dict[str, QLabel]   = {}
        # Track which widgets belong to job-filtered "self" buff rows
        self._self_buff_widgets: dict[str, list[QWidget]] = {}

        # ── Section header: Show All checkbox ─────────────────────────────
        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self._show_all_chk = QCheckBox("Show All")
        self._show_all_chk.setObjectName("passive_show_all")
        self._show_all_chk.toggled.connect(self._on_show_all_toggled)
        header_layout.addStretch()
        header_layout.addWidget(self._show_all_chk)
        self.add_content_widget(header_row)

        # ── Self Buffs ────────────────────────────────────────────────────
        self.add_content_widget(_make_sub_header("Self Buffs"))

        buffs_widget = QWidget()
        buffs_grid = QGridLayout(buffs_widget)
        buffs_grid.setContentsMargins(0, 0, 0, 0)
        buffs_grid.setHorizontalSpacing(6)
        buffs_grid.setVerticalSpacing(3)

        party_row_start: int | None = None

        for row_i, (sc_key, display, has_lv, min_lv, max_lv, source_skill, buff_type) in enumerate(_SELF_BUFFS):
            if buff_type == "party" and party_row_start is None:
                # Visual separator label before party buffs
                sep = QLabel("— Party / Song Buffs —")
                sep.setObjectName("passive_sub_separator")
                buffs_grid.addWidget(sep, row_i, 0, 1, 2)
                party_row_start = row_i
                # Shift actual widgets down one row
                actual_row = row_i + 1
            elif buff_type == "party":
                actual_row = row_i + 1
            else:
                actual_row = row_i

            chk = QCheckBox(display)
            chk.setObjectName("passive_sc_check")
            self._sc_checks[sc_key] = chk
            buffs_grid.addWidget(chk, actual_row, 0)

            row_widgets: list[QWidget] = [chk]

            if has_lv:
                spin = QSpinBox()
                spin.setRange(min_lv, max_lv)
                spin.setValue(min_lv)
                spin.setFixedWidth(52)
                spin.setEnabled(False)
                self._sc_spins[sc_key] = spin
                buffs_grid.addWidget(spin, actual_row, 1)
                row_widgets.append(spin)
                chk.toggled.connect(spin.setEnabled)

            chk.toggled.connect(self._on_passives_changed)

            if buff_type == "self":
                self._self_buff_widgets[sc_key] = row_widgets

        for spin in self._sc_spins.values():
            spin.valueChanged.connect(self._on_passives_changed)

        self.add_content_widget(buffs_widget)

        # ── Passives (masteries + other passive skills) ───────────────────
        self.add_content_widget(_make_sub_header("Passives"))

        mastery_widget = QWidget()
        mastery_grid = QGridLayout(mastery_widget)
        mastery_grid.setContentsMargins(0, 0, 0, 0)
        mastery_grid.setHorizontalSpacing(12)
        mastery_grid.setVerticalSpacing(3)

        for i, (m_key, m_display, max_lv, source_skill) in enumerate(_PASSIVES):
            row = i // 2
            col_base = (i % 2) * 2

            lbl = QLabel(m_display)
            lbl.setObjectName("passive_mastery_label")
            self._mastery_labels[m_key] = lbl
            mastery_grid.addWidget(lbl, row, col_base)

            spin = QSpinBox()
            spin.setRange(0, max_lv)
            spin.setValue(0)
            spin.setFixedWidth(52)
            self._mastery_spins[m_key] = spin
            mastery_grid.addWidget(spin, row, col_base + 1)

            spin.valueChanged.connect(self._on_passives_changed)

        self.add_content_widget(mastery_widget)

        # ── Flags ─────────────────────────────────────────────────────────
        self.add_content_widget(_make_sub_header("Flags"))

        flags_widget = QWidget()
        flags_layout = QGridLayout(flags_widget)
        flags_layout.setContentsMargins(0, 0, 0, 0)
        flags_layout.setHorizontalSpacing(8)
        flags_layout.setVerticalSpacing(3)

        self._riding_peco_chk = QCheckBox("Riding Peco")
        self._riding_peco_chk.toggled.connect(self._on_passives_changed)
        flags_layout.addWidget(self._riding_peco_chk, 0, 0)

        self._no_sizefix_chk = QCheckBox("No Size Fix")
        self._no_sizefix_chk.toggled.connect(self._on_passives_changed)
        flags_layout.addWidget(self._no_sizefix_chk, 0, 1)

        # is_ranged_override: Auto | Melee | Ranged
        ranged_lbl = QLabel("Ranged Override:")
        ranged_lbl.setObjectName("passive_mastery_label")
        flags_layout.addWidget(ranged_lbl, 1, 0)

        ranged_row = QWidget()
        ranged_layout = QHBoxLayout(ranged_row)
        ranged_layout.setContentsMargins(0, 0, 0, 0)
        ranged_layout.setSpacing(6)

        self._ranged_group = QButtonGroup(self)
        self._ranged_group.setExclusive(True)

        self._ranged_auto  = QRadioButton("Auto")
        self._ranged_melee = QRadioButton("Melee")
        self._ranged_ranged= QRadioButton("Ranged")
        self._ranged_auto.setChecked(True)

        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            self._ranged_group.addButton(rb)
            ranged_layout.addWidget(rb)
            rb.toggled.connect(self._on_passives_changed)

        flags_layout.addWidget(ranged_row, 1, 1, 1, 2)

        self.add_content_widget(flags_widget)

    # ── Public API (job visibility) ────────────────────────────────────────

    def update_job(self, job_id: int) -> None:
        """Show/hide job-restricted rows based on current job_id and skill tree."""
        self._current_job_id = job_id
        show_all = self._show_all_chk.isChecked()
        job_skills = loader.get_skills_for_job(job_id)

        # Self buff rows: visible when job has the source skill (or Show All)
        for sc_key, _disp, _has_lv, _min, _max, source_skill, buff_type in _SELF_BUFFS:
            if buff_type != "self":
                continue
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

        # Passive rows: visible when job has the source skill (or Show All)
        for m_key, _disp, _max_lv, source_skill in _PASSIVES:
            visible = show_all or (source_skill in job_skills)
            if m_key in self._mastery_labels:
                self._mastery_labels[m_key].setVisible(visible)
            if m_key in self._mastery_spins:
                spin = self._mastery_spins[m_key]
                spin.setVisible(visible)
                if not visible:
                    spin.blockSignals(True)
                    spin.setValue(0)
                    spin.blockSignals(False)

    # ── Internal ──────────────────────────────────────────────────────────

    def _on_show_all_toggled(self, _: bool) -> None:
        self.update_job(getattr(self, "_current_job_id", 0))

    def _on_passives_changed(self) -> None:
        self.passives_changed.emit()
        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def _build_summary(self) -> str:
        """Single-line summary for compact view."""
        parts: list[str] = []

        for sc_key, display, has_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks.get(sc_key)
            if chk and chk.isChecked():
                if has_lv and sc_key in self._sc_spins:
                    parts.append(f"{display} {self._sc_spins[sc_key].value()}")
                else:
                    parts.append(display)

        for m_key, m_display, *_ in _PASSIVES:
            spin = self._mastery_spins.get(m_key)
            if spin and spin.value() > 0:
                parts.append(f"{m_display} {spin.value()}")

        flags: list[str] = []
        if self._riding_peco_chk.isChecked():
            flags.append("Riding")
        if self._no_sizefix_chk.isChecked():
            flags.append("NoSizeFix")
        if self._ranged_melee.isChecked():
            flags.append("Melee")
        elif self._ranged_ranged.isChecked():
            flags.append("Ranged")
        if flags:
            parts.append(f"[{', '.join(flags)}]")

        return "  ·  ".join(parts) if parts else "No active passives"

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

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build: PlayerBuild) -> None:
        """Populate all passive widgets from build without emitting change signals."""
        # Block all signals
        for chk in self._sc_checks.values():
            chk.blockSignals(True)
        for spin in self._sc_spins.values():
            spin.blockSignals(True)
        for spin in self._mastery_spins.values():
            spin.blockSignals(True)
        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            rb.blockSignals(True)
        self._riding_peco_chk.blockSignals(True)
        self._no_sizefix_chk.blockSignals(True)

        active = build.active_status_levels

        for sc_key, _, has_lv, min_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks[sc_key]
            is_active = sc_key in active
            chk.setChecked(is_active)
            if has_lv and sc_key in self._sc_spins:
                spin = self._sc_spins[sc_key]
                spin.setValue(active.get(sc_key, min_lv))
                spin.setEnabled(is_active)

        for m_key, _, *_ in _PASSIVES:
            spin = self._mastery_spins[m_key]
            spin.setValue(build.mastery_levels.get(m_key, 0))

        self._riding_peco_chk.setChecked(build.is_riding_peco)
        self._no_sizefix_chk.setChecked(build.no_sizefix)

        override = build.is_ranged_override
        if override is None:
            self._ranged_auto.setChecked(True)
        elif override is False:
            self._ranged_melee.setChecked(True)
        else:
            self._ranged_ranged.setChecked(True)

        # Unblock
        for chk in self._sc_checks.values():
            chk.blockSignals(False)
        for spin in self._sc_spins.values():
            spin.blockSignals(False)
        for spin in self._mastery_spins.values():
            spin.blockSignals(False)
        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            rb.blockSignals(False)
        self._riding_peco_chk.blockSignals(False)
        self._no_sizefix_chk.blockSignals(False)

        self._current_job_id = build.job_id
        self.update_job(build.job_id)

        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def collect_into(self, build: PlayerBuild) -> None:
        """Write section state into an existing PlayerBuild in-place."""
        active: dict[str, int] = {}
        for sc_key, _, has_lv, min_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks[sc_key]
            if chk.isChecked():
                if has_lv and sc_key in self._sc_spins:
                    active[sc_key] = self._sc_spins[sc_key].value()
                else:
                    active[sc_key] = min_lv
        build.active_status_levels = active

        build.mastery_levels = {
            m_key: self._mastery_spins[m_key].value()
            for m_key, *_ in _PASSIVES
            if self._mastery_spins[m_key].value() > 0
        }

        build.is_riding_peco = self._riding_peco_chk.isChecked()
        build.no_sizefix = self._no_sizefix_chk.isChecked()

        if self._ranged_auto.isChecked():
            build.is_ranged_override = None
        elif self._ranged_melee.isChecked():
            build.is_ranged_override = False
        else:
            build.is_ranged_override = True
