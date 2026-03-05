# PS_Calc — Claude Code Instructions

## Ask First, Search Later

If a task requires locating files, external data, or unfamiliar formats — ask the
user first. One targeted grep or read is fine. Exploratory multi-file searches are
not. Stop and ask after one failed attempt.

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

C1. Damage Variance — **Session 2**
Three sources as `(min, max, scale)` tuples: weapon ATK range (crit→atkmax),
overrefine rnd(1,max) (NOT clamped on crit), VIT DEF rnd(0,max-1) (bypassed on crit;
avg currently off by 0.5). Variance and deterministic multipliers must stay strictly
separated. Foundation for Phase 7 histogram.

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

E1. Hit/Miss — **Session 2** — 80 + HIT − FLEE; Perfect Dodge 1+⌊LUK/10⌋+bonus.
E2. Damage Bonus/Reduction — size/race/element multipliers, blocked on D5.
E3. Bane skills — **Session 6** — Beast/Demon Bane, Dragonology. After VIT DEF, before RefineFix.
E4. Katar second hit — **Session 6** — verify fraction from source.
E5. SC_IMPOSITIO in BATK — likely feeds bonus_batk. Verify against source.
E6. Forged weapon Verys — flat +5/Very after elemental modifier.
E7. Cart Revolution double elemental fix.
E8. GS_GROUNDDRIFT — separate 50*lv neutral component with own elemental fix.