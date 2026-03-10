from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QWidget,
)

from core.data_loader import loader
from core.models.build import PlayerBuild
from gui.section import Section

# Self-buff rows have moved to buffs_section.py (Session M0).
# passive_section now contains only: Passives (masteries) + Flags.

# ── Passives (masteries and other passive skills) ─────────────────────────────
# (skill_key, display_name, max_lv, source_skill)
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
    ("BS_HILTBINDING",   "Hilt Binding",    1,  "BS_HILTBINDING"),
    ("SA_DRAGONOLOGY",   "Dragonology",     5,  "SA_DRAGONOLOGY"),
    ("AC_OWL",           "Owl's Eye",      10,  "AC_OWL"),
    ("CR_TRUST",         "Faith",          10,  "CR_TRUST"),
    ("BS_WEAPONRESEARCH","Weapon Research",10,  "BS_WEAPONRESEARCH"),
    ("AC_VULTURE",       "Vulture's Eye",  10,  "AC_VULTURE"),
    ("GS_SINGLEACTION",  "Single Action",  10,  "GS_SINGLEACTION"),
    ("GS_SNAKEEYE",      "Snake's Eye",    10,  "GS_SNAKEEYE"),
    ("TF_MISS",          "Improve Dodge",  10,  "TF_MISS"),
    ("MO_DODGE",         "Dodge",          10,  "MO_DODGE"),
    ("BS_SKINTEMPER",    "Skin Tempering",  5,  "BS_SKINTEMPER"),
    ("AL_DP",            "Divine Protection", 10, "AL_DP"),
    ("SM_RECOVERY",      "Recuperation",   10,  "SM_RECOVERY"),
    ("MG_SRECOVERY",     "Spiritual Recovery", 10, "MG_SRECOVERY"),
    ("NJ_NINPOU",        "Ninpou",          4,  "NJ_NINPOU"),
    ("NJ_TOBIDOUGU",     "Throw Mastery",  10,  "NJ_TOBIDOUGU"),
]


class _NoWheelCombo(QComboBox):
    """QComboBox that ignores scroll wheel events."""
    def wheelEvent(self, event) -> None:
        event.ignore()


def _make_sub_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("passive_sub_header")
    return lbl


