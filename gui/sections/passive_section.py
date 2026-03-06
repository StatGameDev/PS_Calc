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

from core.models.build import PlayerBuild
from gui.section import Section

# ── Self buffs that feed active_status_levels ─────────────────────────────────
# (sc_key, display_name, has_level, min_lv, max_lv)
_SELF_BUFFS: list[tuple[str, str, bool, int, int]] = [
    ("SC_AURABLADE",       "Aura Blade",       True,  1, 5),
    ("SC_MAXIMIZEPOWER",   "Maximize Power",   False, 1, 1),
    ("SC_OVERTHRUST",      "Overthrust",        True,  1, 10),
    ("SC_OVERTHRUSTMAX",   "Max. Overthrust",   True,  1, 5),
    # ASPD buffs (G9) — source: status.c status_calc_aspd_rate (1000=100% scale)
    # Quicken/Adrenaline: aspd_rate -= max(active). Only highest applies.
    ("SC_TWOHANDQUICKEN",  "Two-Hand Quicken", False, 1,  1),   # val2=300 (fixed)
    ("SC_SPEARQUICKEN",    "Spear Quicken",    True,  1, 10),   # val2=200+10*lv (level matters)
    ("SC_ONEHANDQUICKEN",  "One-Hand Quicken", False, 1,  1),   # val2=300 (fixed)
    ("SC_ADRENALINE",      "Adrenaline Rush",  False, 1,  1),   # val3=300 self / 200 party; no lv effect
    ("SC_ASSNCROS",        "Assassin Cross",   False, 1,  1),   # val2=f(bard_agi) — placeholder
]

# ── Masteries that feed mastery_levels ────────────────────────────────────────
# (mastery_key, display_name)
_MASTERIES: list[tuple[str, str]] = [
    ("SM_SWORD",         "Sword"),
    ("SM_TWOHANDSWORD",  "Two-Hand Sword"),
    ("KN_SPEARMASTERY",  "Spear Mastery"),
    ("AM_AXEMASTERY",    "Axe Mastery"),
    ("PR_MACEMASTERY",   "Mace Mastery"),
    ("MO_IRONHAND",      "Iron Hand"),
    ("BA_MUSICALLESSON", "Musical Lesson"),
    ("DC_DANCINGLESSON", "Dancing Lesson"),
    ("SA_ADVANCEDBOOK",  "Advanced Book"),
    ("AS_KATAR",         "Katar"),
    ("ASC_KATAR",        "Adv. Katar"),
    ("AL_DEMONBANE",     "Demon Bane"),
    ("HT_BEASTBANE",     "Beast Bane"),
]

# Masteries restricted to specific job IDs. Keys not present here are always visible.
_MASTERY_JOB_FILTER: dict[str, set[int]] = {
    "ASC_KATAR": {24},   # Assassin Cross only
}


def _make_sub_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("passive_sub_header")
    return lbl


class PassiveSection(Section):
    """Phase 1.5 — Self Buffs, Party Buffs, Masteries, Flags sub-groups."""

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

        # ── Self Buffs ────────────────────────────────────────────────────
        self.add_content_widget(_make_sub_header("Self Buffs"))

        buffs_widget = QWidget()
        buffs_grid = QGridLayout(buffs_widget)
        buffs_grid.setContentsMargins(0, 0, 0, 0)
        buffs_grid.setHorizontalSpacing(6)
        buffs_grid.setVerticalSpacing(3)

        for row_i, (sc_key, display, has_lv, min_lv, max_lv) in enumerate(_SELF_BUFFS):
            chk = QCheckBox(display)
            chk.setObjectName("passive_sc_check")
            self._sc_checks[sc_key] = chk
            buffs_grid.addWidget(chk, row_i, 0)

            if has_lv:
                spin = QSpinBox()
                spin.setRange(min_lv, max_lv)
                spin.setValue(min_lv)
                spin.setFixedWidth(52)
                spin.setEnabled(False)
                self._sc_spins[sc_key] = spin
                buffs_grid.addWidget(spin, row_i, 1)

                chk.toggled.connect(spin.setEnabled)

            chk.toggled.connect(self._on_passives_changed)

        for spin in self._sc_spins.values():
            spin.valueChanged.connect(self._on_passives_changed)

        self.add_content_widget(buffs_widget)

        # ── Party Buffs (placeholder) ─────────────────────────────────────
        self.add_content_widget(_make_sub_header("Party Buffs"))
        party_placeholder = QLabel("Party buff controls coming in a future phase.")
        party_placeholder.setObjectName("passive_placeholder")
        self.add_content_widget(party_placeholder)

        # ── Masteries ─────────────────────────────────────────────────────
        self.add_content_widget(_make_sub_header("Masteries"))

        mastery_widget = QWidget()
        mastery_grid = QGridLayout(mastery_widget)
        mastery_grid.setContentsMargins(0, 0, 0, 0)
        mastery_grid.setHorizontalSpacing(12)
        mastery_grid.setVerticalSpacing(3)

        for i, (m_key, m_display) in enumerate(_MASTERIES):
            row = i // 2
            col_base = (i % 2) * 2

            lbl = QLabel(m_display)
            lbl.setObjectName("passive_mastery_label")
            self._mastery_labels[m_key] = lbl
            mastery_grid.addWidget(lbl, row, col_base)

            spin = QSpinBox()
            spin.setRange(0, 10)
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
        """Show/hide job-restricted mastery rows based on current job_id."""
        for m_key, _ in _MASTERIES:
            restriction = _MASTERY_JOB_FILTER.get(m_key)
            if restriction is None:
                continue
            visible = job_id in restriction
            if m_key in self._mastery_labels:
                self._mastery_labels[m_key].setVisible(visible)
            if m_key in self._mastery_spins:
                spin = self._mastery_spins[m_key]
                spin.setVisible(visible)
                if not visible:
                    spin.setValue(0)

    # ── Internal ──────────────────────────────────────────────────────────

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

        for m_key, m_display in _MASTERIES:
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

        for m_key, _ in _MASTERIES:
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
            for m_key, _ in _MASTERIES
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
