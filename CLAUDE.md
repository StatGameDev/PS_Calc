# PS_Calc — Claude Code Instructions

## Ask First, Search Later

If a task requires locating files, external data, or unfamiliar formats — ask the
user first. One targeted grep or read is fine. Exploratory multi-file searches are
not. Stop and ask after one failed attempt.

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
LUK→HIT, LUK→FLEE, SC_IMPOSITIO ATK_ADD in battle_calc_base_damage2,
SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2.

---

## Hercules Source

`./Hercules/src/map/` — battle.c, status.c, skill.c, pc.c

    grep -n "function_name" Hercules/src/map/battle.c
    sed -n 'START,ENDp' Hercules/src/map/battle.c

Always grep first. Never load entire files.

---

## Project File Structure

### Core calculator files (`core/calculators/`)

    core/calculators/battle_pipeline.py        — BattlePipeline orchestrator
    core/calculators/status_calculator.py      — StatusCalculator (HIT, FLEE, BATK, CRI, DEF)
    core/calculators/modifiers/
        base_damage.py       — weapon ATK range, SizeFix, overrefine (battle_calc_base_damage2)
        skill_ratio.py       — SkillRatio (battle_calc_skillratio)
        defense_fix.py       — DefenseFix: hard DEF % + VIT DEF rnd range
        crit_atk_rate.py     — CritAtkRate (pre-defense crit bonus)
        active_status_bonus.py — SC_AURABLADE etc. (post-defense)
        refine_fix.py        — RefineFix: deterministic atk2 (post-defense)
        mastery_fix.py       — MasteryFix (battle_calc_masteryfix, #ifndef RENEWAL)
        attr_fix.py          — AttrFix: elemental multiplier table
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
    tables/            — size_fix, attr_fix, refine_weapon, mastery_fix, active_status_bonus

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

> See MODELS.md for data model reference (PlayerBuild, BattleResult, Target, etc.)

---

## Pipeline Step Order

    BaseDamage → SkillRatio → DefenseFix → CritAtkRate (crit only) →
    RefineFix → ActiveStatusBonus → MasteryFix → AttrFix → FinalRateBonus

---

## Session Plan

Phases 0–4 complete. See GUI_PLAN.md for full session specs and bug details.

> Reference files: MODELS.md (data models, DataLoader, project structure) —
> PHASES_DONE.md (completed phase specs, archive only) —
> COMPLETED_WORK.md (work log, codebase map)

| Session | Focus | Key constraint |
|---|---|---|
| 1 | GUI stabilization: fix B3+B4+B5, verify B6+B7 | No new features until layout is stable |
| 2 | C1 Variance (tuple threading) + E1 Hit/Miss | Variance sources and deterministic multipliers strictly separated |
| 3 | C3 ASPD + HP + SP together | Leave bonus stubs for Session 4 |
| 4 | D5/D4 Script parsing + gear/card effects + tooltips | Grep bonus-type distribution before starting; decide manual-vs-generated split first |
| 5 | GUI enhancements: 4.4–4.7 (filters) | No pipeline deps |
| 6 | E3 Bane skills + E4 Katar second hit + polish | — |

---

## Open Items

### C — Pipeline Gaps

C1. Damage Variance — **Needs planning session (web Claude)**
`DamageRange(min, max, avg)` is insufficient for histogram computation.
Multiple independent random variables (weapon ATK, overrefine, VIT DEF) are
convolved through the pipeline — the full distribution is NOT recoverable from
min/max/avg alone. Needs proper design: exact convolution, Irwin-Hall
approximation, or Monte Carlo. Plan in web Claude before implementing.
C1a (VIT DEF avg off-by-0.5): DONE — `variance_max//2` in defense_fix.py.

C2. FinalRateBonus — short/long_damage_rate are map-level in Hercules, not global
BattleConfig. Verify before fixing.

C3. StatusCalculator — **Session 3** — ASPD, HP, SP placeholders.
All three share the same pattern; implement together. Bonus stubs defined here,
populated in Session 4.

### D — Data Infrastructure

D4. Card effects — **Session 4**, depends on D5.
D5. Script parsing — **Session 4**. Parse bonus/bonus2/bonus3 → structured effect
lists → numeric bonuses into stat/pipeline layers → human-readable tooltips.
Quality bar: ratemyserver.com descriptions. Grep item_db bonus-type distribution
before starting to decide manual-vs-generated split.

### E — Additional Pipeline Mechanics

E1. Hit/Miss — **Session 3** — 80 + HIT − FLEE; Perfect Dodge 1+⌊LUK/10⌋+bonus.
    hitrate has further modifiers not yet modelled (skill bonuses, SC_FOGWALL,
    arrow_hit, agi_penalty_type). Implement basic formula first; add TODO for rest.
E2. Damage Bonus/Reduction — size/race/element multipliers, blocked on D5.
E3. Bane skills — **Session 6** — Beast/Demon Bane, Dragonology. After VIT DEF, before RefineFix.
E4. Katar second hit — **Session 6** — verify fraction from source.
E5. SC_IMPOSITIO in BATK — likely feeds bonus_batk. Verify against source.
E6. Forged weapon Verys — flat +5/Very after elemental modifier.
E7. Cart Revolution double elemental fix.
E8. GS_GROUNDDRIFT — separate 50*lv neutral component with own elemental fix.