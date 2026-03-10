from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

# Bard job IDs: Bard (19), Clown (4020)
_BARD_JOBS   = frozenset({19, 4020})
# Dancer job IDs: Dancer (20), Gypsy (4021)
_DANCER_JOBS = frozenset({20, 4021})

# ── Self Buffs ────────────────────────────────────────────────────────────────
# (sc_key, display_name, has_level, min_lv, max_lv, source_skill)
# All are job-filtered via update_job(). Show All overrides filtering.
# SC_ADRENALINE and SC_ASSNCROS are in support_buffs / song_state — not here.
_SELF_BUFFS: list[tuple] = [
    # ── Existing (Sessions 1–M2) ──────────────────────────────────────────────
    ("SC_AURABLADE",          "Aura Blade",           True,  1,  5,  "LK_AURABLADE"),
    ("SC_MAXIMIZEPOWER",      "Maximize Power",        False, 1,  1,  "BS_MAXIMIZE"),
    ("SC_OVERTHRUST",         "Overthrust",            True,  1,  10, "BS_OVERTHRUST"),
    ("SC_OVERTHRUSTMAX",      "Max. Overthrust",       True,  1,  5,  "WS_OVERTHRUSTMAX"),
    ("SC_TWOHANDQUICKEN",     "Two-Hand Quicken",      False, 1,  1,  "KN_TWOHANDQUICKEN"),
    ("SC_SPEARQUICKEN",       "Spear Quicken",         True,  1,  10, "CR_SPEARQUICKEN"),
    ("SC_ONEHANDQUICKEN",     "One-Hand Quicken*",     False, 1,  1,  "KN_ONEHAND"),
    # ── Session N — Swordman / Knight / Crusader ──────────────────────────────
    # SC_SUB_WEAPONPROPERTY: stub; fire property + 20% dmg for one hit (battle.c:996-1001)
    ("SC_SUB_WEAPONPROPERTY", "Magnum Break",          False, 1,  1,  "SM_MAGNUM"),
    # SC_AUTOBERSERK: stub; auto-applies SC_PROVOKE when HP<25% — no outgoing dmg formula
    ("SC_AUTOBERSERK",        "Auto Berserk",          False, 1,  1,  "SM_AUTOBERSERK"),
    # SC_ENDURE: mdef += val1=lv — status_calculator.py (status.c:5149)
    ("SC_ENDURE",             "Endure",                True,  1,  10, "SM_ENDURE"),
    # SC_AUTOGUARD: stub; block chance incoming — no outgoing effect
    ("SC_AUTOGUARD",          "Auto Guard",            False, 1,  1,  "CR_AUTOGUARD"),
    # SC_REFLECTSHIELD: stub; reflect incoming melee — advanced/incoming only
    ("SC_REFLECTSHIELD",      "Reflect Shield",        False, 1,  1,  "CR_REFLECTSHIELD"),
    # SC_DEFENDER: aspd_rate += val4=250-50×lv — status_calculator.py (status_calc_aspd_rate:5674)
    ("SC_DEFENDER",           "Defender",              True,  1,  5,  "CR_DEFENDER"),
    # ── Session N — Monk / Champion ──────────────────────────────────────────
    # MO_SPIRITBALL: no SC; sphere count stored for future skill ratio use
    ("MO_SPIRITBALL",         "Spirit Spheres",        True,  1,  5,  "MO_CALLSPIRITS"),
    # SC_STEELBODY: aspd_rate += 250; def cap=90 stub — status_calculator.py
    ("SC_STEELBODY",          "Steel Body",            False, 1,  1,  "MO_STEELBODY"),
    # SC_EXPLOSIONSPIRITS: cri += val2=75+25×lv — status_calculator.py (status.c:4753)
    ("SC_EXPLOSIONSPIRITS",   "Fury",                  True,  1,  10, "MO_EXPLOSIONSPIRITS"),
    # ── Session N — Archer / Hunter ───────────────────────────────────────────
    # SC_CONCENTRATION: stub; agi/dex % boost needs card-split (status.c:4007, 4195)
    ("SC_CONCENTRATION",      "Concentration",         True,  1,  10, "AC_CONCENTRATION"),
    # ── Session N — Merchant ──────────────────────────────────────────────────
    # SC_SHOUT: str += 4 flat — status_calculator.py (status.c:3956)
    ("SC_SHOUT",              "Loud",                  False, 1,  1,  "MC_LOUD"),
    # ── Session N — Mage / Sage ───────────────────────────────────────────────
    # SC_ENERGYCOAT: stub; SP-absorbs incoming — incoming pipeline only
    ("SC_ENERGYCOAT",         "Energy Coat",           False, 1,  1,  "MG_ENERGYCOAT"),
    # ── Session N — Assassin / Assassin Cross ────────────────────────────────
    # SC_CLOAKING: stub; cloaked state — no outgoing damage effect
    ("SC_CLOAKING",           "Cloaking",              False, 1,  1,  "AS_CLOAKING"),
    # SC_POISONREACT: stub; counter attack — no direct outgoing stat
    ("SC_POISONREACT",        "Poison React",          False, 1,  1,  "AS_POISONREACT"),
    # ── Session N — Rogue / Stalker ──────────────────────────────────────────
    # SC_RG_CCONFINE_M: flee += 10 — status_calculator.py (status.c:4874)
    ("SC_RG_CCONFINE_M",      "Close Confine",         False, 1,  1,  "RG_CLOSECONFINE"),
    # ── Session N — Gunslinger ────────────────────────────────────────────────
    # GS_COINS: no SC; coin count stored for future GS skill ratio use
    ("GS_COINS",              "Coins",                 True,  1,  10, "GS_GLITTERING"),
    # SC_GS_MADNESSCANCEL: batk+=100; aspd_rate-=200 (separate) — status_calculator.py
    ("SC_GS_MADNESSCANCEL",   "Madness Cancel",        False, 1,  1,  "GS_MADNESSCANCEL"),
    # SC_GS_ADJUSTMENT: hit-=30; flee+=30 — status_calculator.py (status.c:4809, 4878)
    ("SC_GS_ADJUSTMENT",      "Adjustment",            False, 1,  1,  "GS_ADJUSTMENT"),
    # SC_GS_ACCURACY: agi+4, dex+4, hit+20 — status_calculator.py (status.c:4023, 4219, 4811)
    ("SC_GS_ACCURACY",        "Increasing Acc.",       False, 1,  1,  "GS_INCREASING"),
    # SC_GS_GATLINGFEVER: batk+=20+10×lv; flee-=5×lv; aspd in max pool — status_calculator.py
    ("SC_GS_GATLINGFEVER",    "Gatling Fever",         True,  1,  10, "GS_GATLINGFEVER"),
    # ── Session N — Ninja ────────────────────────────────────────────────────
    # SC_NJ_NEN: str+=lv; int_+=lv — status_calculator.py (status.c:3962, 4148)
    ("SC_NJ_NEN",             "Nen",                   True,  1,  10, "NJ_NEN"),
    # ── Session N — Taekwon (future job support) ─────────────────────────────
    # SC_RUN: stub; movement speed +55 (status.c:5375); FLEE effect unconfirmed
    ("SC_RUN",                "Sprint",                False, 1,  1,  "TK_RUN"),
]


