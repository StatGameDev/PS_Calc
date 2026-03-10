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

---

## Session N — Self-Buffs

**Goal**: Add all self-only SC rows to `_SELF_BUFFS` in `buffs_section.py` and implement
their formulas in `status_calculator.py` / `active_status_bonus.py`.

**Full skill tracking**: `docs/buff_temp_list.md` — every entry from buff_skills.md with
category/status/notes. Load this file at session start.

**Self-only SCs to add (22 new rows):**
7 SM_MAGNUM, 8 SM_ENDURE, 45 AC_CONCENTRATION, 135 AS_CLOAKING, 139 AS_POISONREACT,
146 SM_AUTOBERSERK, 155 MC_LOUD, 157 MG_ENERGYCOAT, 249 CR_AUTOGUARD,
252 CR_REFLECTSHIELD, 257 CR_DEFENDER, 261 MO_CALLSPIRITS, 268 MO_STEELBODY,
270 MO_EXPLOSIONSPIRITS, 411 TK_RUN, 500 GS_GLITTERING, 504 GS_MADNESSCANCEL,
505 GS_ADJUSTMENT, 506 GS_INCREASING, 517 GS_GATLINGFEVER, 543 NJ_NEN,
1005 RG_CLOSECONFINE

**Formulas confirmed from Hercules this session** (status.c):
- SC_GS_MADNESSCANCEL: batk += 100 (#ifndef RENEWAL, line 4479); ASPD skill1 bonus=20
- SC_GS_GATLINGFEVER: batk += 20+10×lv (#ifndef RENEWAL); flee −= 5×lv; ASPD rate += val1; init: val2=20×lv, val3=20+10×lv, val4=5×lv (line 8348)
- SC_GS_ADJUSTMENT: hit −= 30; flee += 30 (lines 4809, 4878)
- SC_GS_ACCURACY (GS_INCREASING): hit += 20 (line 4810)
- SC_RG_CCONFINE_M (RG_CLOSECONFINE): flee += 10 (line 4831)
- SC_EXPLOSIONSPIRITS: critical += val2 (line 4754)
- SC_NJ_NEN: str += val1; int_ += val1 (lines 3963, 4149)
- SC_PROVOKE init: val3=2+3×lv (atk%), val4=5+5×lv (def%) (line 8363)

**Still needs one grep at session start** (SC keys not found):
- SM_MAGNUM SC key, AC_CONCENTRATION SC key, MC_LOUD SC key, MO_CALLSPIRITS SC key,
  GS_GLITTERING SC key; also val definitions for SC_NJ_NEN and SC_EXPLOSIONSPIRITS

**Party buff corrections identified this session:**
- PR_SUFFRAGIUM (67): skipped in Session M — add to next party buff session
- CR_PROVIDENCE (256): party buff, future session
- SM_PROVOKE (6): debuff on enemies (Session R); SC_PROVOKE on player via SM_AUTOBERSERK only

**Architecture**: All new self SCs go into `active_status_levels` dict (existing).
StatusCalculator gains one new block after the ASPD section reading active_sc keys.
Stub rows (incoming-only: AutoGuard, ShieldReflect, Defender, MentalStrength, Cloaking,
PoisonReact, EnergyCoat, AutoBerserk) get UI rows but zero calculator effect.

**Estimated tokens**: 25–35k.

---

## Session O — Weapon Endow + Ground Effects

**Goal**: Properly document and integrate weapon endow + ground effect SCs.
**Skills**: Weapon endow: ID 68, 138, 280–283, 425 (buff_skills.md).
Ground effects: ID 285, 286, 287, 538 (buff_skills.md).
**Prep**: Fill weapon_endow.md + ground_effects.md stubs (skill.c + item_db.json).
**Weapon endow**: Already modelled via manual element override. Formalise SC→element
mapping; may improve existing override UI by naming the SC source.
**Ground effects**: SA_VOLCANO / SA_DELUGE / SA_VIOLENTGALE; AttrFix-adjacent.
Ground Effects sub-group in buffs_section already scaffolded (Session M).
**Estimated tokens**: 20–30k.

---

## Session P — Passive Skills Completion

**Goal**: Implement passive_skills.md entries not yet in StatusCalculator or mastery.
**Source**: pc.c → `pc_calcstatus`.
**Skills**: ~52 entries in passive_skills.md; subset already done (weapon masteries,
ASC_KATAR, ASPD passives). Remaining = weapon-type stat bonuses, conditional stat
passives, and any formula passives feeding StatusData.
**Architecture**: Extend StatusCalculator; introduce `passive_calculator.py` if volume
warrants a separate module.
**Gap ID**: G50
**Estimated tokens**: 30–40k.

---

## Session Q1 — Offensive Skill Ratios (Melee Classes)

**Goal**: Complete skill_ratio.py for melee-class offensive skills.
**Classes**: Swordsman, Crusader, Merchant, Blacksmith, Thief, Acolyte, Monk.
**Source**: skill.c → `calc_skillratio` BF_WEAPON path.
**Estimated tokens**: 35–45k.

---

## Session Q2 — Offensive Skill Ratios (Ranged / Magic Classes)

**Goal**: Complete skill_ratio.py for ranged and magic offensive skills.
**Classes**: Hunter, Wizard, Sage, Rogue, Bard/Dancer offensive skills, Ninja, Gunslinger.
**Source**: skill.c → `calc_skillratio` BF_WEAPON / BF_MAGIC paths.
**Estimated tokens**: 35–45k.

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
**Estimated tokens**: 30–40k (new architecture + UI).

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
