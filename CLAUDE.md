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

- **Pre-renewal only.** This project targets pre-renewal kRO mechanics exclusively.
- **Hercules is the source of truth.** If a formula is uncertain, grep the source
  before guessing. Do not rely on wikis or third-party calculators alone.
- **Every DamageStep must cite its source.** All `hercules_ref` fields must point
  to the exact function and file. Never leave them as "N/A".
- **Python 3.13.** No deprecated APIs.
- **GUI framework: CustomTkinter.** No mixing with raw Tkinter widgets except where
  unavoidable (e.g. ttk.Treeview as a temporary scaffold — to be replaced).
- **Use `status.int_` not `status.int`** everywhere. `int` shadows Python's built-in.
  Enforce this in all new and existing code.

### CRITICAL: Renewal vs Pre-Renewal Guards

Hercules source contains mechanics for both pre-renewal and renewal in the same
files, separated by preprocessor guards. **Reading past or ignoring these guards
is the single most common source of bugs in this project.**

Rules for reading Hercules source:
- Code inside `#ifdef RENEWAL` — **renewal only. Ignore entirely.**
- Code inside `#ifndef RENEWAL` — **pre-renewal only. This is what we implement.**
- Code with no guard — applies to both. Implement as-is.
- When in doubt, check for a guard. Assume guarded until verified otherwise.

