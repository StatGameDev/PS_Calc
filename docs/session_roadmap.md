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

---

## Session Q2 — BF_WEAPON Special Mechanics + Remaining BF_MAGIC

**Status**: Partial. Session Q2-cont picks up remaining runtime-param skills.

**Completed this session**:
- `MO_FINGEROFFENSIVE`: ratio `100+50*lv` (battle.c:2191-2192); hit_count = `MO_CALLSPIRITS` level (proxy for `sd->spiritball_old`, battle.c:4698-4704)
- `MO_INVESTIGATE`: ratio `100+75*lv` (battle.c:2194-2195); pdef=2 DEF reversal handled in DefenseFix (`flag.pdef=flag.pdef2=2`, battle.c:4759; formula `dmg×2×(def1+vit_def)/100`, battle.c:1539)
- `AM_ACIDTERROR`: ratio `100+40*lv` (battle.c:2187-2189 `#else` pre-re); `def1` forced to 0 in DefenseFix (battle.c:1474 `#ifndef RENEWAL`) — only vit_def applies
- `DefenseFix` updated: NK_IGNORE_DEF bypass (separate note from crit, battle.c:4673); `skill_name` + `nk_flags` params added; all three special branches documented in docstring
- BF_MAGIC: all roadmap entries were already in `_BF_MAGIC_RATIOS` from prior sessions; nothing to add

**Key source facts confirmed this session** (do not re-read next session):
- `AM_ACIDTERROR` pre-re: `def1=0` at battle.c:1474 inside `battle_calc_defense`; the custom ATK+MATK block at battle.c:5424 is `#ifdef RENEWAL` only
- `MO_INVESTIGATE`: `flag.pdef=flag.pdef2=2` at battle.c:4759; pre-re formula `damage=damage*pdef*(def1+vit_def)/100` at battle.c:1539; vit_def NOT subtracted separately when `flag&2`
- `pdef=1` from `def_ratio_atk_ele/race` card bonuses (battle.c:5686/5694): sets flag via SD bonus, NOT flag-based idef. Formula `damage*1*(def1+vit_def)/100`. **Not yet implemented** — needs new `gear_bonuses` field + parser
- Flag interaction: card `sd->ignore_def` zeros def1 INSIDE calc_defense BEFORE formula; with pdef=2 this gives `2*(0+vit_def)/100` — damage becomes weak vs low-VIT targets (correct, matches in-game)
- `IMPLEMENTED_BF_WEAPON_SKILLS` now 34 (was 31)

**Remaining for Q2-cont (runtime-param skills — need `skill_params` on PlayerBuild + UI)**:

| Constant | Source confirmed | Formula | Input needed |
|---|---|---|---|
| `KN_CHARGEATK` | battle.c:2350-2359 | `+100*min((dist-1)//3,2)` → 100/200/300% | Distance dropdown (1–3 / 4–6 / 7+) |
| `MC_CARTREVOLUTION` | battle.c:2120-2127 | `+50 + 100*cart_weight/cart_weight_max` → 150–250% | Cart weight % spinbox |
| `MO_EXTREMITYFIST` | battle.c:2197-2206 `#ifndef RENEWAL` | `min(100+100*(8+sp/10),60000)` — **pre-re only** | Current SP spinbox |
| `TK_JUMPKICK` | battle.c:2290-2300 | `30+10*lv` base; `+10*lv/3` if SC_COMBOATTACK running; ×2 if SC_STRUP | Running toggle |

**Still deferred**:
- `CR_GRANDCROSS` — multi-target AoE + self-damage + undead/demon split, Q3+
- `AL_HEAL` / `PR_TURNUNDEAD` — entirely custom code paths, not ratio switch; Q3+
- `pdef=1` card bonuses — needs gear_bonuses field (add to gaps.md)

**Source for Q2-cont** (formulas already confirmed above — no re-read needed):
- `skill_params: dict[str, Any]` on PlayerBuild; GUI context-sensitive widget below skill selector

---

## Session Q3 — Ninja Hybrid + Gunslinger

**Goal**: Ninja (true BF_WEAPON + BF_MAGIC hybrid class) and Gunslinger (all-ranged BF_WEAPON
plus one BF_MAGIC outlier). Natural grouping: both are non-transcendent special classes,
both need Q1/Q2 infrastructure fully in place first.

**Ninja** (NJ_*):

| Constant | ID | Type | Notes |
|---|---|---|---|
| NJ_SYURIKEN | 523 | BF_WEAPON | thrown |
| NJ_KUNAI | 524 | BF_WEAPON | thrown |
| NJ_HUUMA | 525 | BF_WEAPON | thrown |
| NJ_KASUMIKIRI | 528 | BF_WEAPON | |
| NJ_KIRIKAGE | 530 | BF_WEAPON | |
| NJ_ZENYNAGE | 526 | BF_WEAPON | Zeny-based damage |
| NJ_ISSEN | 544 | BF_WEAPON | HP-based damage |
| NJ_KOUENKA | 534 | BF_MAGIC | fire |
| NJ_KAENSIN | 535 | BF_MAGIC | ground fire; advanced modelling |
| NJ_BAKUENRYU | 536 | BF_MAGIC | |
| NJ_HYOUSENSOU | 537 | BF_MAGIC | |
| NJ_HYOUSYOURAKU | 539 | BF_MAGIC | |
| NJ_RAIGEKISAI | 541 | BF_MAGIC | |
| NJ_KAMAITACHI | 542 | BF_MAGIC | |

**Gunslinger** (GS_*):

| Constant | ID | Type | Notes |
|---|---|---|---|
| GS_TRIPLEACTION | 502 | BF_WEAPON | |
| GS_BULLSEYE | 503 | BF_WEAPON | |
| GS_TRACKING | 512 | BF_WEAPON | |
| GS_PIERCINGSHOT | 514 | BF_WEAPON | |
| GS_RAPIDSHOWER | 515 | BF_WEAPON | |
| GS_DESPERADO | 516 | BF_WEAPON | |
| GS_DUST | 518 | BF_WEAPON | |
| GS_FULLBUSTER | 519 | BF_WEAPON | |
| GS_SPREADATTACK | 520 | BF_WEAPON | |
| GS_FLING | 501 | BF_WEAPON | DEF reduction + special damage |
| GS_MAGICALBULLET | 507 | BF_MAGIC | only BF_MAGIC gunslinger skill |

**Source**: skill.c `calc_skillratio` (NJ_* and GS_* cases).
**Estimated tokens**: 35–45k.

**Also in Q3 — BF_MISC skill filter wiring**: When implementing the deferred BF_MISC skills,
add `_BF_MISC_RATIOS: dict = {}` + `IMPLEMENTED_BF_MISC_SKILLS =
frozenset(_BF_MISC_RATIOS.keys())` to `skill_ratio.py`, then add `IMPLEMENTED_BF_MISC_SKILLS`
to `_IMPLEMENTED_SKILLS` in both `combat_controls.py` and `skill_browser.py`.

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
