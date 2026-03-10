# PS_Calc — Claude Code Instructions

## IDs Over Name Strings

Always use integer IDs instead of name strings for internal data:
- Job filtering: `job_id in item["job"]` — `item["job"]` is `list[int]` (scraper converts Hercules names to IDs)
- Skill lookup: use skill name keys (e.g. `"KN_ONEHAND"`) only as they appear in skill_tree.json
- Never map job_id → display name → compare string; always compare IDs directly
- When adding new data fields that reference jobs/elements/races, store as int, not string

---

## Ask First, Search Later

If a task requires locating files, external data, or unfamiliar formats — ask the
user first. One targeted grep or read is fine. Exploratory multi-file searches are
not. Stop and ask after one failed attempt.

## Source Verification — Hard Rule

**No implementation without reading the exact source line in the current session.**

Prior session notes, memory files, and roadmap entries are planning aids, not
verified source. Before writing any formula or value into code:

1. Grep or read the specific Hercules source line that justifies it — this session.
2. If the line was not read this session, read it now before writing the code.
3. Never derive a formula by reasoning about code you haven't read. If the
   implementation requires understanding a function's full logic (e.g. how a
   variable maps to an output), read that function — do not infer it.

**Save confirmed facts with file + line number so the next session can skip the grep:**

When a formula, val definition, or SC behaviour is confirmed from source, record it
in `docs/session_roadmap.md` (or the relevant planning doc) as:
`SC_FOO: effect description (file.c:line_number)`

This avoids re-reading the same lines every session while still requiring that
every implementation is backed by a line number that was actually read.

**Do not report partial evidence as full confirmation.**
"I found a line that mentions this SC" is not the same as "I read the formula."
If you have not read the formula line, say so explicitly before implementing.

**Implement every confirmed effect — no silent omissions.**
If a Hercules source line confirms an effect exists (even if it does not directly
affect the damage pipeline), it must be implemented or explicitly flagged to the
user for a decision. Do not unilaterally decide an effect is "not important enough"
and skip it without telling the user. This applies to any stat tracked in StatusData
(MaxHP, FLEE, ASPD, etc.) and to any pipeline step, regardless of whether that stat
feeds the outgoing damage number.

---

## Cost Controls — Hard Limits

These caps are non-negotiable. Exceeding them wastes context with no benefit.

**Static bug investigation: 3-file cap.**
If the root cause of a bug is not found after reading 3 files, STOP.
Add a debug print at the most likely site and ask the user to run the app and
report the output. Do not read more files trying to reason it out.

**Repeating the same trace: immediate stop.**
If you catch yourself re-reading a file you already read, or re-checking logic
you already verified, stop immediately. You are in a loop. Add the debug print
and ask for runtime cooperation.

**Unexpected task scope: declare and ask.**
If a task turns out to require more than ~5 file reads or edits beyond what was
agreed in the session plan, stop and say "this is larger than expected — here
is what I've found so far, do you want me to continue or adjust scope?"
Never silently expand the work.

---

## Project Overview

Pre-renewal Ragnarok Online damage calculator in Python/PySide6.
Hercules emulator cloned at ./Hercules/ — all formulas must be traceable to source.
Competitive target: rocalc.com. Key differentiator: transparent damage pipeline with
step-by-step breakdown, formula display, and Hercules source citation.

---

## Development Stage

**Pre-alpha. No users yet.** Correctness and clean architecture take priority over keeping
the app usable short-term. Do not compromise on architecture to avoid touching working code.

---

## Non-Negotiable Rules

- Pre-renewal only.
- Hercules is the source of truth. One targeted grep before asking. No wikis.
- Every DamageStep must cite its source. hercules_ref = exact file + function.
- Python 3.13. No deprecated APIs.
- GUI: PySide6 + QSS (dark.qss). No CustomTkinter. No raw Tkinter. No matplotlib.
- `status.int_` not `status.int` everywhere.

### Renewal vs Pre-Renewal Guards — CRITICAL

- `#ifdef RENEWAL` — ignore entirely.
- `#ifndef RENEWAL` — pre-renewal only, implement this.
- No guard — applies to both.

Always check guards before implementing:

    sed -n 'START,ENDp' Hercules/src/map/battle.c | grep -n "RENEWAL"

Known renewal-only mechanics (must NOT appear in pre-renewal code):
LUK→HIT, LUK→FLEE, SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2.