Known examples of renewal-only mechanics that must NOT appear in pre-renewal code:
- LUK contributing to HIT (verified renewal-only in-game)
- LUK contributing to FLEE (verified renewal-only in-game)
- SC_IMPOSITIO ATK_ADD in battle_calc_base_damage2 (inside #ifdef RENEWAL)
- SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2 (inside #ifdef RENEWAL)

When reading a Hercules function, always grep for `#ifdef RENEWAL` and `#ifndef RENEWAL`
within that function's line range before implementing anything from it.
Example: `sed -n '607,690p' Hercules/src/map/battle.c | grep -n "RENEWAL"`

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

Bugs are grouped by priority. Fix Group A entirely before touching Group B or C.
Do not add new features until Group A is resolved.

---

### GROUP A — Formula Correctness (highest priority)

#### A1. StatusCalculator — status.int_ naming (CRITICAL)
`core/models/status.py` declares `int: int = 0` — shadows Python's builtin.
`core/calculators/status_calculator.py` assigns `status.int = ...` throughout.
Rename field to `int_` in both files and every reference across the codebase.
Enforce this rule on all new code — never use `int` as a field name.

#### A2. StatusCalculator — HIT formula (VERIFIED — current formula is correct)
LUK contributing to HIT is **renewal-only**. Verified in-game on private server.
The current formula `status.hit = build.base_level + status.dex + build.bonus_hit`
is correct for pre-renewal. No change needed. Remove the TODO comment if present.

#### A3. StatusCalculator — FLEE formula (VERIFIED — current formula is correct)
Same as A2. LUK contributing to FLEE is **renewal-only**. Verified in-game.
The current formula `status.flee = build.base_level + status.agi + build.bonus_flee`
is correct for pre-renewal. No change needed. Remove the TODO comment if present.

#### A4. BattlePipeline — SizeFix is double-applied (CRITICAL)
`battle_calc_base_damage2` already applies size fix internally for PC targets
via `sd->right_weapon.atkmods[t_size]` (battle.c lines 659-664).
The standalone `SizeFix` step in `battle_pipeline.py` applies it a second time,
making all PC damage wrong. Remove the SizeFix step from the pipeline entirely.
The `size_fix.py` modifier file can be kept for reference but must not be called.

#### A5. BattlePipeline — wrong step order
The correct pre-renewal order from `battle_calc_weapon_attack` source is:
```
BaseDamage    ← battle_calc_base_damage2 (SizeFix is INTERNAL to this for PC)
SkillRatio    ← battle_calc_skillratio
DefenseFix    ← battle_calc_defense (called ~line 5725-5738)
ActiveStatusBonus  ← SC_AURABLADE etc. applied POST-defense (lines 5770-5795)
MasteryFix    ← calc_masteryfix (#ifndef RENEWAL, lines 5815-5818)
AttrFix       ← calc_elefix (after mastery in pre-renewal)
FinalRateBonus
```
Current pipeline has SizeFix between SkillRatio and DefenseFix (wrong),
and MasteryFix before ActiveStatusBonus (wrong). Reorder to match source.

---

### GROUP B — Data Correctness

#### B1. active_status_bonus.json — SC_MAXIMIZEPOWER is wrong
SC_MAXIMIZEPOWER has NO ATK_ADD in pre-renewal `battle_calc_weapon_attack`.
Its only effect: `atkmin = atkmax` inside `battle_calc_base_damage2` (line 648)
— it collapses variance, it does not add flat damage.
Remove SC_MAXIMIZEPOWER from active_status_bonus.json entirely.
Handle variance collapse in BaseDamage when this SC is present in build.

#### B2. active_status_bonus.json — SC_SPURT origin unverified
Grep of `Hercules/src/map/*.c` returned zero results for SC_SPURT.
However, the `Hercules/db/` directory (conf/txt files) was NOT searched.
Before removing SC_SPURT or declaring it hallucinated, Claude Code must run:
  `grep -rn "SPURT" Hercules/db/`
  `grep -rn "SPURT" Hercules/src/`
If zero results across both: remove from active_status_bonus.json and note it
was hallucinated by a previous model. If found in db but not src: document what
it is and whether it applies to pre-renewal. Do not remove without checking both.

#### B3. active_status_bonus.json — SC_GS_MADNESSCANCEL is RENEWAL-only
The ATK_ADD for SC_GS_MADNESSCANCEL in `battle_calc_base_damage2` is wrapped
in `#ifdef RENEWAL`. No pre-renewal ATK_ADD exists anywhere in the source.
Remove from active_status_bonus.json.

#### B4. active_status_bonus.json — SC_IMPOSITIO is RENEWAL-only
Same issue — SC_IMPOSITIO ATK_ADD is inside `#ifdef RENEWAL` (source line ~881).
No pre-renewal effect in the weapon damage path.
Remove from active_status_bonus.json.

#### B5. active_status_bonus.json — SC_OVERTHRUST belongs in skill_ratio.py
SC_OVERTHRUST does NOT add flat ATK. In pre-renewal it adds `val3` to
`skillratio` inside `battle_calc_skillratio` (source lines 2919-2920).
SC_OVERTHRUSTMAX adds `val2` (source lines 2921-2922).
Remove both from active_status_bonus.json.
Add handling to skill_ratio.py: read level from `build.active_status_levels`,
look up val3/val2 from config, and add to ratio before applying to damage.

#### B6. Test presets — incomplete stat fields
Both build presets are missing `base_agi`, `base_dex`, `base_int`, `base_luk`,
`job_level` — these default to 1, making BATK, HIT, FLEE, and crit wrong.
Do NOT fill these in with guessed values. See Verification section below —
proper test values require verified in-game measurements first.
Mark existing presets as known-incomplete development scaffolds only.

---

### GROUP C — Known Gaps (implement after A and B)

#### C1. Damage Variance — partially confirmed, implement carefully
Three confirmed variance sources from source reading:
- **Weapon ATK range** — `rnd() % (atkmax - atkmin) + atkmin` in
  `battle_calc_base_damage2` lines 652-655. `atkmax = weapon.atk`,
  `atkmin = dex-based value`. This IS confirmed variance.
- **Overrefine bonus** — `rnd() % sd->right_weapon.overrefine + 1`
  (source lines ~680-685). Adds random overrefine variance.
- **VIT DEF soft defense** — `rnd() % variance_max` in `battle_calc_defense`.
  DefenseFix currently uses `variance_max / 2` for average but correct
  average is `(variance_max - 1) / 2`.
Implement only after reading exact source lines. Verify ranges on private
server before finalising. Use controlled tests (VIT=0 target) to isolate.

#### C2. FinalRateBonus — application context unclear
`short_damage_rate` and `long_damage_rate` in Hercules are map-level properties
(`map->list[bl->m].short_damage_rate`), not a global BattleConfig field.
Current implementation applies them as global config values which may not match
Hercules behaviour. Verify the intended use before fixing.

#### C3. StatusCalculator — ASPD, HP, SP are placeholders
Requires `job_aspd_base.json` integration and full job HP/SP multiplier tables.
Implement after Groups A and B are resolved.

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