# ── Party Buffs ───────────────────────────────────────────────────────────────
# Tuple layout:
#   (sc_key, display_name, widget_type, min_lv, max_lv)
#   widget_type: "spin" = QSpinBox(0..max) — 0=off
#                "check" = QCheckBox only
#                "adrenaline" = QCheckBox + QComboBox (special case)
_PARTY_BUFFS: list[tuple] = [
    ("SC_BLESSING",  "Blessing",       "spin",       0, 10),
    ("SC_INC_AGI",   "Increase AGI",   "spin",       0, 10),
    ("SC_GLORIA",    "Gloria",         "check",      0,  0),
    ("SC_ANGELUS",   "Angelus",        "spin",       0, 10),
    ("SC_IMPOSITIO", "Impositio Manus","spin",        0,  5),
    ("SC_ADRENALINE","Adrenaline Rush","adrenaline",  0,  0),
]
# SC_ADRENALINE QComboBox options: index 0 = Self (val3=300), index 1 = Party (val3=200)
_ADRENALINE_VALUES = (300, 200)


# ── Bard Songs ────────────────────────────────────────────────────────────────
# (sc_key, display_name, overrides: list of (stat_key, label))
# stat_key maps to "SC_ASSNCROS_agi" in song_state; shared key is "caster_{stat}"
_BARD_SONGS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("SC_ASSNCROS",  "Assassin Cross", [("agi", "AGI")]),
    ("SC_WHISTLE",   "Whistle",        [("agi", "AGI"), ("luk", "LUK")]),
    ("SC_APPLEIDUN", "Apple of Idun",  [("vit", "VIT")]),
    ("SC_POEMBRAGI", "Poem of Bragi",  [("dex", "DEX"), ("int", "INT")]),
]

