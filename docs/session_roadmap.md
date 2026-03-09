# PS_Calc — Session Roadmap
_Gap IDs reference docs/gaps.md. Pipeline specs in docs/pipeline_specs.md._

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

---

## Session J — Party buffs

**Goal**: Implement confirmed Bard/Dancer song SCs in StatusCalculator + new Party Buffs UI panel.
**Gap IDs**: G9~ (SC_ASSNCROS), new items for SC_POEMBRAGI, SC_APPLEIDUN, DC_FORTUNEKISS, DC_SERVICEFORYOU and other Songs
**Estimated tokens**: ~35–45k (new UI sub-section + multiple formula implementations + possible new StatusData fields)

**All confirmed formulas are in `docs/BARD_DANCER_SONGS.md` — no Hercules research needed for these six.**
BA_WHISTLE and DC_HUMMING still need a targeted grep before implementation.

### Design decision (discuss with user before coding):

Add a "Party Buffs" collapsible sub-group to `passive_section.py` (placeholder already exists).
The sub-group needs a "song caster" input panel: AGI, DEX, VIT, INT, LUK spinboxes + song level
per active song + BA_MUSICALLESSON / DC_DANCINGLESSON passive levels.

Alternatively: expose SCs as toggles with manual val2 sliders (simpler; avoids caster stat inputs).
Tradeoff: caster stat inputs are accurate and educational; manual sliders are faster to implement.

### Work items (in order):

1. **Party Buffs UI panel** — add caster stat inputs + per-song enable/level controls to `passive_section.py`

2. **SC_ASSNCROS — complete G9~**
   Formula (from BARD_DANCER_SONGS.md): `val2 = (MusLesson_lv/2 + 10 + song_lv + caster_agi/10) * 10`
   Wire into `status_calculator.py` ASPD reduction block (already scaffolded; currently does nothing).

3. **SC_APPLEIDUN** — MaxHP %: `val1 = 5 + 2*song_lv + caster_vit/10 + MusLesson_lv`
   Apply as `max_hp = max_hp * (100 + val1) // 100` in StatusCalculator.

4. **DC_FORTUNEKISS** — CRI: `val1 = (10 + song_lv + caster_luk/10 + DanceLesson_lv) * 10`
   Apply as flat cri bonus (note: 10× scale → divide by 10 when adding to cri).

5. **DC_SERVICEFORYOU** — MaxSP% + SP cost reduction:
   `val1 = 15 + song_lv + caster_int/10 + DanceLesson_lv/2` (MaxSP%)
   `val2 = 20 + 3*song_lv + caster_int/10 + DanceLesson_lv/2` (SP cost %)
   MaxSP: same pattern as APPLEIDUN. SP cost reduction: new `status.sp_cost_reduction` field if needed.

6. **SC_POEMBRAGI** — cast time + after-cast delay reduction. Requires new StatusData fields
   (`cast_time_reduction_pct`, `after_cast_delay_reduction_pct`) and display rows in derived_section.
   `val1 = 3*song_lv + caster_dex/10 + 2*MusLesson_lv` (cast time %)
   `val2 = (song_lv<10 ? 3*song_lv : 50) + caster_int/5 + 2*MusLesson_lv` (after-cast %)

7. **BA_WHISTLE + DC_HUMMING** — HIT/FLEE/HIT bonuses. Grep first, implement after.

---

---

## Planned Sessions (Post-J)

> Skill coverage reference: `docs/skill_lists/`. Each session's prep step = fill relevant
> docs/buffs/ stubs via targeted Hercules greps (1 per skill, at session start).

---

### Session M — Party Support Buffs

**Goal**: Implement party-cast stat-modifying SCs (Priest/Sage group) in StatusCalculator.
**Source file**: skill.c → `skill_castend_nodamage_id`; status.c for SC val formulas.
**Skills (from buff_skills.md)**: ID 29, 33, 34, 45, 60, 74, 75, 111–114, 155, 157 and
related (SC_BLESSING, SC_INCREASEAGI, SC_DECREASEAGI, SC_GLORIA, SC_MAGNIFICAT,
SC_IMPOSITIOMANUS, SC_ANGELUS, PR_LEXAETERNA, etc.)
**Architecture**: Extend Party Buffs UI from Session J. Add SCs to StatusCalculator
(STR/DEX/INT/AGI/VIT/LUK flat and % modifiers). New `sp_regen_rate` StatusData field
if SC_MAGNIFICAT is in scope.
**stat_foods.md**: SC_FOOD_* / SC_INC* remain in G46 Active Items (already implemented).
Revisit only if SC cap enforcement across food+skill is needed.
**UI section**: "Party — Priest / Acolyte" sub-group inside Buffs section (see UI design below).
**Estimated tokens**: 30–40k.

