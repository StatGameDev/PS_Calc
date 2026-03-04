# PS_Calc — Claude Code Instructions

## Project Overview
Pre-renewal Ragnarok Online toolkit in Python with CustomTkinter GUI.
Faithfully implements all stat, damage, and mechanics from the Hercules emulator,
exposed through a feature-complete GUI for players and theorycrafters.

Features: outgoing/incoming damage calculator with step-by-step breakdown, stat
point planner, skill browser, equipment/item browser, monster database, custom
inputs, saved builds, build/skill/target comparison.

Reference implementation: Hercules emulator cloned at `./Hercules/`.
All formula decisions must be traceable to that source.

---

## Non-Negotiable Rules

- **Pre-renewal only.**
- **Hercules is the source of truth.** Grep before guessing. No wikis.
- **Every DamageStep must cite its source.** `hercules_ref` must point to the
  exact function and file. Never "N/A".
- **Python 3.13.** No deprecated APIs.
- **GUI: CustomTkinter.** No raw Tkinter except unavoidable scaffolds (ttk.Treeview).
- **Use `status.int_` not `status.int`** everywhere.

### CRITICAL: Renewal vs Pre-Renewal Guards

Hercules encodes both modes in the same files using preprocessor guards.
**Ignoring these guards is the most common source of bugs in this project.**

- `#ifdef RENEWAL` — renewal only. **Ignore entirely.**
- `#ifndef RENEWAL` — pre-renewal only. **This is what we implement.**
- No guard — applies to both.

Always grep for RENEWAL guards within a function's line range before implementing:
`sed -n '607,690p' Hercules/src/map/battle.c | grep -n "RENEWAL"`

Known renewal-only mechanics that must NOT appear in pre-renewal code:
- LUK → HIT (verified in-game)
- LUK → FLEE (verified in-game)
- SC_IMPOSITIO ATK_ADD in battle_calc_base_damage2
- SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2

---

## Hercules Source Location

`./Hercules/src/map/` — key files: `battle.c`, `status.c`, `skill.c`, `pc.c`

### How to Research a Formula
```bash
grep -n "battle_calc_defense" Hercules/src/map/battle.c
sed -n '2341,2450p' Hercules/src/map/battle.c
```
Always grep first. Never load entire files.

---

## Project Structure

```
PS_Calc/
├── CLAUDE.md
├── main.py
├── requirements.txt                 ← customtkinter>=5.2.0, pyinstaller
├── saves/                           ← user-saved builds (one JSON per build)
│   ├── knight_bash.json             ← scaffold: LK Bash vs Porcellio (mob 1619)
│   └── spear_peco.json              ← scaffold: LK Spear/Peco vs Sandman (mob 1165)
├── tools/
│   ├── import_item_db.py            ← scraper: item_db.conf → item_db.json
│   └── import_mob_db.py             ← scraper: mob_db.conf → mob_db.json
├── Hercules/                        ← reference only, never modify
├── core/
│   ├── config.py                    ← BattleConfig
│   ├── data_loader.py               ← DataLoader singleton
│   ├── build_manager.py             ← BuildManager: save/load/resolve
│   ├── models/
│   │   ├── build.py                 ← PlayerBuild
│   │   ├── status.py                ← StatusData
│   │   ├── weapon.py                ← Weapon + RANGED_WEAPON_TYPES
│   │   ├── skill.py                 ← SkillInstance
│   │   ├── target.py                ← Target
│   │   └── damage.py                ← DamageResult + DamageStep
│   ├── calculators/
│   │   ├── status_calculator.py
│   │   ├── battle_pipeline.py
│   │   └── modifiers/
│   │       ├── base_damage.py       ← battle_calc_base_damage2
│   │       ├── skill_ratio.py       ← includes SC_OVERTHRUST/OVERTHRUSTMAX
│   │       ├── size_fix.py          ← reference only, not called
│   │       ├── attr_fix.py
│   │       ├── defense_fix.py
│   │       ├── mastery_fix.py
│   │       ├── active_status_bonus.py  ← SC_AURABLADE only
│   │       └── final_rate_bonus.py
│   └── data/pre-re/
│       ├── skills.json
│       ├── db/
│       │   ├── item_db.json         ← 708 weapons, all fields, _scraped_at ✓
│       │   └── mob_db.json          ← 1007 mobs, all fields, _scraped_at ✓
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
    ├── app_config.py
    └── main_window.py               ← test scaffold, to be redesigned
```

