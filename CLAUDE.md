# PS_Calc — Claude Code Instructions

## Project Overview
Pre-renewal Ragnarok Online toolkit in Python with CustomTkinter GUI.
Goal: faithfully implement all stat, damage, and mechanics from the Hercules emulator,
exposed through a feature-complete, user-friendly GUI for players and theorycrafters.

This is not just a damage calculator — the final product includes:
- Full damage calculation with step-by-step breakdown (power user accessible)
- Incoming damage calculation
- Stat point planner (interactive point allocation)
- Skill browser and selector
- Equipment / item database browser
- Monster database with search and filter
- Custom targets, weapons, items, and buff configuration
- Saved builds (save / load)
- Build, skill, and target comparison with damage and metric analysis

The reference implementation is the Hercules emulator (HerculesWS/Hercules),
cloned locally at `./Hercules/`. All formula decisions must be traceable to that source.

---

## Non-Negotiable Rules

- **Pre-renewal only.** Always take the non-RENEWAL path. Ignore all `#ifdef RENEWAL`
  and `#ifndef RENEWAL` blocks entirely.
- **Hercules is the source of truth.** If a formula is uncertain, grep the source
  before guessing. Do not rely on wikis or third-party calculators alone.
- **Every DamageStep must cite its source.** All `hercules_ref` fields must point
  to the exact function and file. Never leave them as "N/A".
- **Python 3.13.** No deprecated APIs.
- **GUI framework: CustomTkinter.** No mixing with raw Tkinter widgets except where
  unavoidable (e.g. ttk.Treeview as a temporary scaffold — to be replaced).
- **Use `status.int_` not `status.int`** everywhere. `int` shadows Python's built-in.
  Enforce this in all new and existing code.

---

## Hercules Source Location

All emulator source lives in `./Hercules/src/map/`.

Key files:
- `battle.c` — damage pipeline, defense, attr fix, size fix, skill ratios, masteries
- `status.c` — stat calculations: BATK, DEF, MDEF, ASPD, HIT, FLEE, HP, SP
- `skill.c` — skill-specific modifiers and NK flags
- `pc.c` — player character bonuses, job checks, riding state

### How to Research a Formula
Always grep before reading. Never load entire files.
```bash
# Find the function and its line number
grep -n "battle_calc_defense" Hercules/src/map/battle.c

# Read only the relevant range
sed -n '2341,2450p' Hercules/src/map/battle.c
```

---

## Project Structure

```
PS_Calc/
├── CLAUDE.md                        ← this file
├── main.py                          ← entry point, launches MainWindow
├── requirements.txt                 ← customtkinter>=5.2.0, pyinstaller
├── Hercules/                        ← emulator source (reference only, never modify)
│   └── src/map/
│       ├── battle.c
│       ├── status.c
│       ├── skill.c
│       └── pc.c
├── core/
│   ├── config.py                    ← BattleConfig (all battle.conf tunables)
│   ├── data_loader.py               ← DataLoader singleton (all data access)
│   ├── models/
│   │   ├── build.py                 ← PlayerBuild dataclass
│   │   ├── status.py                ← StatusData dataclass
│   │   ├── weapon.py                ← Weapon dataclass
│   │   ├── skill.py                 ← SkillInstance dataclass
│   │   ├── target.py                ← Target dataclass
│   │   └── damage.py                ← DamageResult + DamageStep
│   ├── calculators/
│   │   ├── status_calculator.py     ← StatusCalculator (status.c port)
│   │   ├── battle_pipeline.py       ← BattlePipeline orchestrator
│   │   └── modifiers/
│   │       ├── base_damage.py       ← battle_calc_base_damage2
│   │       ├── skill_ratio.py       ← skill damage multipliers
│   │       ├── size_fix.py          ← size penalty table
│   │       ├── attr_fix.py          ← elemental modifier table
│   │       ├── defense_fix.py       ← hard DEF % + soft DEF subtraction
│   │       ├── mastery_fix.py       ← weapon mastery flat bonuses
│   │       ├── active_status_bonus.py  ← SC_* active status bonuses
│   │       └── final_rate_bonus.py  ← weapon/short/long attack rate bonuses
│   └── data/pre-re/
│       ├── skills.json
│       └── tables/
│           ├── attr_fix.json
│           ├── size_fix.json
│           ├── mastery_fix.json
│           ├── mastery_weapon_map.json
│           ├── active_status_bonus.json
│           ├── element_rate.json
│           ├── job_aspd_base.json
│           └── refine_weapon.json
└── gui/
    ├── app_config.py                ← UI-only settings (theme, appearance)
    └── main_window.py               ← MainWindow (currently test scaffold, to be redesigned)
```

---

## Data Models — Key Details

### PlayerBuild (`core/models/build.py`)
- Stats split into `base_X` (character points) and `bonus_X` (equipment/cards/buffs)
- `active_status_levels: Dict[str, int]` — SC_* conditions e.g. `{"SC_AURABLADE": 1}`
- `mastery_levels: Dict[str, int]` — e.g. `{"SM_SWORD": 10}`
- `is_riding_peco: bool` — affects KN_SPEARMASTERY bonus
- `is_ranged: bool` — swaps STR/DEX role in BATK
- `is_katar: bool` — doubles critical rate
- `no_sizefix: bool` — bypasses size fix (sd->special_state.no_sizefix)

### StatusData (`core/models/status.py`)
- Use `int_` everywhere — never `int` (shadows Python built-in)
- `def_` = hard DEF (equipment), `def2` = soft DEF (VIT-based)
- `cri` stored in 0.1% units (100 = 10.0% crit chance)