---

### Session N — Self-Buffs

**Goal**: Self-cast active SCs from buff_skills.md not yet in the system.
**Skills (from buff_skills.md)**: ID 66, 67, 135, 139, 146, 249, 252, 256–258, 261, 268,
270, 309 (non-song entries), 411, 500, 504–506, 517, 543, 1005 and others.
**Architecture**: Extend `active_status_levels` dict + StatusCalculator branches.
ASPD SCs already done (Session C); focus on ATK/DEF/stat-modifying self-SCs.
Self-buff UI: job-filtered toggle list (same pattern as Passives section).
**UI section**: "Self Buffs" sub-group inside Buffs section (see UI design below).
**Estimated tokens**: 25–35k.

---

### Session O — Weapon Endow + Ground Effects

**Goal**: Properly document and integrate weapon endow + ground effect SCs.
**Skills**: Weapon endow: ID 68, 138, 280–283, 425 (buff_skills.md).
Ground effects: ID 285, 286, 287, 538 (buff_skills.md).
**Prep**: Fill weapon_endow.md + ground_effects.md stubs (skill.c + item_db.json).
**Weapon endow**: Already modelled via manual element override. Formalise SC→element
mapping; may improve existing override UI by naming the SC source.
**Ground effects**: SA_VOLCANO / SA_DELUGE / SA_VIOLENTGALE; AttrFix-adjacent.
**Estimated tokens**: 20–30k.

---

### Session P — Passive Skills Completion

**Goal**: Implement passive_skills.md entries not yet in StatusCalculator or mastery.
**Source**: pc.c → `pc_calcstatus`.
**Skills**: ~52 entries in passive_skills.md; subset already done (weapon masteries,
ASC_KATAR, ASPD passives). Remaining = weapon-type stat bonuses, conditional stat
passives, and any formula passives feeding StatusData.
**Architecture**: Extend StatusCalculator; introduce `passive_calculator.py` if volume
warrants a separate module.
**Estimated tokens**: 30–40k.

---

### Session Q1 — Offensive Skill Ratios (Melee Classes)

**Goal**: Complete skill_ratio.py for melee-class offensive skills.
**Classes**: Swordsman, Crusader, Merchant, Blacksmith, Thief, Acolyte, Monk.
**Source**: skill.c → `calc_skillratio` BF_WEAPON path.
**Estimated tokens**: 35–45k.

---

### Session Q2 — Offensive Skill Ratios (Ranged / Magic Classes)

**Goal**: Complete skill_ratio.py for ranged and magic offensive skills.
**Classes**: Hunter, Wizard, Sage, Rogue, Bard/Dancer offensive skills, Ninja, Gunslinger.
**Source**: skill.c → `calc_skillratio` BF_WEAPON / BF_MAGIC paths.
**Estimated tokens**: 35–45k.

---

### Session R — Target Debuff System

**Goal**: Allow debuffs from debuff_skills.md to be applied to the target before the
damage pipeline runs, so they modify the target's effective stats.
**Gap ID**: G48.
**Architecture**: New `target_active_scs: dict[str, int]` on Target dataclass
(mirrors `active_status_levels` on PlayerBuild). DefenseFix / a new
`target_status_calculator.py` reads these SCs and adjusts target DEF, FLEE, element.
**GUI**: "Target State" collapsible section near the target selector panel.
Toggles per debuff (PROVOKE, AGIDISCOUNT, etc.) + level spinbox.
**Estimated tokens**: 30–40k (new architecture + UI).

---

## UI Grouping Design (Buffs Section)

Principle: group by **scenario role** (who provides the buff), not by mechanical effect.
Users think "I have Blessing + Gloria + Bragi," not "I have a LUK+30 and a DEX% effect."

**Player-side — Buffs collapsible section (builder/passive panel):**

```
Buffs
├── Self Buffs          job-filtered; toggle + level per SC (same pattern as Passives)
├── Party — Priest / Acolyte    SC_BLESSING, SC_GLORIA, SC_INCREASEAGI, SC_ANGELUS, …
├── Party — Sage / Scholar      (SCs TBD after Session M Hercules lookups)
├── Party — Bard (songs)        ← Session J
└── Party — Dancer (dances)     ← Session J
```

**Target-side — Target State collapsible section (combat panel, near target selector):**

```
Target State
├── Debuffs on target   SC_PROVOKE, etc. (Session R)
└── Target Ailments     Freeze / Stone / Stun — deferred (advanced combat modelling)
```

**Consumables**: SC_FOOD_* / SC_INC* stay in G46 Active Items (already live). No migration
unless SC-cap enforcement across food + skill sources becomes necessary.

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