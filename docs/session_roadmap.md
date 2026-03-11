# PS_Calc — Session Roadmap
_Gap IDs reference `docs/gaps.md`. Pipeline specs in `docs/pipeline_specs.md`._
_GUI layout and widget specs in `docs/gui_plan.md`._
_Core system architecture in `docs/core_architecture.md`._

---

## Context Budget Reference (from actual session data)

| Session type | Est. tokens | Typical ctx% |
|---|---|---|
| Pure GUI / no Hercules | 20–30k | 40–60% |
| Mixed implementation | 30–40k | 60–80% |
| Investigation-heavy | 40–50k | 80–100% |

**Planning rule**: If a session requires Hercules greps, budget 1–2 greps max alongside
implementation. Never plan investigation + large GUI change + doc maintenance together.
Hit-limit risk rises sharply past 3 Hercules reads in one session.

Fixed overhead per session (CLAUDE.md + system + conversation): ~6k tokens.
Doc maintenance (gaps.md + completed_work.md + context_log.md update): ~3–5k.

---

## Completed Sessions (reference only)

| Session | Primary work | Key gaps closed |
|---|---|---|
| 1–5 | Foundation, GUI Phases 0–4, data scrapers | B3–B9, C3, D1–D5, E1, F2, F5, F6 |
| A | Target model, CardFix | G1–G3, G5, G6, G8, G11 |
| B | BF_MAGIC outgoing pipeline | G18–G25 |
| C | ASC_KATAR mastery, ASPD buffs, bAtkRate | G4, G9~, G10, G42 |
| D | armor_element field, mob ATK investigation | G27 |
| E | Incoming physical + magic pipelines, player_build_to_target | G7, G26–G29, G31–G32 |
| F | Incoming config controls + unified target selector | G43, G30 |
| G | Card slot UI + armor refine DEF | G12, G13 |
| H | PMF foundation: pmf/ package + damage.py + base_damage.py | — |
| I | PMF migration: all 9 modifiers + 4 pipelines; DamageRange removed | — |
| J1 | Skill combo job filter + skill_tree.json scraper | G34 |
| J2 | Equipment browser / monster browser / passives job filters | G35, G36, G37 |
| K | Katar second hit + forged weapon bonus | G16, G17 |
| K2 | ActiveItems + ManualAdj sections + bonus column redesign + skill_data bugfix | G15, G46, G47 |
| L | StepsBar tooltips + state persistence + inline dropdown + job ID system fix | G39, G40, G45 |
| M0 | Buff/Debuff UI scaffolding: CollapsibleSubGroup widget, buffs_section (8 sub-groups, Self Buffs wired), player_debuffs_section, Manual Adj into build_header, passive_section strip | G49~ |
| Design | Buff Architecture Q1–Q5 resolved; decisions written to core_architecture.md | — |
| M | Party Buffs: SC_BLESSING/INC_AGI/GLORIA/ANGELUS/IMPOSITIO/ADRENALINE; def_percent chain; bonus display "Buffs" column | G49~ |
| M2 | Bard/Dancer songs: song_state on PlayerBuild; SC_ASSNCROS/WHISTLE/APPLEIDUN/POEMBRAGI/HUMMING/FORTUNE/SERVICEFORYU in StatusCalculator; SC_DRUMBATTLE+SC_NIBELUNGEN in base_damage.py; Bard Songs+Dancer Dances+Ensembles UI; job visibility filter | G9, G49~ |
| N | Self-Buffs: 10 SCs in StatusCalculator (stat/BATK/CRI/HIT/FLEE/ASPD/MDEF); 3 ASPD bugs fixed (MADNESSCANCEL not in max pool, STEELBODY/DEFENDER scale corrected); 22 new _SELF_BUFFS rows in buffs_section.py | G49~ |
| O | Ground Effects: SC_VOLCANO (base_damage.py, lv*10 WATK); SC_VIOLENTGALE (status_calculator.py, lv*3 FLEE); SC_DELUGE (UI only, MaxHP no damage effect); Ground Effects sub-group wired (QComboBox+QSpinBox). Endows deferred (manual element override sufficient). | G49~ |
| GUI-Adj | Spinbox→dropdowns/toggles, no-wheel on all combos, refine cap +10 | — |
| P | Passive skills: hp/sp regen in StatusData+StatusCalculator+DerivedSection; 16 new passive_section rows; stat/HIT/FLEE/ASPD/regen passives in StatusCalculator; GearBonusAggregator.apply_passive_bonuses() (sub_ele/add_race/sub_race); NJ_TOBIDOUGU in mastery_fix.py. Deferred: G52 dual-wield, G53 falcon, G55 Shuriken type verify. | G50~ |
| G54 | Double-hit procs (TF_DOUBLE/GS_CHAINACTION) + DPS stat: AttackDefinition + SelectionStrategy (Markov seam); correct probability tree; katar combined; DPS row in SummarySection. New gaps G56 (skill timing) + G57 (Markov). | G54 |
| G52 | Dual-wield pipeline (partial): AS_RIGHT/AS_LEFT passives, LH forge fields+widgets, lh_normal/lh_crit on BattleResult, dual-wield branch in BattlePipeline, LH card browser EQP fix, monster perfect_dodge=0. Remaining: proc interaction with dual-wield (needs source read). | G52 |

---

## Session Q1 — Offensive Skill Ratios (Melee Classes)

**Goal**: Complete skill_ratio.py for melee-class offensive skills.
**Classes**: Swordsman, Crusader, Merchant, Blacksmith, Thief, Acolyte, Monk.
**Source**: skill.c → `calc_skillratio` BF_WEAPON path.
**Estimated tokens**: 35–45k.
**Note**: DPS row will show auto-attack DPS for skill selections until G56 (skill timing
data) is implemented. Consider hiding DPS row when skill_id != 0 as part of this session.