Note: SC_IMPOSITIO is PRE-RENEWAL (#ifndef RENEWAL in status.c ~line 4562).
It adds `val2` (level×5) flat to watk. Implemented in base_damage.py (Session A).

---

## Hercules Source

`./Hercules/src/map/` — battle.c, status.c, skill.c, pc.c

    grep -n "function_name" Hercules/src/map/battle.c
    sed -n 'START,ENDp' Hercules/src/map/battle.c

Always grep first. Never load entire files.

---

## Project File Structure

### Core calculator files (`core/calculators/`)

    core/calculators/battle_pipeline.py        — BattlePipeline orchestrator (routes Magic → MagicPipeline)
    core/calculators/magic_pipeline.py         — MagicPipeline: BF_MAGIC outgoing (Session B)
    core/calculators/status_calculator.py      — StatusCalculator (HIT, FLEE, BATK, CRI, DEF, MATK, MDEF)
    core/calculators/modifiers/
        base_damage.py       — weapon ATK range, SizeFix, overrefine (battle_calc_base_damage2)
        skill_ratio.py       — SkillRatio (battle_calc_skillratio); calculate_magic() for BF_MAGIC
        defense_fix.py       — DefenseFix: hard DEF % + VIT DEF rnd range; calculate_magic() for MDEF
        crit_atk_rate.py     — CritAtkRate (pre-defense crit bonus)
        active_status_bonus.py — SC_AURABLADE etc. (post-defense)
        refine_fix.py        — RefineFix: deterministic atk2 (post-defense)
        mastery_fix.py       — MasteryFix (battle_calc_masteryfix, #ifndef RENEWAL)
        attr_fix.py          — AttrFix: elemental multiplier table
        forge_bonus.py       — ForgeBonus: Star crumb bonus (G17, inserted between AttrFix and CardFix)
        card_fix.py          — CardFix: race/ele/size/long_atk bonuses + PvP target resist (Session A)
        final_rate_bonus.py  — FinalRateBonus: short/long damage rates
        crit_chance.py       — calculate_crit_chance, CRIT_ELIGIBLE_SKILLS
        hit_chance.py        — calculate_hit_chance (E1, Session 2/3)

### Core models (`core/models/`)

    build.py    — PlayerBuild dataclass
    weapon.py   — Weapon dataclass, RANGED_WEAPON_TYPES
    target.py   — Target dataclass (mirror of tstatus for damage calc)
    status.py   — StatusData dataclass (output of StatusCalculator)
    damage.py   — DamageRange, DamageStep, DamageResult, BattleResult
    skill.py    — SkillInstance

### Data files (`core/data/pre-re/`)

    db/item_db.json    — 2760 items (IT_WEAPON, IT_ARMOR, IT_CARD, IT_AMMO)
    db/mob_db.json     — 1007 mobs
    db/skills.json     — 1168 skills
    tables/            — size_fix, attr_fix, refine_weapon, refine_armor, mastery_fix, active_status_bonus

### Planning docs (`docs/`)

    gaps.md               — all open gaps: ID, status, Hercules ref, one-line description
    session_roadmap.md    — session work items in order, context budget reference
    pipeline_specs.md     — full pipeline step specs for BF_WEAPON, BF_MAGIC, incoming
    core_architecture.md  — module map, data flow, buff integration design (open questions)
    data_models.md        — Target/StatusData/GearBonuses/PlayerBuild field specs (current vs needed)
    context_log.md        — historical context % used per session; used to calibrate future scope
    completed_work.md     — full history of completed work (Sessions 1–A); append each session
    gui_plan.md           — GUI section layout (current + planned), widget specs, Phases 5–8, Buffs UI design
    phases_done.md        — GUI phase specs archive (Phases 0–4)
    buffs/               — Party buff reference docs (one file per category; see buffs/README.md)
        songs_dances.md  — All BA_*/DC_*/BD_* SCs: confirmed formulas, val mapping, status
        support_buffs.md — Priest/Knight/etc party-cast buffs (SC_BLESSING, SC_GLORIA, etc.)
        weapon_endow.md  — Weapon element endow (SA_*, PR_ASPERSIO, AS_*, TK_*)
        stat_foods.md    — Consumable stat buffs (SC_FOOD_*, SC_INC*)
        ground_effects.md — Ground/zone AoE buff effects (SA_VOLCANO, etc.)

    Load these on demand — do NOT load all at session start.
    Always load gaps.md + session_roadmap.md when planning or scoping a session.
    Load context_log.md when estimating whether a planned session fits in one context window.

### Lookup tables (`docs/lookup/`)

    README.md          — column specs, usage examples, regeneration instructions
    skill_ref.tsv      — 1168 skills: id · constant · description · category · notes
    item_ref.tsv       — 2760 items:  id · aegis_name · name · type · script · on_equip · on_unequip · notes
    mob_ref.tsv        — 1007 mobs:   id · sprite_name · name · notes
    job_ref.tsv        — 36 jobs:     id · name · notes
    job_skill_map.tsv  — job_id → skill_id mappings (one row per pair, includes inherited skills)

    Use these for all ID↔name lookups instead of grepping the raw JSON databases.
    skill_ref.tsv also carries category codes (B/P/O/D/S/H/C/M/X) and planning notes
    from docs/skill_lists/skills_by_job.md for all categorised skills.
    Regenerate after any DB rescrape — see docs/lookup/README.md for instructions.

### GUI (`gui/`)

    main_window.py          — QMainWindow, signal routing, pipeline triggers
    panel_container.py      — PanelContainer(QSplitter), focus states, snap
    panel.py                — Panel(QWidget), StepsBar
    section.py              — Section base class, compact_mode protocol
    sections/               — one file per section key (see layout_config.json)
    dialogs/                — EquipmentBrowserDialog, SkillBrowserDialog, etc.
    themes/dark.qss         — all styling (no inline styles anywhere)
    layout_config.json      — section registry: key, panel, compact_mode

---

## Bug Investigation Protocol

When a runtime bug cannot be found through static analysis (e.g. a value
shows as 0 in the GUI despite code tracing showing it should be non-zero):

1. Add a targeted `print(..., file=sys.stderr)` at the suspect site.
2. **Ask the user to run the app and reproduce the issue**, then report
   the printed output back verbatim.
3. Only hypothesise fixes after seeing actual runtime values.

Do not spend more than one read-through attempting to find a pure
static-analysis explanation. Ask the user for runtime cooperation.

---

## Coding Conventions

- Modifiers: `@staticmethod def calculate(...)` — no instantiation.
- `result.add_step(...)` for every calculation — never silently mutate.
- All magic numbers cite Hercules source in comments.
- No global state outside loader; no sudo.
- No inline style strings — all styling via dark.qss.
- No business logic in widget classes — widgets emit signals, core handles
  calculation, results pushed back via signals.

> See `docs/data_models.md` for data model field specs (PlayerBuild, BattleResult, Target, etc.)

---

## Pipeline Step Order

**BF_WEAPON** (BattlePipeline → `_run_branch`):

    BaseDamage → SkillRatio → CritAtkRate (crit only) → DefenseFix (skip on crit) →
    ActiveStatusBonus → RefineFix → MasteryFix → AttrFix → ForgeBonus → CardFix → FinalRateBonus

**BF_MAGIC** (BattlePipeline routes to MagicPipeline when `attack_type == "Magic"`):

    MATK roll → SkillRatio(magic, per-hit) → DefenseFix(magic, per-hit) →
    AttrFix(magic, per-hit) → HitCount×N → CardFix(magic, target-side only) → FinalRateBonus

    Source: battle.c:3828 battle_calc_magic_attack (#else not RENEWAL)
    Result stored in BattleResult.magic; mirrored to .normal for GUI display.

---

## Session Planning

> Current gaps, session scope, and work items are tracked in `docs/`.
> Do not maintain a separate open-items list here — it will go stale.

- Open gaps by ID: `docs/gaps.md`
- Session scope and work items in order: `docs/session_roadmap.md`
- Context budget history for scope calibration: `docs/context_log.md`

---

## Instance Handoff Protocol

`docs/current_state.md` is the handoff surface for switching between Claude instances
(different accounts or handing to another developer). Only needed when actually switching.

**On user says `handoff`:** Update `docs/current_state.md` with:
- What was completed this session
- Next session work items (copied from session_roadmap.md, trimmed to essentials)
- Any in-progress or interrupted work
- Active known bugs not yet fixed
- Any discoveries not yet written to permanent docs

For web Claude receiving a handoff: user pastes `docs/current_state.md` + the relevant
sections of this file (rules, file structure, pipeline order).

`docs/current_state.md` is the only file updated at handoff and should only be updated when user requests a handoff for switching instances. Do not duplicate into MEMORY.md or gaps.md.

## End-of-Session Docs Maintenance (before commit)

- `docs/gaps.md` — mark completed gaps [x], update [~] partials
- `docs/completed_work.md` — append new session section with what was done
- `docs/session_roadmap.md` — remove completed session section and move to completed session reference list or update session section if not fully completed
- `docs/data_models.md` — for each field implemented: move it from its [NEW] block into the [EXISTS] block of the same section, keeping the comment
- `docs/core_architecture.md` — update if you changed core systems
- `docs/pipeline_specs.md` — update if you changed the pipeline
- `docs/gui_plan.md` — update if GUI design changes were decided upon
- `CLAUDE.md` — update Pipeline Step Order and modifiers list if steps added/reordered, update project structure if files added/deleted/moved
- **DO NOT touch `docs/current_state.md`** — only written on explicit user command `handoff`. Do not read or write it as part of routine session start or end.