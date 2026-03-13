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
| O | Ground Effects: SC_VOLCANO (base_damage.py, lv * 10 WATK); SC_VIOLENTGALE (status_calculator.py, lv * 3 FLEE); SC_DELUGE (UI only, MaxHP no damage effect); Ground Effects sub-group wired (QComboBox+QSpinBox). Endows deferred (manual element override sufficient). | G49~ |
| GUI-Adj | Spinbox→dropdowns/toggles, no-wheel on all combos, refine cap +10 | — |
| P | Passive skills: hp/sp regen in StatusData+StatusCalculator+DerivedSection; 16 new passive_section rows; stat/HIT/FLEE/ASPD/regen passives in StatusCalculator; GearBonusAggregator.apply_passive_bonuses() (sub_ele/add_race/sub_race); NJ_TOBIDOUGU in mastery_fix.py. Deferred: G52 dual-wield, G53 falcon, G55 Shuriken type verify. | G50~ |
| G54 | Double-hit procs (TF_DOUBLE/GS_CHAINACTION) + DPS stat: AttackDefinition + SelectionStrategy (Markov seam); correct probability tree; katar combined; DPS row in SummarySection. New gaps G56 (skill timing) + G57 (Markov). | G54 |
| G52 | Dual-wield pipeline (complete): AS_RIGHT/AS_LEFT passives, LH forge fields+widgets, lh_normal/lh_crit, dual-wield branch, LH card EQP fix, perfect_dodge=0, proc×RH-only + ATK_RATER on double_hit branches, ASPD (RH+LH)×7/10. | G52 |
| Q0 | Skill timing calculator: calculate_skill_timing() (new file); GearBonuses castrate/delayrate/skill_castrate; bCastrate/bVarCastrate/bDelayrate routed; SC_SUFFRAGIUM party buff; amotion period for skills; BF_MAGIC DPS; dps_valid frozensets; Speed (actions/s) in SummarySection. | G56, G59, G60 |
| Q1 | 31 BF_WEAPON ratios in `_BF_WEAPON_RATIOS` + `_BF_WEAPON_HIT_COUNT_FN`. All level-linear skills + KN_PIERCE (hit_count=tgt.size+1, battle.c:4719-4722). IMPLEMENTED_BF_WEAPON_SKILLS=31. Deferred to Q3: AS_SPLASHER (+mastery), RG_BACKSTAP (bow split), BF_MISC traps/TF_THROWSTONE/BA_DISSONANCE. | G61 |
| GUI-Rework | `gui/widgets/` package: `NoWheelCombo`, `NoWheelSpin`, `LevelWidget`. 9 files swept. `combat_controls`: `_sync_level_widget` + `_on_skill_changed`. `passive_section`: `LevelWidget` for masteries. `buffs_section`: full overhaul — lesson combos extracted to `_bard_lesson`/`_dancer_lesson`, `isinstance` guard eliminated. | — |
| GUI-CompactRework2 | `compact_mode: str` → `compact_modes: list[str]`; two flags: `"slim_content"` (compact widget in slim, correct toggle) + `"header_summary"` (always-visible header label, auto-collapses). Base class owns all frame/state; subclass hooks only show/hide widget. passive + buffs → header_summary. New doc: `docs/compact_modes.md`. | — |
| Q2 | MO_FINGEROFFENSIVE/MO_INVESTIGATE/AM_ACIDTERROR ratios; DefenseFix NK_IGNORE_DEF + pdef=2 + def1=0. KN_CHARGEATK/MC_CARTREVOLUTION/MO_EXTREMITYFIST/TK_JUMPKICK ratios via skill_params; context-sensitive params UI row. IMPLEMENTED_BF_WEAPON_SKILLS=38. | G62 |
| GUI-BuffLvl | All has_lv=True self buffs → combo-only (label + LevelWidget, no checkbox). Bidirectional sphere sync: MO_SPIRITBALL ↔ MO_FINGEROFFENSIVE sphere dropdown via new spirit_spheres_changed signals + set_spirit_spheres() setters. Known bug G69 (MO_EXTREMITYFIST formula) flagged for Q3. | — |
| Q3 | G69 arch fix (SkillInstance hydrated before _run_branch; nk_ignore_def/flee/name fields; DefenseFix/MasteryFix take skill param). G55 mastery fix (NJ_TOBIDOUGU skill-based + NJ_KUNAI +60). 9 GS BF_WEAPON + 5 NJ BF_WEAPON (incl. NJ_SYURIKEN +4×lv flat) + 7 NJ BF_MAGIC ratios + BF_MISC infra. KN_PIERCE size crash fix. NJ BF_MAGIC roadmap table was wrong — corrected from source read. Charm bonuses deferred (G71). IMPLEMENTED_BF_WEAPON_SKILLS=55, BF_MAGIC=30. | G63, G55, G69 |

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

## Session S — Item Scripts Pass

**STUB**: This Session still needs to be planned out
Ensure all scripts work properly and begin implementing consumables.
The Hercules file detailing item scripts is "C:\Projects\PS_Calc\Hercules\doc\item_bonus.md"
That directory has a lot of useful documents in general

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