---

## Data Models — Key Details

### PlayerBuild (`core/models/build.py`)
- `base_X` / `bonus_X` stat split
- `equipped: Dict[str, Optional[int]]` — slot → item ID
- `refine_levels: Dict[str, int]` — slot → refine level
- `weapon_element: Optional[int] = None` — element 0-9 override for right_hand.
  No level — attack elements never have a level. None = use item_db element.
- `target_mob_id: Optional[int]` — resolved via `loader.get_monster()` at runtime
- `active_status_levels: Dict[str, int]` — e.g. `{"SC_AURABLADE": 1}`
- `mastery_levels: Dict[str, int]`
- `is_riding_peco: bool`
- `is_ranged_override: Optional[bool] = None` — derived from weapon type normally
- `no_sizefix: bool`
- `is_katar` — REMOVED, derived from weapon_type == W_KATAR

### Weapon (`core/models/weapon.py`)
- `RANGED_WEAPON_TYPES: frozenset` — W_BOW, W_MUSICAL, W_WHIP, W_REVOLVER,
  W_RIFLE, W_GATLING, W_SHOTGUN, W_GRENADE
- `element: int` — no level; overridden by `build.weapon_element` when set
- `aegis_name: str`, `refineable: bool`

### Target (`core/models/target.py`)
- Pipeline: `def_`, `vit`, `size`, `race`, `element`, `element_level`, `is_boss`, `level`
- Display: `hp`, `mdef`, `atk_min`, `atk_max`, `sprite_name`, `name`
- Element level belongs on Target only — never on attack sources.

### DamageStep (`core/models/damage.py`)
Every step requires: `name`, `value`, `note`, `formula`, `hercules_ref`.

### DamageResult (`core/models/damage.py`)
Currently carries a single damage value per step. Once C6 is implemented, each
step from the crit branch decision point onward must carry both a `normal` and
`crit` value. Design the model to support this before the GUI is built.

### DataLoader (`core/data_loader.py`)
- Singleton: `from core.data_loader import loader`
- All access via public methods only
- `get_monster(mob_id) -> Target` — WARNING + safe default on missing ID
- `get_monster_data(mob_id) -> Optional[Dict]` — GUI display

### BuildManager (`core/build_manager.py`)
- `save_build(build, path)`, `load_build(path) -> PlayerBuild`, `list_builds(dir)`
- `resolve_weapon(item_id, refine=0, element_override=None) -> Weapon`
  Missing ID → WARNING + Unarmed fallback (ATK 0, wlv 1, neutral, no overrefine).
  Unarmed is distinct from W_FIST.

---

## Data Architecture

### Separation of Concerns
- **Build file:** base stats, job, level, refine levels, item IDs, buff levels,
  mastery levels, flags, weapon_element override, target_mob_id.
- **Item database:** ATK, weapon type, weapon level, base element, weight,
  refineable — intrinsic item properties.
- **Mob database:** all Target pipeline fields. Never hardcode in save files or GUI.

### Parser Completeness Rule
Both scrapers must capture **all** fields from their .conf files. The JSON is the
authoritative local copy — future features must never require a re-scrape because
a field was filtered out. Add `_scraped_at` ISO timestamp to every output.

### Build File Schema
```json
{
  "name": "My LK",
  "job_id": 7,
  "base_level": 99,
  "base_stats": { "str": 80, "agi": 30, "vit": 70, "int": 10, "dex": 50, "luk": 10 },
  "bonus_stats": { "str": 0, "agi": 0, "vit": 0, "int": 0, "dex": 0, "luk": 0,
                   "hit": 0, "flee": 0, "cri": 0, "batk": 0 },
  "target_mob_id": 1619,
  "equipped": { "right_hand": 1225, "ammo": null },
  "refine": { "right_hand": 0 },
  "weapon_element": 3,
  "active_buffs": { "SC_OVERTHRUST": 5 },
  "mastery_levels": { "SM_SWORD": 10 },
  "flags": { "is_ranged_override": null, "is_riding_peco": false, "no_sizefix": false }
}
```

