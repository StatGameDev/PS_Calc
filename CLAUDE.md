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
├── saves/                           ← user-saved builds (one JSON per build)
│   └── .gitkeep
├── tools/
│   └── import_item_db.py            ← one-shot scraper: item_db.conf → item_db.json ✓
├── Hercules/                        ← emulator source (reference only, never modify)
│   └── src/map/
│       ├── battle.c
│       ├── status.c
│       ├── skill.c
│       └── pc.c
├── core/
│   ├── config.py                    ← BattleConfig (all battle.conf tunables)
│   ├── data_loader.py               ← DataLoader singleton (all data access)
│   ├── build_manager.py             ← BuildManager: save/load/resolve builds ✓
│   ├── models/
│   │   ├── build.py                 ← PlayerBuild dataclass
│   │   ├── status.py                ← StatusData dataclass
│   │   ├── weapon.py                ← Weapon dataclass + RANGED_WEAPON_TYPES
│   │   ├── skill.py                 ← SkillInstance dataclass
│   │   ├── target.py                ← Target dataclass
│   │   └── damage.py                ← DamageResult + DamageStep
│   ├── calculators/
│   │   ├── status_calculator.py     ← StatusCalculator (status.c port)
│   │   ├── battle_pipeline.py       ← BattlePipeline orchestrator
│   │   └── modifiers/
│   │       ├── base_damage.py       ← battle_calc_base_damage2 (SizeFix internal)
│   │       ├── skill_ratio.py       ← skill damage multipliers
│   │       ├── size_fix.py          ← size penalty table (reference only, not called)
│   │       ├── attr_fix.py          ← elemental modifier table
│   │       ├── defense_fix.py       ← hard DEF % + soft DEF subtraction
│   │       ├── mastery_fix.py       ← weapon mastery flat bonuses
│   │       ├── active_status_bonus.py  ← SC_AURABLADE only (all others removed)
│   │       └── final_rate_bonus.py  ← weapon/short/long attack rate bonuses
│   └── data/pre-re/
│       ├── skills.json
│       ├── db/
│       │   ├── item_db.json         ← 708 weapons scraped from item_db.conf ✓
│       │   └── mob_db.json          ← Phase 3 (not yet created)
│       ├── tables/
│       │   ├── attr_fix.json
│       │   ├── size_fix.json
│       │   ├── mastery_fix.json
│       │   ├── mastery_weapon_map.json
│       │   ├── active_status_bonus.json  ← SC_AURABLADE only ✓
│       │   ├── element_rate.json
│       │   ├── job_aspd_base.json
│       │   └── refine_weapon.json
│       └── test_presets/            ← development scaffolds only, not ground truth
│           ├── builds/
│           ├── skills/
│           └── targets/
└── gui/
    ├── app_config.py                ← UI-only settings (theme, appearance)
    └── main_window.py               ← MainWindow (test scaffold, to be redesigned)