# ── Dancer Dances ─────────────────────────────────────────────────────────────
_DANCER_DANCES: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("SC_HUMMING",      "Humming",         [("dex", "DEX")]),
    ("SC_FORTUNE",      "Fortune's Kiss",  [("luk", "LUK")]),
    ("SC_SERVICEFORYU", "Service for You", [("int", "INT")]),
]

# ── Ensembles ─────────────────────────────────────────────────────────────────
# Level only (0=off); no caster-stat formula. Calculator deferred (pipeline TBD).
_ENSEMBLES: list[tuple[str, str, int]] = [
    ("SC_DRUMBATTLE", "Battle Theme",        5),
    ("SC_NIBELUNGEN", "Song of Nibelungen",  5),
    ("SC_SIEGFRIED",  "Lullaby of Woe",      5),
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

        # Storage for Party Buffs
        self._party_spins: dict[str, QSpinBox] = {}
        self._party_checks: dict[str, QCheckBox] = {}
        self._party_combos: dict[str, QComboBox] = {}  # SC_ADRENALINE only

        # Storage for Bard Songs
        self._bard_caster_spins: dict[str, QSpinBox] = {}   # "caster_agi", ..., "mus_lesson"
        self._song_level_spins: dict[str, QSpinBox] = {}    # SC_key → level spin (0=off)
        self._song_ov_checks: dict[str, dict[str, QCheckBox]] = {}  # SC_key → {stat → chk}
        self._song_ov_spins:  dict[str, dict[str, QSpinBox]]  = {}  # SC_key → {stat → spin}

        # Storage for Dancer Dances
        self._dancer_caster_spins: dict[str, QSpinBox] = {}  # "dancer_agi", ..., "dance_lesson"
        self._dance_level_spins: dict[str, QSpinBox] = {}
        self._dance_ov_checks: dict[str, dict[str, QCheckBox]] = {}
        self._dance_ov_spins:  dict[str, dict[str, QSpinBox]]  = {}

        # Storage for Ensembles
        self._ensemble_spins: dict[str, QSpinBox] = {}

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

        # ── 2. Party Buffs ────────────────────────────────────────────────
        self._sub_party = CollapsibleSubGroup("Party Buffs", default_collapsed=False)

        party_widget = QWidget()
        party_grid = QGridLayout(party_widget)
        party_grid.setContentsMargins(0, 0, 0, 0)
        party_grid.setHorizontalSpacing(6)
        party_grid.setVerticalSpacing(3)

        for row_i, (sc_key, display, wtype, min_lv, max_lv) in enumerate(_PARTY_BUFFS):
            lbl = QLabel(display)
            party_grid.addWidget(lbl, row_i, 0)

            if wtype == "spin":
                spin = QSpinBox()
                spin.setRange(min_lv, max_lv)
                spin.setValue(0)
                spin.setFixedWidth(52)
                spin.setSpecialValueText("Off")
                self._party_spins[sc_key] = spin
                spin.valueChanged.connect(self._on_changed)
                party_grid.addWidget(spin, row_i, 1)

            elif wtype == "check":
                chk = QCheckBox()
                self._party_checks[sc_key] = chk
                chk.toggled.connect(self._on_changed)
                party_grid.addWidget(chk, row_i, 1)

            elif wtype == "adrenaline":
                chk = QCheckBox()
                self._party_checks[sc_key] = chk
                combo = QComboBox()
                combo.addItem("Self")
                combo.addItem("Party member")
                combo.setEnabled(False)
                self._party_combos[sc_key] = combo
                chk.toggled.connect(combo.setEnabled)
                chk.toggled.connect(self._on_changed)
                combo.currentIndexChanged.connect(self._on_changed)
                party_grid.addWidget(chk, row_i, 1)
                party_grid.addWidget(combo, row_i, 2)

        self._sub_party.add_content_widget(party_widget)
        self.add_content_widget(self._sub_party)

        # ── 3. Ground Effects (stub) ──────────────────────────────────────
        self._sub_ground = CollapsibleSubGroup("Ground Effects", default_collapsed=False)
        self._sub_ground.add_content_widget(_stub_label("(Sage ground buffs — Session O)"))
        self.add_content_widget(self._sub_ground)

        # ── 4. Bard Songs ────────────────────────────────────────────────────
        self._sub_bard = CollapsibleSubGroup("Bard Songs", default_collapsed=True)
        self._sub_bard.add_content_widget(self._build_bard_widget())
        self.add_content_widget(self._sub_bard)

        # ── 5. Dancer Dances ─────────────────────────────────────────────────
        self._sub_dancer = CollapsibleSubGroup("Dancer Dances", default_collapsed=True)
        self._sub_dancer.add_content_widget(self._build_dancer_widget())
        self.add_content_widget(self._sub_dancer)

        # ── 6. Ensembles ─────────────────────────────────────────────────────
        self._sub_ensemble = CollapsibleSubGroup("Ensembles", default_collapsed=True)
        self._sub_ensemble.add_content_widget(self._build_ensemble_widget())
        self.add_content_widget(self._sub_ensemble)

        # ── 7. Guild Buffs (stub) ─────────────────────────────────────────
        self._sub_guild = CollapsibleSubGroup("Guild Buffs", default_collapsed=True)
        self._sub_guild.add_content_widget(_stub_label("(Guild skills — Session M)"))
        self.add_content_widget(self._sub_guild)

        # ── 8. Miscellaneous Effects (stub) ───────────────────────────────
        self._sub_misc = CollapsibleSubGroup("Miscellaneous Effects", default_collapsed=False)
        self._sub_misc.add_content_widget(_stub_label("(Item proc / pet buffs — future session)"))
        self.add_content_widget(self._sub_misc)

    # ── Song/Dance widget builders ─────────────────────────────────────────

    @staticmethod
    def _make_caster_row(grid: QGridLayout, row: int,
                         stats: list[tuple[str, str]], store: dict[str, QSpinBox],
                         lesson_key: str, lesson_label: str,
                         on_changed) -> None:
        """Build the shared caster-stats row for songs or dances."""
        col = 0
        for stat_key, lbl_text in stats:
            lbl = QLabel(lbl_text)
            lbl.setObjectName("passive_sub_header")
            grid.addWidget(lbl, row, col)
            spin = QSpinBox()
            spin.setRange(1, 255)
            spin.setValue(1)
            spin.setFixedWidth(52)
            store[stat_key] = spin
            spin.valueChanged.connect(on_changed)
            grid.addWidget(spin, row, col + 1)
            col += 2
        # Lesson spinbox
        lbl = QLabel(lesson_label)
        lbl.setObjectName("passive_sub_header")
        grid.addWidget(lbl, row, col)
        spin = QSpinBox()
        spin.setRange(0, 10)
        spin.setValue(0)
        spin.setFixedWidth(52)
        store[lesson_key] = spin
        spin.valueChanged.connect(on_changed)
        grid.addWidget(spin, row, col + 1)

    def _make_song_rows(self, grid: QGridLayout, start_row: int,
                        song_list: list[tuple[str, str, list[tuple[str, str]]]],
                        level_store: dict[str, QSpinBox],
                        ov_check_store: dict[str, dict[str, QCheckBox]],
                        ov_spin_store:  dict[str, dict[str, QSpinBox]]) -> None:
        """Build one row per song: level spin + per-stat override check+spin."""
        for r, (sc_key, display, overrides) in enumerate(song_list, start=start_row):
            lbl = QLabel(display)
            grid.addWidget(lbl, r, 0)

            lv_spin = QSpinBox()
            lv_spin.setRange(0, 10)
            lv_spin.setValue(0)
            lv_spin.setFixedWidth(52)
            lv_spin.setSpecialValueText("Off")
            level_store[sc_key] = lv_spin
            lv_spin.valueChanged.connect(self._on_changed)
            grid.addWidget(lv_spin, r, 1)

            ov_check_store[sc_key] = {}
            ov_spin_store[sc_key]  = {}
            col = 2
            for stat_key, stat_label in overrides:
                ov_lbl = QLabel(f"{stat_label}:")
                grid.addWidget(ov_lbl, r, col)
                ov_chk = QCheckBox("Ovr")
                ov_chk.setObjectName("passive_sc_check")
                ov_check_store[sc_key][stat_key] = ov_chk
                grid.addWidget(ov_chk, r, col + 1)
                ov_spin = QSpinBox()
                ov_spin.setRange(1, 255)
                ov_spin.setValue(1)
                ov_spin.setFixedWidth(52)
                ov_spin.setEnabled(False)
                ov_spin_store[sc_key][stat_key] = ov_spin
                ov_chk.toggled.connect(ov_spin.setEnabled)
                ov_chk.toggled.connect(self._on_changed)
                ov_spin.valueChanged.connect(self._on_changed)
                grid.addWidget(ov_spin, r, col + 2)
                col += 3

    def _build_bard_widget(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(3)
        self._make_caster_row(
            grid, 0,
            [("caster_agi", "AGI"), ("caster_vit", "VIT"), ("caster_dex", "DEX"),
             ("caster_int", "INT"), ("caster_luk", "LUK")],
            self._bard_caster_spins, "mus_lesson", "Mus.Lesson",
            self._on_changed,
        )
        self._make_song_rows(grid, 1, _BARD_SONGS,
                             self._song_level_spins,
                             self._song_ov_checks, self._song_ov_spins)
        return w

    def _build_dancer_widget(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(3)
        self._make_caster_row(
            grid, 0,
            [("dancer_agi", "AGI"), ("dancer_vit", "VIT"), ("dancer_dex", "DEX"),
             ("dancer_int", "INT"), ("dancer_luk", "LUK")],
            self._dancer_caster_spins, "dance_lesson", "Dance Lesson",
            self._on_changed,
        )
        self._make_song_rows(grid, 1, _DANCER_DANCES,
                             self._dance_level_spins,
                             self._dance_ov_checks, self._dance_ov_spins)
        return w

    def _build_ensemble_widget(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(3)
        note = QLabel("(WATK/resist effects pending — pipeline position TBD)")
        note.setObjectName("passive_sub_header")
        grid.addWidget(note, 0, 0, 1, 4)
        for r, (sc_key, display, max_lv) in enumerate(_ENSEMBLES, start=1):
            grid.addWidget(QLabel(display), r, 0)
            spin = QSpinBox()
            spin.setRange(0, max_lv)
            spin.setValue(0)
            spin.setFixedWidth(52)
            spin.setSpecialValueText("Off")
            self._ensemble_spins[sc_key] = spin
            spin.valueChanged.connect(self._on_changed)
            grid.addWidget(spin, r, 1)
        return w

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

        # Show Bard Songs only for Bard/Clown; Dancer Dances only for Dancer/Gypsy.
        self._sub_bard.setVisible(job_id in _BARD_JOBS)
        self._sub_dancer.setVisible(job_id in _DANCER_JOBS)

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
        # Block all signals while loading
        _all_widgets: list[QWidget] = (
            list(self._sc_checks.values()) +
            list(self._sc_spins.values()) +
            list(self._party_spins.values()) +
            list(self._party_checks.values()) +
            list(self._party_combos.values()) +
            list(self._bard_caster_spins.values()) +
            list(self._song_level_spins.values()) +
            list(self._dancer_caster_spins.values()) +
            list(self._dance_level_spins.values()) +
            list(self._ensemble_spins.values())
        )
        for ov_d in self._song_ov_checks.values():
            _all_widgets.extend(ov_d.values())
        for ov_d in self._song_ov_spins.values():
            _all_widgets.extend(ov_d.values())
        for ov_d in self._dance_ov_checks.values():
            _all_widgets.extend(ov_d.values())
        for ov_d in self._dance_ov_spins.values():
            _all_widgets.extend(ov_d.values())
        for w in _all_widgets:
            w.blockSignals(True)

        # Self buffs
        active = build.active_status_levels
        for sc_key, _, has_lv, min_lv, *_ in _SELF_BUFFS:
            chk = self._sc_checks[sc_key]
            is_active = sc_key in active
            chk.setChecked(is_active)
            if has_lv and sc_key in self._sc_spins:
                spin = self._sc_spins[sc_key]
                spin.setValue(active.get(sc_key, min_lv))
                spin.setEnabled(is_active)

        # Party buffs
        support = build.support_buffs
        for sc_key, _, wtype, *_ in _PARTY_BUFFS:
            if wtype == "spin":
                self._party_spins[sc_key].setValue(int(support.get(sc_key, 0)))
            elif wtype == "check":
                self._party_checks[sc_key].setChecked(bool(support.get(sc_key, False)))
            elif wtype == "adrenaline":
                val = int(support.get(sc_key, 0))
                chk = self._party_checks[sc_key]
                chk.setChecked(val != 0)
                combo = self._party_combos[sc_key]
                combo.setEnabled(val != 0)
                combo.setCurrentIndex(0 if val != 200 else 1)

        # Songs/dances
        ss = build.song_state
        self._load_song_group(ss, self._bard_caster_spins,
                              self._song_level_spins, self._song_ov_checks, self._song_ov_spins,
                              _BARD_SONGS)
        self._load_song_group(ss, self._dancer_caster_spins,
                              self._dance_level_spins, self._dance_ov_checks, self._dance_ov_spins,
                              _DANCER_DANCES)
        for sc_key, _, _ in _ENSEMBLES:
            self._ensemble_spins[sc_key].setValue(int(ss.get(sc_key, 0)))

        for w in _all_widgets:
            w.blockSignals(False)

        self._current_job_id = build.job_id
        self.update_job(build.job_id)

        if self._compact_summary_lbl is not None:
            self._compact_summary_lbl.setText(self._build_summary())

    def _load_song_group(self, ss: dict,
                         caster_store: dict[str, QSpinBox],
                         level_store:  dict[str, QSpinBox],
                         ov_chk_store: dict[str, dict[str, QCheckBox]],
                         ov_spin_store: dict[str, dict[str, QSpinBox]],
                         song_list: list) -> None:
        for stat_key, spin in caster_store.items():
            spin.setValue(int(ss.get(stat_key, 1)))
        for sc_key, _, overrides in song_list:
            level_store[sc_key].setValue(int(ss.get(sc_key, 0)))
            for stat_key, _ in overrides:
                ov_key = f"{sc_key}_{stat_key}"
                raw = ss.get(ov_key)  # None = use shared; int = override
                chk = ov_chk_store[sc_key][stat_key]
                spin = ov_spin_store[sc_key][stat_key]
                if raw is not None:
                    chk.setChecked(True)
                    spin.setValue(int(raw))
                    spin.setEnabled(True)
                else:
                    chk.setChecked(False)
                    spin.setEnabled(False)

    def collect_into(self, build: PlayerBuild) -> None:
        # Self buffs → active_status_levels
        active: dict[str, int] = build.active_status_levels.copy()
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

        # Party buffs → support_buffs
        support: dict[str, object] = build.support_buffs.copy()
        for sc_key, *_ in _PARTY_BUFFS:
            support.pop(sc_key, None)
        for sc_key, _, wtype, *_ in _PARTY_BUFFS:
            if wtype == "spin":
                val = self._party_spins[sc_key].value()
                if val > 0:
                    support[sc_key] = val
            elif wtype == "check":
                if self._party_checks[sc_key].isChecked():
                    support[sc_key] = 1
            elif wtype == "adrenaline":
                if self._party_checks[sc_key].isChecked():
                    idx = self._party_combos[sc_key].currentIndex()
                    support[sc_key] = _ADRENALINE_VALUES[idx]
        build.support_buffs = support

        # Songs/dances → song_state
        ss: dict[str, object] = {}
        self._collect_song_group(ss, self._bard_caster_spins,
                                 self._song_level_spins, self._song_ov_checks, self._song_ov_spins,
                                 _BARD_SONGS)
        self._collect_song_group(ss, self._dancer_caster_spins,
                                 self._dance_level_spins, self._dance_ov_checks, self._dance_ov_spins,
                                 _DANCER_DANCES)
        for sc_key, _, _ in _ENSEMBLES:
            ss[sc_key] = self._ensemble_spins[sc_key].value()
        build.song_state = ss

    def _collect_song_group(self, ss: dict,
                            caster_store: dict[str, QSpinBox],
                            level_store:  dict[str, QSpinBox],
                            ov_chk_store: dict[str, dict[str, QCheckBox]],
                            ov_spin_store: dict[str, dict[str, QSpinBox]],
                            song_list: list) -> None:
        for stat_key, spin in caster_store.items():
            ss[stat_key] = spin.value()
        for sc_key, _, overrides in song_list:
            ss[sc_key] = level_store[sc_key].value()
            for stat_key, _ in overrides:
                ov_key = f"{sc_key}_{stat_key}"
                chk = ov_chk_store[sc_key][stat_key]
                if chk.isChecked():
                    ss[ov_key] = ov_spin_store[sc_key][stat_key].value()
                else:
                    ss[ov_key] = None