---

## Phase Plan

### Completed
- Pipeline core, all modifiers, StatusCalculator
- Group A formula fixes (A1–A5)
- Group B data fixes (B1–B6)
- Phase 1: save/load system, BuildManager, build schema
- Phase 2: item_db scraper (708 weapons)
- Phase 3: mob_db scraper (1007 mobs), get_monster(), get_monster_data()
- C4: refineable flag wired up
- C5: is_ranged/is_katar derived from weapon type
- base_damage.py order fix; Weapon ATK Range step added
- Preset migration: test_presets/ deleted, scaffolds in saves/
- D1: both scrapers expanded to all fields, _scraped_at added
- D2: weapon_elements → weapon_element: Optional[int]

### Next: D3 (equipment DB expansion) → C6 (crits) → GUI redesign

**D3 — Equipment DB + crit investigation (combined session)**
Expand item_db scraper to cover all equippable types beyond IT_WEAPON.
While reading item scripts and gear data, log all modifiers found that affect:
- Crit chance (bCritical, bCriticalLong, etc.)
- Crit damage %
- Any conditional crit effects
- Any effect that reads or modifies DEF values after the fact
Collect findings into a crit modifier inventory before C6 begins.
Cards are scraped but effects deferred to D5.

**C6 — Crit implementation (after D3)**
Full crit system implementation. Requires D3 findings to be complete first.
See C6 entry in Open Items for the full specification.

**GUI redesign (after C6)**
`main_window.py` must be fully replaced. Propose layout before writing any code.
GUI must be designed knowing that crittable attacks show both normal and crit rows
from the crit decision point onward. See GUI Vision section.

---

## Open Items

### GROUP C — Pipeline Gaps

#### C1. Damage Variance
Three confirmed sources, all discrete uniform distributions:
- **Weapon ATK range** — `rnd() % (atkmax - atkmin) + atkmin` (battle.c:652-655)
- **Overrefine bonus** — `rnd() % overrefine + 1` (battle.c:~680-685)
- **VIT DEF** — `rnd() % variance_max` in battle_calc_defense.
  Current avg uses `variance_max / 2`; correct is `(variance_max - 1) / 2`.

**Distribution model:** track variance sources as `(min, max, scale)` tuples where
scale = product of all deterministic multipliers applied after that source. Final
damage is a sum/difference of scaled discrete uniforms — closed-form piecewise
polynomial with exact moments. Enables full statistical analysis without simulation.
Keep variance sources and deterministic multipliers strictly separated.

Read exact source lines before implementing. Verify on private server.
Use VIT=0 targets to isolate weapon variance from DEF variance.

#### C2. FinalRateBonus — context unclear
`short_damage_rate` / `long_damage_rate` are map-level properties in Hercules
(`map->list[bl->m]`), not global BattleConfig. Verify before fixing.

#### C3. StatusCalculator — ASPD, HP, SP placeholders
Requires `job_aspd_base.json` and full job HP/SP multiplier tables.

#### C6. Crit system (implement after D3) — DO NOT START BEFORE D3 IS COMPLETE
Crits are a parallel damage branch that must be calculated alongside normal damage
for any attack that can crit. The GUI will show both normal and crit rows for all
steps from the crit decision point onward.

**What is known:**
- Crits bypass DEF (exact mechanism TBD — see verification required below)
- Crits enforce maximum weapon ATK range (Overrefine Bonus still has variance)
- Crit damage % modifiers from skills/gear/scripts stack on the base crit result
- Normal attacks always have crit chance
- Only skills with the NK_CRITICAL flag (verify against Hercules skill data) can crit
- `cri` is already tracked in StatusData (0.1% units)

**What must be verified against Hercules source before implementing:**
1. Exact DEF bypass mechanism in the crit branch of `battle_calc_weapon_attack`:
   - Are DEF values zeroed before DefenseFix runs, or is the reduction step skipped
     while values remain readable? This matters because later effects may read DEF
     values from the pipeline — the values must remain accessible.