### DamageStep (`core/models/damage.py`)
Every step must include:
- `name` — human-readable label (shown in clean results view)
- `value` — integer result after this step
- `note` — plain English explanation (shown on hover tooltip)
- `formula` — Python expression used (shown in power user toggle)
- `hercules_ref` — exact file + function from Hercules source (power user toggle)

### DataLoader (`core/data_loader.py`)
- Singleton — import as `from core.data_loader import loader`
- All data access must go through public methods only.
- Never call `loader._load_json()` directly from modifier classes.
  Add a public method to DataLoader instead.

---

## Known Bugs — Fix These Before Adding Features

### 1. FinalRateBonus — weapon_damage_rate never applied
`rate` is assigned `config.weapon_damage_rate` then immediately overwritten by
short/long rate, so weapon_damage_rate has no effect. Hercules applies it as a
separate multiplier. Fix: apply both multipliers as two sequential operations.

### 2. SkillRatio — SC_MAXIMIZEPOWER check is dead code
`ratio = 100` is set after `dmg_after_ratio` is already computed, so it has no
effect on the output. The check must happen before the multiplication.

### 3. AttrFix and MasteryFix — private method access
Both call `loader._load_json()` directly. Add public methods to DataLoader
(`get_attr_fix_multiplier`, `get_mastery_weapon_map`) and update both classes to
use them.

### 4. Damage Variance — unresolved, requires source verification
Variance is known to exist in at least two places:
- **VIT DEF soft defense** — `rnd() % variance_max` in `battle_calc_defense`,
  already partially modelled in DefenseFix but the average is off by one:
  `rnd() % variance_max` averages to `(variance_max - 1) / 2`, not `variance_max / 2`.
- **Weapon ATK / base damage** — there is believed to be a random component at or
  before the weapon ATK addition, but this has NOT been confirmed from source.
  Previous attempts hallucinated variance that did not exist. Do NOT implement
  any weapon ATK variance without first reading the relevant section of
  `battle_calc_base_damage2` verbatim from Hercules/src/map/battle.c.

**Required action before touching variance:** grep and read the full body of
`battle_calc_base_damage2` and `battle_calc_weapon_attack` from source, identify
every `rnd()` call and what it applies to, and document findings before writing
any code. When in doubt, do not implement — leave a clearly marked TODO instead.

### 6. StatusCalculator — ASPD, HP, SP are placeholders
Requires job_aspd_base.json integration and full job HP/SP multiplier tables.

---

## GUI Vision

### Design Philosophy: Progressive Disclosure
Clean and simple by default. Deep and technical on demand.

- **Casual users see:** damage summary card + clean step list (name + value only)
- **On hover:** tooltip reveals `note` and `formula` for that step
- **Power user toggle:** "Show Source" button expands `hercules_ref` inline per step
- The existing ttk.Treeview with raw column layout must be fully replaced.
- All DamageStep fields are already structured correctly — this is a UI layer change only.

### Layout
Not yet decided — propose the best layout before implementing. Consider the full
feature set: this tool will be used repeatedly with many combinations of builds,
skills, and targets. Usability and fast iteration between configurations is the
top priority. Evaluate side panel + results area vs. other approaches and recommend.

### Required Features (full product)
1. **Outgoing damage calculator** — clean results with progressive disclosure breakdown
2. **Incoming damage calculator** — same pipeline from target's perspective
3. **Stat point planner** — interactive base stat allocation with live recalculation
4. **Skill browser / selector** — searchable, select skill + level for calculation
5. **Equipment / item database browser** — search, filter, apply gear to build
6. **Monster database** — search and filter, select as damage target
7. **Custom inputs** — manually configure targets, weapons, items, buffs not in DB
8. **Saved builds** — save and load named builds (DataLoader already has stubs)
9. **Comparison tool** — compare builds / skills / targets side by side, analyze
   damage and other metrics across multiple configurations simultaneously

### Results View (replaces current treeview)
- Summary card at top: min / max / avg damage, crit chance, hit chance
- Step list below: name + final value per step, clean and compact
- Hover tooltip per step: shows `note` + `formula`
- "Show Source" toggle: reveals `hercules_ref` inline under each step
- Design for both casual readability and power user depth

---

## Coding Conventions
- Modifier classes use `@staticmethod def calculate(...)` — no instantiation needed
- One file per modifier — single responsibility
- Use `result.add_step(...)` for every discrete calculation — never silently mutate values
- All magic numbers must have a comment citing their origin in Hercules source
- No global state outside the `loader` singleton
- No `sudo`

---

## Verification & Testing

### Current State
The existing test presets (Knight Bash vs Porcellio, Spear/Peco vs Earth Lv3) are
development scaffolds only — they were used for early pipeline testing and are not
rigorous enough to verify formula correctness. Do not treat passing these tests as
proof that any formula is correct.

### What Proper Testing Requires
Before writing new tests, a proper test strategy needs to be designed. This is an
open task. Key requirements for any valid test:

- **Known reference values** — expected damage must come from a verified source:
  ideally in-game measurements on a private server running stock Hercules pre-renewal,
  or from rocalc.com with the exact same inputs confirmed to match Hercules behavior.
- **Full input specification** — every variable that touches the pipeline must be
  fixed and documented: base stats, bonus stats, weapon ATK, refine, weapon type,
  skill ID + level, target DEF, target VIT, target size, target element + level,
  active statuses, masteries, BattleConfig values.
- **Coverage across the pipeline** — tests should isolate individual modifiers
  (e.g. a test where only size fix varies) as well as end-to-end cases.
- **Variance handling** — until variance is properly understood and implemented,
  tests should use inputs that produce zero variance (e.g. VIT=0 on target where
  possible) or compare against a known range rather than a single value.

### Action
Do not add more ad-hoc presets. Instead, design a proper test framework first —
propose the structure before implementing. Consider pytest with clearly documented
fixtures, expected value sources, and tolerance handling for variance.