```

---

## Data Models — Key Details

### PlayerBuild (`core/models/build.py`)
- Stats split into `base_X` (character points) and `bonus_X` (equipment/cards/buffs)
- `name: str` — display name for the build
- `equipped: Dict[str, Optional[int]]` — slot → item ID, e.g. `{"right_hand": 1225}`
- `refine_levels: Dict[str, int]` — slot → refine level, e.g. `{"right_hand": 7}`
- `active_status_levels: Dict[str, int]` — SC_* conditions e.g. `{"SC_AURABLADE": 1}`
- `mastery_levels: Dict[str, int]` — e.g. `{"SM_SWORD": 10}`
- `is_riding_peco: bool` — affects KN_SPEARMASTERY bonus
- `is_ranged_override: Optional[bool] = None` — normally None; derived automatically
  from weapon type via `effective_is_ranged()`. Set only to force an override.
- `no_sizefix: bool` — bypasses size fix (sd->special_state.no_sizefix)
- `is_katar` — REMOVED. Katar detection now derived from weapon_type == W_KATAR.

### Weapon (`core/models/weapon.py`)
- `RANGED_WEAPON_TYPES: frozenset` — W_BOW, W_MUSICAL, W_WHIP, W_REVOLVER, W_RIFLE,
  W_GATLING, W_SHOTGUN, W_GRENADE. Used by `effective_is_ranged()`.
- `aegis_name: str` — display name from item_db, no calculation effect
- `refineable: bool` — if False, overrefine bonus is suppressed in base_damage.py

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
- `get_test_preset_weapon` is **deprecated** — routes through BuildManager now.

### BuildManager (`core/build_manager.py`)
Handles all user-owned save files. DataLoader handles static databases.
- `save_build(build: PlayerBuild, path: str) -> None`
- `load_build(path: str) -> PlayerBuild` — applies Unarmed fallback on missing IDs
- `list_builds(directory: str) -> List[str]`
- `resolve_weapon(item_id: Optional[int]) -> Weapon` — looks up item_db; on missing
  ID logs `WARNING: Item ID {id} not found in item_db. Using Unarmed defaults.`
  and returns Unarmed (ATK 0, wlv 1, neutral element, all size modifiers 100%).
  Unarmed is distinct from the in-game W_FIST weapon type.

---

## Data Architecture — Saves and Databases

### Separation of Concerns
A saved build file contains only character-owned data. Item properties are looked
up from the item database at runtime by ID. Never duplicate item stats inline in
a build file.

**Build file owns:** base stats, job, level, refine levels, equipped item IDs,
active buff levels, mastery levels, flags (is_riding_peco, no_sizefix).

**Item database owns:** weapon ATK, weapon type, weapon level, element, weight,
refineable flag — anything intrinsic to the item itself.

### Build File Schema
```json
{
  "name": "My LK",
  "job_id": 7,
  "base_level": 99,
  "base_stats": {
    "str": 80, "agi": 30, "vit": 70, "int": 10, "dex": 50, "luk": 10
  },
  "bonus_stats": {
    "str": 0, "agi": 0, "vit": 0, "int": 0, "dex": 0, "luk": 0,
    "hit": 0, "flee": 0, "cri": 0, "batk": 0
  },
  "equipped": {
    "right_hand": 1225,
    "ammo": null
  },
  "refine": {
    "right_hand": 0
  },
  "active_buffs": { "SC_OVERTHRUST": 5 },
  "mastery_levels": { "SM_SWORD": 10 },
  "flags": {
    "is_ranged_override": null,
    "is_riding_peco": false,
    "no_sizefix": false
  }
}
```
Note: `is_katar` is not in the schema — derived from weapon_type == W_KATAR.
`is_ranged_override` is null in normal use — derived from weapon type automatically.

---

## Phase Plan

### Completed
- **Pipeline core** — BattlePipeline, all modifier files, StatusCalculator
- **Group A fixes** — int_ rename (A1), SizeFix double-apply removed (A4),
  pipeline step order corrected (A5). A2/A3 verified correct as-is.
- **Phase 1 — Save/load** — BuildManager, build file schema, test presets migrated
- **Phase 2 — item_db** — 708 weapons scraped from item_db.conf via custom parser
- **C4** — refineable flag wired up in base_damage.py
- **C5** — is_ranged and is_katar derived from weapon type; manual flags removed
- **Group B fixes** — active_status_bonus.json stripped to SC_AURABLADE only;
  SC_OVERTHRUST/SC_OVERTHRUSTMAX moved to skill_ratio.py
- **base_damage.py order fix** — overrefine now correctly applied after refine bonus;
  Weapon ATK Range step added to DamageResult
- **GUI weapon display** — RAW INPUTS row shows aegis_name, ID, ATK, level,
  weapon type, refine, and refineable flag

### Next: Phase 3 — mob_db

**Phase 3 — mob_db**
- Scrape `Hercules/db/pre-re/mob_db.conf` → `mob_db.json`
- Extend DataLoader with `get_monster(mob_id)`
- Replace manual Target test presets with DB-backed lookups

---

## Known Bugs

### GROUP A — Formula Correctness (ALL DONE)

#### A1. DONE — status.int_ rename
`status.py` and `status_calculator.py` updated. `int_` enforced throughout.

#### A2. VERIFIED CORRECT — HIT formula
LUK contributing to HIT is renewal-only (verified in-game). Current formula
`status.hit = base_level + dex + bonus_hit` is correct for pre-renewal.

#### A3. VERIFIED CORRECT — FLEE formula
LUK contributing to FLEE is renewal-only (verified in-game). Current formula
`status.flee = base_level + agi + bonus_flee` is correct for pre-renewal.

#### A4. DONE — SizeFix double-apply removed
Standalone SizeFix step removed from pipeline. SizeFix remains internal to
BaseDamage (battle_calc_base_damage2) as Hercules source requires.
`size_fix.py` kept for reference but is no longer called.

#### A5. DONE — Pipeline step order corrected
Correct pre-renewal order now implemented:
```
BaseDamage → SkillRatio → DefenseFix → ActiveStatusBonus → MasteryFix → AttrFix → FinalRateBonus
```

---

### GROUP B — Data Correctness (ALL DONE)

#### B1. DONE — SC_MAXIMIZEPOWER removed from active_status_bonus.json
Variance collapse (atkmin = atkmax) now handled inside BaseDamage when
SC_MAXIMIZEPOWER is present. Logged as a "Weapon ATK Range" step note.

#### B2. DONE — SC_SPURT removed (confirmed hallucinated)
Zero results in both `Hercules/src/` and `Hercules/db/`. Never existed.

#### B3. DONE — SC_GS_MADNESSCANCEL removed (RENEWAL-only)
#### B4. DONE — SC_IMPOSITIO removed (RENEWAL-only)

#### B5. DONE — SC_OVERTHRUST moved to skill_ratio.py
SC_OVERTHRUST adds val3 (+5×level) to skillratio (battle.c:2919-2920).
SC_OVERTHRUSTMAX adds val2 (+20×level) to skillratio (battle.c:2921-2922).
Both removed from active_status_bonus.json and handled in skill_ratio.py.
active_status_bonus.json comment documents all removals and reasons.

#### B6. Test presets — incomplete stat fields
Both build presets default base_agi, base_dex, base_int, base_luk, job_level to 1.
Do NOT fill with guessed values — requires verified in-game measurements.
Scaffolds only.

---

### GROUP C — Known Gaps

#### C1. Damage Variance — implement carefully
Three confirmed variance sources:
- **Weapon ATK range** — `rnd() % (atkmax - atkmin) + atkmin` in
  `battle_calc_base_damage2` lines 652-655. Confirmed. Step is now logged.
- **Overrefine bonus** — `rnd() % sd->right_weapon.overrefine + 1`
  (source lines ~680-685). Confirmed. Step is now logged.
- **VIT DEF soft defense** — `rnd() % variance_max` in `battle_calc_defense`.
  Current average uses `variance_max / 2`; correct is `(variance_max - 1) / 2`.
Read exact source lines before implementing. Verify on private server.
Use VIT=0 targets to isolate weapon variance from DEF variance.

#### C2. FinalRateBonus — application context unclear
`short_damage_rate` and `long_damage_rate` in Hercules are map-level properties
(`map->list[bl->m].short_damage_rate`), not global BattleConfig fields.
Verify intended use before fixing.

#### C3. StatusCalculator — ASPD, HP, SP are placeholders
Requires `job_aspd_base.json` integration and full job HP/SP multiplier tables.

#### C4. DONE — BaseDamage refineable flag wired up
Overrefine block in `base_damage.py` wrapped in `if weapon.refineable:`.
Unrefineable weapons correctly receive zero overrefine bonus.

#### C5. DONE — Derived flags is_ranged and is_katar
`RANGED_WEAPON_TYPES` frozenset defined in `weapon.py` (8 types: W_BOW, W_MUSICAL,
W_WHIP, W_REVOLVER, W_RIFLE, W_GATLING, W_SHOTGUN, W_GRENADE).
`is_katar` removed from PlayerBuild entirely.
`is_ranged` replaced by `is_ranged_override: Optional[bool] = None` on PlayerBuild.
`effective_is_ranged()` helper derives flag from weapon type, falling back to
override only when explicitly set.
`status_calculator.py` now takes `is_ranged: bool` directly — no longer depends on build.
`battle_pipeline.py` pre-computes `is_ranged` via `effective_is_ranged` before calling
FinalRateBonus. All calc calls pass `weapon` explicitly.
Test preset JSONs updated: `is_katar`/`is_ranged` replaced by `"is_ranged_override": null`.

---

## GUI Vision

### Design Philosophy: Progressive Disclosure
Clean and simple by default. Deep and technical on demand.

- **Casual users see:** damage summary card + clean step list (name + value only)
- **On hover:** tooltip reveals `note` and `formula` for that step
- **Power user toggle:** "Show Source" button expands `hercules_ref` inline per step
- The existing ttk.Treeview must be fully replaced.
- All DamageStep fields are already structured correctly — UI layer change only.

### Layout
Not yet decided — propose before implementing. Usability and fast iteration across
builds/skills/targets is the top priority. Recommend an approach before coding.

### Required Features (full product)
1. Outgoing damage calculator — clean results with progressive disclosure breakdown
2. Incoming damage calculator — same pipeline from target's perspective
3. Stat point planner — interactive base stat allocation with live recalculation
4. Skill browser / selector — searchable, select skill + level for calculation
5. Equipment / item database browser — search, filter, apply gear to build
6. Monster database — search and filter, select as damage target
7. Custom inputs — manually configure targets, weapons, items, buffs not in DB
8. Saved builds — save and load named builds
9. Comparison tool — compare builds / skills / targets side by side

### Results View (replaces current treeview)
- Summary card at top: min / max / avg damage, crit chance, hit chance
- Step list below: name + final value per step, clean and compact
- Hover tooltip per step: shows `note` + `formula`
- "Show Source" toggle: reveals `hercules_ref` inline under each step

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
development scaffolds only. Do not treat them as proof any formula is correct.

### What Proper Testing Requires
- **Known reference values** — from in-game measurements on a private Hercules
  pre-renewal server, or rocalc.com with confirmed matching inputs.
- **Full input specification** — every pipeline variable fixed and documented:
  base stats, bonus stats, weapon ATK, refine, weapon type, skill ID + level,
  target DEF/VIT/size/element/level, active statuses, masteries, BattleConfig.
- **Pipeline coverage** — isolate individual modifiers as well as end-to-end cases.
- **Variance handling** — use VIT=0 targets or compare ranges until variance is
  fully implemented.

### Action
Do not add ad-hoc presets. Design a proper pytest framework first — propose
structure before implementing. Fixtures must document expected value sources.