2. Which variance sources are enforced to max on crit — weapon ATK range is
   confirmed, but overrefine variance is unverified. Check the crit branch in
   `battle_calc_base_damage2` explicitly.
3. VIT DEF variance: irrelevant since DEF is bypassed, but confirm.
4. Verify NK_CRITICAL is the correct skill flag for crit eligibility, or identify
   the actual mechanism.
5. Crit damage % modifier: identify all sources in pre-renewal (skills, gear,
   cards, SCs). D3 investigation should surface these — collect before implementing.

**DamageResult model change required:**
From the crit decision point onward, every step must carry both `normal` and `crit`
values. Update `DamageResult` and `DamageStep` to support dual values before
implementing the pipeline changes. The step name, note, formula, and hercules_ref
remain singular — only the value(s) split.

---

### GROUP D — Data Infrastructure

#### D1. DONE — Parser completeness
#### D2. DONE — weapon_element fix

#### D3. DONE — Equipment DB expansion
item_db scraper expanded to IT_ARMOR (1431), IT_CARD (538), IT_AMMO (83) in addition
to IT_WEAPON (708). Total: 2760 items in item_db.json. IT_CASH and consumable types
skipped (not equippable).
Schema changes vs D1:
- All entries now include `"type"` field (discriminator).
- `loc` normalized to list for all types (was string for weapons).
- IT_ARMOR adds: def (int), slots, refineable, view_sprite, on_equip_script, on_unequip_script.
- IT_CARD: shared fields only (script contains the card effect).
- IT_AMMO adds: atk, subtype (A_* string), element.
DataLoader.get_items_by_type(item_type) added for GUI equipment browser.
Cards are scraped but effects deferred to D5.

#### D4. Card effects (blocked on D5)
Cards in item_db have script fields. Raw data captured in D1/D3. Implementation
requires script parsing (D5). Deferred until pipeline and GUI are stable.

#### D5. Script parsing and effect implementation (late stage)
Raw script strings are already in item_db.json. Interpreting them touches nearly
every system. Dedicated late-stage phase after GUI is stable and pipeline verified.

---

## GUI Vision

### Design Philosophy: Progressive Disclosure
- **Default:** damage summary card + clean step list (name + value only)
- **Hover:** tooltip with `note` and `formula`
- **Power user toggle:** `hercules_ref` inline per step
- ttk.Treeview must be fully replaced. DamageStep fields are already correct.
- For crittable attacks: show normal and crit rows in parallel from the crit
  decision point onward. GUI must be designed with this in mind from the start.

### Layout
Not yet decided. Propose before implementing. Fast iteration across
builds/skills/targets is the top priority. Must accommodate all 9 features
without feeling cluttered in the common case.

### Required Features
1. Outgoing damage calculator — progressive disclosure, normal + crit rows
2. Incoming damage calculator
3. Stat point planner — interactive allocation, live recalculation
4. Skill browser / selector
5. Equipment browser — all slots: weapon, armor, shield, garment, footwear,
   accessories. Required for full stat calculations.
6. Monster database — search, filter, select as target
7. Custom inputs — manually configure anything not in DB
8. Saved builds — save and load named builds
9. Comparison tool — builds / skills / targets side by side

### Results View
- Summary card: normal damage range, crit damage range (when applicable),
  crit chance, hit chance
- Step list: normal + crit columns from crit decision point onward
- Hover: `note` + `formula`
- "Show Source" toggle: `hercules_ref` per step

---

## Coding Conventions
- Modifiers: `@staticmethod def calculate(...)` — no instantiation
- One file per modifier
- `result.add_step(...)` for every calculation — never silently mutate
- All magic numbers cite Hercules source in comments
- No global state outside `loader`
- No `sudo`

---

## Verification & Testing

Two scaffold builds in saves/. Real item IDs and mob_db targets. Stats still have
placeholder 1s for agi/dex/int/luk — do not treat output as verified reference.

Proper tests require: known reference values from in-game measurement or rocalc.com,
full input specification, pipeline coverage including isolated modifiers, and
variance handling (use VIT=0 targets until variance is fully implemented).

Design a pytest framework first — propose structure before implementing.
Fixtures must document expected value sources.