class PassiveSection(Section):
    """Session M0 — Passives (masteries) + Flags. Self-buffs moved to BuffsSection."""

    passives_changed = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None):
        super().__init__(key, display_name, default_collapsed, compact_mode, parent)

        self._compact_widget: QWidget | None = None
        self._compact_summary_lbl: QLabel | None = None
        self._current_job_id: int = 0

        self._mastery_combos: dict[str, QComboBox]  = {}  # max_lv > 1 → dropdown
        self._mastery_checks: dict[str, QCheckBox]  = {}  # max_lv == 1 → toggle
        self._mastery_labels: dict[str, QLabel]     = {}

        # ── Passives (masteries) ──────────────────────────────────────────
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

            if max_lv == 1:
                chk = QCheckBox()
                self._mastery_checks[m_key] = chk
                mastery_grid.addWidget(chk, row, col_base + 1)
                chk.toggled.connect(self._on_passives_changed)
            else:
                combo = _NoWheelCombo()
                combo.addItem("Off", 0)
                for lv in range(1, max_lv + 1):
                    combo.addItem(str(lv), lv)
                combo.setCurrentIndex(0)
                self._mastery_combos[m_key] = combo
                mastery_grid.addWidget(combo, row, col_base + 1)
                combo.currentIndexChanged.connect(self._on_passives_changed)

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

        ranged_lbl = QLabel("Ranged Override:")
        ranged_lbl.setObjectName("passive_mastery_label")
        flags_layout.addWidget(ranged_lbl, 1, 0)

        ranged_row = QWidget()
        ranged_layout = QHBoxLayout(ranged_row)
        ranged_layout.setContentsMargins(0, 0, 0, 0)
        ranged_layout.setSpacing(6)

        self._ranged_group = QButtonGroup(self)
        self._ranged_group.setExclusive(True)

        self._ranged_auto   = QRadioButton("Auto")
        self._ranged_melee  = QRadioButton("Melee")
        self._ranged_ranged = QRadioButton("Ranged")
        self._ranged_auto.setChecked(True)

        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            self._ranged_group.addButton(rb)
            ranged_layout.addWidget(rb)
            rb.toggled.connect(self._on_passives_changed)

        flags_layout.addWidget(ranged_row, 1, 1, 1, 2)
        self.add_content_widget(flags_widget)

    # ── Value helpers ──────────────────────────────────────────────────────

    def _get_mastery_value(self, m_key: str) -> int:
        if m_key in self._mastery_checks:
            return 1 if self._mastery_checks[m_key].isChecked() else 0
        combo = self._mastery_combos.get(m_key)
        return (combo.currentData() or 0) if combo else 0

    def _set_mastery_value(self, m_key: str, value: int) -> None:
        if m_key in self._mastery_checks:
            self._mastery_checks[m_key].setChecked(value > 0)
        elif m_key in self._mastery_combos:
            combo = self._mastery_combos[m_key]
            idx = combo.findData(value)
            combo.setCurrentIndex(idx if idx >= 0 else 0)

    # ── Public API (job visibility) ────────────────────────────────────────

    def update_job(self, job_id: int) -> None:
        self._current_job_id = job_id
        job_skills = loader.get_skills_for_job(job_id)
        for m_key, _disp, max_lv, source_skill in _PASSIVES:
            visible = source_skill in job_skills
            if m_key in self._mastery_labels:
                self._mastery_labels[m_key].setVisible(visible)
            w = self._mastery_combos.get(m_key) or self._mastery_checks.get(m_key)
            if w is not None:
                w.setVisible(visible)
                if not visible:
                    w.blockSignals(True)
                    if isinstance(w, QCheckBox):
                        w.setChecked(False)
                    else:
                        w.setCurrentIndex(0)
                    w.blockSignals(False)

    # ── Internal ──────────────────────────────────────────────────────────

    def _on_passives_changed(self) -> None:
        self.passives_changed.emit()
        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def _build_summary(self) -> str:
        parts: list[str] = []
        for m_key, m_display, *_ in _PASSIVES:
            val = self._get_mastery_value(m_key)
            if val > 0:
                parts.append(f"{m_display} {val}")
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
        all_widgets = (
            list(self._mastery_combos.values()) +
            list(self._mastery_checks.values())
        )
        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            rb.blockSignals(True)
        self._riding_peco_chk.blockSignals(True)
        self._no_sizefix_chk.blockSignals(True)
        for w in all_widgets:
            w.blockSignals(True)

        for m_key, _, *_ in _PASSIVES:
            self._set_mastery_value(m_key, build.mastery_levels.get(m_key, 0))

        self._riding_peco_chk.setChecked(build.is_riding_peco)
        self._no_sizefix_chk.setChecked(build.no_sizefix)

        override = build.is_ranged_override
        if override is None:
            self._ranged_auto.setChecked(True)
        elif override is False:
            self._ranged_melee.setChecked(True)
        else:
            self._ranged_ranged.setChecked(True)

        for w in all_widgets:
            w.blockSignals(False)
        for rb in (self._ranged_auto, self._ranged_melee, self._ranged_ranged):
            rb.blockSignals(False)
        self._riding_peco_chk.blockSignals(False)
        self._no_sizefix_chk.blockSignals(False)

        self._current_job_id = build.job_id
        self.update_job(build.job_id)

        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def collect_into(self, build: PlayerBuild) -> None:
        build.mastery_levels = {
            m_key: self._get_mastery_value(m_key)
            for m_key, *_ in _PASSIVES
            if self._get_mastery_value(m_key) > 0
        }
        build.is_riding_peco = self._riding_peco_chk.isChecked()
        build.no_sizefix = self._no_sizefix_chk.isChecked()
        if self._ranged_auto.isChecked():
            build.is_ranged_override = None
        elif self._ranged_melee.isChecked():
            build.is_ranged_override = False
        else:
            build.is_ranged_override = True