---

## Session Q2 — Offensive Skill Ratios (Ranged / Magic Classes)

**Goal**: Complete skill_ratio.py for ranged and magic offensive skills.
**Classes**: Hunter, Wizard, Sage, Rogue, Bard/Dancer offensive skills, Ninja, Gunslinger.
**Source**: skill.c → `calc_skillratio` BF_WEAPON / BF_MAGIC paths.
**Estimated tokens**: 35–45k.

---

## Session G52-cont — Dual-Wield: Double-Attack Procs (remaining)

**Gap ID**: G52 [~] — partial. Core dual-wield pipeline done. Proc interaction not yet implemented.

### Confirmed Hercules facts (read in Session G52)
- LH base damage: separate `calc_base_damage2(sstatus, &sstatus->lhw, ...)` call (battle.c:5304)
- RH rate: `wd.damage * (50 + AS_RIGHT_lv*10) / 100` (battle.c:5923-5926, ATK_RATER)
- LH rate: `wd.damage2 * (30 + AS_LEFT_lv*10) / 100` (battle.c:5929-5932, ATK_RATEL)
- Pre-renewal floor 1 for both (battle.c:5937-5938, #else branch)
- LH element independent: `s_ele_ = sstatus->lhw.ele` (battle.c:4811)
- Dual-wield is normal attack only; skills always use RH (battle.c:4855-4859)

### Remaining work — read source BEFORE writing any code

Read battle.c around TF_DOUBLE proc block (~4920-4930) and the dual-wield + proc region:
- Does `flag.lh` affect TF_DOUBLE eligibility?
- Is the proc triggered on RH swing only, or can LH also trigger it?
- Does `wd.damage2` (LH) get multiplied by proc_hit_count, or is LH excluded from proc?
- Does the dual-wield rate (ATK_RATER/ATK_RATEL) also apply to the proc branch?

Only implement after reading those source lines.

---

## Session R — Target Debuff System

**Goal**: Allow debuffs from debuff_skills.md to be applied to the target before the
damage pipeline runs, so they modify the target's effective stats.
**Gap ID**: G48.
**Architecture**: New `target_active_scs: dict[str, int]` on Target dataclass.
`player_active_scs` already stubbed on PlayerBuild (Session M0 prereq). DefenseFix /
a new `target_status_calculator.py` reads these SCs and adjusts target DEF, FLEE, element.
**GUI**: Wire `target_state_section` Applied Debuffs + Monster State sub-groups with actual
debuff toggles (SC_PROVOKE, SC_DECREASEAGI, PR_LEXAETERNA, etc.).
Wire `player_debuffs_section` (already scaffolded in M0) with actual debuff toggles
(SC_ETERNALCHAOS, SC_CURSE, SC_BLIND, SC_DECREASEAGI).
Toggles per debuff (PROVOKE, AGIDISCOUNT, etc.) + level spinbox.
Readback regarding player/target differences in implementation (ideally re-use system for both)
**Estimated tokens**: 30–40k (new architecture + UI).

---

## Session GUI-Rework — Widget Architecture Cleanup

**Goal**: Replace all level-selector widgets with a shared `LevelWidget` class;
consolidate the 9 duplicate `_NoWheelCombo`/`_NoWheelSpin` local definitions into
`gui/widgets/`; fix the `isinstance` guard in `_load_song_group` introduced by the
lesson combo living in the caster-spins dict.

**Motivation**: The GUI-Adj session converted all spinboxes to dropdowns but left each
file with its own copy of `_NoWheelCombo` and a bespoke `_make_level_combo` helper.
Future widget-type changes still require touching every call site.

**Work items** (see `docs/gui_plan.md` → LevelWidget Refactor for full spec):
1. Create `gui/widgets/level_widget.py` — `LevelWidget(QComboBox)` with `value()`,
   `setValue()`, `valueChanged` matching QSpinBox API.
2. Export `LevelWidget`, `NoWheelCombo`, `NoWheelSpin` from `gui/widgets/__init__.py`;
   remove the 9 local `_NoWheelCombo`/`_NoWheelSpin` class definitions.
3. Update `passive_section.py` and `buffs_section.py` to use `LevelWidget`; remove
   `_make_level_combo()` helper.
4. Move `mus_lesson` / `dance_lesson` out of `_bard_caster_spins` / `_dancer_caster_spins`
   into dedicated `_bard_lesson: LevelWidget` / `_dancer_lesson: LevelWidget` attributes
   (eliminates the `isinstance` guard in `_load_song_group`).

**Estimated tokens**: ~20–25k (pure GUI, no Hercules reads).

---

## Deferred (Phase 5+ / Advanced Combat Modelling)

| Item | Reason deferred |
|---|---|
| **G41 — PC VIT DEF discrepancy** | LOW PRIORITY. Hercules comment vs C code disagree. Investigate vs official server data before any fix. Currently following C implementation. |
| **Status ailments** (status_skills.md) | Need turn-sequence / hit-count modelling. Phase 5+. |
| **Combo system** (combo_skills.md) | Requires turn-sequence and stance-state modelling. |
| **Healing calculator** (healing_skill.md) | Separate feature mode; 4 skills. |
| **Rebirth / Star Gladiator / Soul Linker** | Not yet in skill_lists; to be added in a future extension session. |
| **Phases 5–8** | Stat Planner, Comparison, Histogram, Config/Scale tabs. |
