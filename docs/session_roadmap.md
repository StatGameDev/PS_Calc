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

---

## Design Session — Buff Architecture ✅ DONE (2026-03-09)
_Decisions written to `docs/core_architecture.md` — "Buff Integration Design — Decisions"._

| Q | Decision |
|---|----------|
| Q1 | Extend StatusCalculator (Option A); WATK buffs → BaseDamage |
| Q2 | StatusCalculator reads build.song_state directly (Option A) |
| Q3 | Deferred — no concrete use case for M/M2 |
| Q4 | TargetStatusCalculator.apply_debuffs(target) → effective Target (Option B) |
| Q5 | Already resolved — two separate fields |

---

## Session M — Priest/Sage Party Buffs ✅ DONE (2026-03-10)

| Session | Primary work | Key gaps closed |
|---|---|---|
| M | Party Buffs: SC_BLESSING/INC_AGI/GLORIA/ANGELUS/IMPOSITIO/ADRENALINE; def_percent field; bonus display pipeline | G49~ |

---

## Session M2 — Bard/Dancer Songs

**Goal**: Implement confirmed Bard/Dancer song SCs in StatusCalculator + wire Bard Songs
and Dancer Dances sub-groups in buffs_section.
**Gap IDs**: G9~ (SC_ASSNCROS completion)
**Estimated tokens**: ~35–45k (new PlayerBuild.song_state field + multiple SC implementations)

**Prerequisite**: Session M (buffs_section + CollapsibleSubGroup must exist).

**All confirmed formulas are in `docs/buffs/songs_dances.md` — no Hercules research needed
for SC_ASSNCROS, SC_APPLEIDUN, DC_FORTUNEKISS, DC_SERVICEFORYOU, SC_POEMBRAGI.
BA_WHISTLE and DC_HUMMING still need a targeted grep before implementation.**

### Work items (in order):

1. **PlayerBuild.song_state** — new dict field (see data model in `docs/gui_plan.md`
   Bard Songs sub-group). Add save/load round-trip in BuildManager.
   Build save migration: move `SC_ASSNCROS` level from `active_status_levels` → `song_state`.

2. **Bard Songs + Dancer Dances sub-groups** — wire UI in `buffs_section.py`.
   Shared caster stat row + per-song checkbox/level/override rows.
   `update_job(job_id)` — Bard Songs hidden unless job is Bard/Clown;
   Dancer Dances hidden unless job is Dancer/Gypsy.

3. **SC_ASSNCROS — complete G9~**
   Formula: `val2 = (MusLesson_lv/2 + 10 + song_lv + caster_agi/10) * 10`
   Wire into `status_calculator.py` ASPD reduction block (already scaffolded).

4. **SC_APPLEIDUN** — MaxHP %: `val1 = 5 + 2*song_lv + caster_vit/10 + MusLesson_lv`
   Apply as `max_hp = max_hp * (100 + val1) // 100` in StatusCalculator.

5. **DC_FORTUNEKISS** — CRI: `val1 = (10 + song_lv + caster_luk/10 + DanceLesson_lv) * 10`
   Apply as flat cri bonus (note: 10× scale → divide by 10 when adding to cri).

6. **DC_SERVICEFORYOU** — MaxSP% + SP cost reduction:
   `val1 = 15 + song_lv + caster_int/10 + DanceLesson_lv/2` (MaxSP%)
   `val2 = 20 + 3*song_lv + caster_int/10 + DanceLesson_lv/2` (SP cost %)
   MaxSP: same pattern as APPLEIDUN. SP cost reduction: new `StatusData.sp_cost_reduction`
   field if needed.

7. **SC_POEMBRAGI** — cast time + after-cast delay reduction. New StatusData fields
   (`cast_time_reduction_pct`, `after_cast_delay_reduction_pct`) + derived_section rows.
   `val1 = 3*song_lv + caster_dex/10 + 2*MusLesson_lv` (cast time %)
   `val2 = (song_lv<10 ? 3*song_lv : 50) + caster_int/5 + 2*MusLesson_lv` (after-cast %)

8. **BA_WHISTLE + DC_HUMMING** — HIT/FLEE bonuses. Grep first, implement after.

---

## Session N — Self-Buffs

**Goal**: Self-cast active SCs from buff_skills.md not yet in the system.
**Skills (from buff_skills.md)**: ID 66, 67, 135, 139, 146, 249, 252, 256–258, 261, 268,
270, 309 (non-song entries), 411, 500, 504–506, 517, 543, 1005 and others.
**Architecture**: Extend `active_status_levels` dict + StatusCalculator branches.
ASPD SCs already done (Session C); focus on ATK/DEF/stat-modifying self-SCs.
Self-buff UI: job-filtered toggle list in `buffs_section` Self Buffs sub-group (already
scaffolded in Session M). Session N adds more rows and implements their SC formulas.
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
