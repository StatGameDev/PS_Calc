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
│   ├── knight_bash.json             ← scaffold: LK Bash vs Porcellio (mob 1619) ✓
│   └── spear_peco.json              ← scaffold: LK Spear/Peco vs Sandman (mob 1165) ✓
├── tools/
│   ├── import_item_db.py            ← scraper: item_db.conf → item_db.json ✓
│   └── import_mob_db.py             ← scraper: mob_db.conf → mob_db.json ✓
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
│       │   └── mob_db.json          ← 1007 mobs scraped from mob_db.conf ✓
│       ├── tables/
│       │   ├── attr_fix.json
│       │   ├── size_fix.json
│       │   ├── mastery_fix.json
│       │   ├── mastery_weapon_map.json
│       │   ├── active_status_bonus.json  ← SC_AURABLADE only ✓
│       │   ├── element_rate.json
│       │   ├── job_aspd_base.json
│       │   └── refine_weapon.json
│       └── (test_presets/ deleted — scaffolds moved to saves/)
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
- `weapon_elements: Dict[str, int]` — slot → element int (0-9). Overrides item_db
  element per slot. Used for elemental imbues until a proper SC/item system is built.
- `target_mob_id: Optional[int]` — when set, pipeline caller resolves target via
  `loader.get_monster(build.target_mob_id)`. None = caller supplies Target manually.
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

### Target (`core/models/target.py`)
Pipeline fields: `def_`, `vit`, `size`, `race`, `element`, `element_level`, `is_boss`, `level`
Display fields: `hp`, `mdef`, `atk_min`, `atk_max`, `sprite_name`, `name`

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
- `get_monster(mob_id) -> Target` — pipeline use; WARNING + safe default on missing ID
- `get_monster_data(mob_id) -> Optional[Dict]` — GUI display use

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

**Mob database owns:** all Target pipeline fields — def_, vit, size, race, element,
element_level, is_boss, level. Never hardcode these in test presets or GUI code.

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
  "target_mob_id": 1619,
  "equipped": {
    "right_hand": 1225,
    "ammo": null
  },
  "refine": {
    "right_hand": 0
  },
  "weapon_elements": {
    "right_hand": 3
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
Notes:
- `is_katar` not in schema — derived from weapon_type == W_KATAR.
- `is_ranged_override` null in normal use — derived from weapon type automatically.
- `target_mob_id` null/absent = caller supplies Target manually (future GUI inputs).
- `weapon_elements` absent = use item_db element. Present = override per slot.
  Used for elemental imbues (scrolls, SCs) until a proper system is implemented.

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
- **Phase 3 — mob_db** — 1007 mobs scraped from mob_db.conf; get_monster() and
  get_monster_data() added to DataLoader
- **Preset migration** — test_presets/ deleted; both scaffolds moved to saves/ with
  real item IDs, target_mob_id, and weapon_elements override. GUI updated to a
  build dropdown (CTkOptionMenu) that lists all files in saves/.

### Next: GUI redesign

The current `main_window.py` is a test scaffold and must be fully replaced.
Before writing any GUI code, Claude Code must propose a layout and get approval.
See the GUI Vision section for requirements and design philosophy.

---

## Known Bugs and Open Items

### GROUP A — Formula Correctness (ALL DONE)

#### A1. DONE — status.int_ rename
#### A2. VERIFIED CORRECT — HIT formula (LUK contribution is renewal-only)
#### A3. VERIFIED CORRECT — FLEE formula (LUK contribution is renewal-only)
#### A4. DONE — SizeFix double-apply removed
#### A5. DONE — Pipeline step order corrected
```
BaseDamage → SkillRatio → DefenseFix → ActiveStatusBonus → MasteryFix → AttrFix → FinalRateBonus
```

---

### GROUP B — Data Correctness (ALL DONE)

#### B1. DONE — SC_MAXIMIZEPOWER removed; variance collapse handled in BaseDamage
#### B2. DONE — SC_SPURT removed (confirmed hallucinated — zero results in src/ and db/)
#### B3. DONE — SC_GS_MADNESSCANCEL removed (RENEWAL-only)
#### B4. DONE — SC_IMPOSITIO removed (RENEWAL-only)
#### B5. DONE — SC_OVERTHRUST/SC_OVERTHRUSTMAX moved to skill_ratio.py

#### B6. DONE — Test presets migrated
Both scaffolds moved to saves/ with real mob IDs. test_presets/ deleted.
Target stats now resolved from mob_db at runtime via loader.get_monster(target_mob_id).

---

### GROUP C — Known Gaps

#### C1. Damage Variance — implement carefully
Three confirmed variance sources:
- **Weapon ATK range** — `rnd() % (atkmax - atkmin) + atkmin` in
  `battle_calc_base_damage2` lines 652-655. Step now logged in DamageResult.
- **Overrefine bonus** — `rnd() % sd->right_weapon.overrefine + 1`
  (source lines ~680-685). Step now logged in DamageResult.
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
#### C5. DONE — Derived flags is_ranged and is_katar

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
Not yet decided — **propose before implementing**. Usability and fast iteration
across builds/skills/targets is the top priority. Recommend an approach before
writing any code. Consider the full feature set (9 items below) — the layout must
accommodate all of them without feeling cluttered in the common case.

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
Two scaffold builds exist in saves/ (knight_bash.json, spear_peco.json).
Both use real item IDs and mob_db-backed targets. Stats are still placeholder 1s
for agi/dex/int/luk. Do not treat any scaffold output as a verified reference value.

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