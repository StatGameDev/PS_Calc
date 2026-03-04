# PS_Calc — Claude Code Instructions

## BEFORE YOU START: Ask First, Search Later

**If a task requires locating files, external data, or unfamiliar formats — ask the
user first.** The user is present and can provide exact paths, paste file contents,
or answer format questions in one message. Do not spend tokens searching, grepping
speculatively, or reading large files to answer a question the user can answer
instantly.

Examples of when to ask:
- "Where are the downloaded rocalc JS files?" → ask, don't search ~/Downloads
- "What is the array index for weapon refine in rocalc saves?" → ask
- "Which Hercules function handles X?" → grep battle.c once, then ask if not found

When in doubt: one targeted grep or read is fine. Exploratory multi-file searches
are not. Stop and ask after one failed attempt.

---

## Project Overview

Pre-renewal Ragnarok Online toolkit in Python/CustomTkinter.
Goal: faithful Hercules emulator port with full-featured GUI for players and theorycrafters.
Reference: Hercules emulator cloned at `./Hercules/`. All formulas must be traceable to source.

---

## Non-Negotiable Rules

- **Pre-renewal only.**
- **Hercules is the source of truth.** One targeted grep before asking. No wikis.
- **Every DamageStep must cite its source.** `hercules_ref` = exact file + function.
- **Python 3.13.** No deprecated APIs.
- **GUI: CustomTkinter.** No raw Tkinter except unavoidable scaffolds.
- **`status.int_` not `status.int`** everywhere.

### Renewal vs Pre-Renewal Guards — CRITICAL

- `#ifdef RENEWAL` — ignore entirely.
- `#ifndef RENEWAL` — pre-renewal only, implement this.
- No guard — applies to both.

Always check guards before implementing anything:
`sed -n 'START,ENDp' Hercules/src/map/battle.c | grep -n "RENEWAL"`

Known renewal-only mechanics (must NOT appear in pre-renewal code):
LUK→HIT, LUK→FLEE, SC_IMPOSITIO ATK_ADD in battle_calc_base_damage2,
SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2.

---

## Hercules Source

`./Hercules/src/map/` — battle.c, status.c, skill.c, pc.c

```bash
grep -n "function_name" Hercules/src/map/battle.c
sed -n 'START,ENDp' Hercules/src/map/battle.c
```
Always grep first. Never load entire files.

---

## Project Structure

```
PS_Calc/
├── CLAUDE.md
├── main.py
├── saves/                           ← user builds (JSON); 6 builds from rocalc ✓
│   ├── knight_bash.json             ← scaffold (placeholder stats)
│   ├── spear_peco.json              ← scaffold (placeholder stats)
│   ├── ak77_hunter.json             ← rocalc import (8 items, [MISMATCH] flagged)
│   ├── dd_sin.json                  ← rocalc import (10 items, dual wield)
│   ├── nat_crit_sin.json            ← rocalc import (8 items, 1 unresolved)
│   ├── agi_bs.json                  ← rocalc import (8 items)
│   ├── combo_monk.json              ← rocalc import (10 items)
│   └── ip_rogue.json                ← rocalc import (10 items)
├── tools/
│   ├── import_item_db.py            ← item_db.conf → item_db.json
│   ├── import_mob_db.py             ← mob_db.conf → mob_db.json
│   └── import_rocalc_saves.py       ← rocalc localStorage → build JSON ✓
├── Hercules/                        ← reference only, never modify
├── core/
│   ├── config.py                    ← BattleConfig (includes critical_min)
│   ├── data_loader.py               ← singleton; get_monster, get_items_by_type
│   ├── build_manager.py             ← save/load/resolve_weapon
│   ├── models/
│   │   ├── build.py                 ← PlayerBuild
│   │   ├── status.py                ← StatusData (use int_ not int)
│   │   ├── weapon.py                ← Weapon + RANGED_WEAPON_TYPES
│   │   ├── skill.py                 ← SkillInstance
│   │   ├── target.py                ← Target (includes luk)
│   │   └── damage.py                ← DamageResult + BattleResult
│   ├── calculators/
│   │   ├── status_calculator.py
│   │   ├── battle_pipeline.py       ← _run_branch(is_crit) → BattleResult
│   │   └── modifiers/
│   │       ├── base_damage.py       ← is_crit forces atkmax
│   │       ├── refine_fix.py        ← flat ATK_ADD2; after defense, before mastery
│   │       ├── skill_ratio.py
│   │       ├── attr_fix.py
│   │       ├── defense_fix.py       ← is_crit: idef=idef2=1, values remain
│   │       ├── mastery_fix.py
│   │       ├── active_status_bonus.py  ← SC_AURABLADE only
│   │       ├── crit_chance.py
│   │       ├── crit_atk_rate.py
│   │       ├── size_fix.py          ← reference only
│   │       └── final_rate_bonus.py
│   └── data/pre-re/
│       ├── skills.json
│       ├── db/
│       │   ├── item_db.json         ← 2760 items (weapon/armor/card/ammo)
│       │   └── mob_db.json          ← 1007 mobs
│       └── tables/                  ← attr_fix, size_fix, mastery_fix, etc.
└── gui/
    ├── app_config.py
    └── main_window.py               ← scaffold, to be redesigned
```

### Pipeline Step Order
```
BaseDamage → SkillRatio → DefenseFix → CritAtkRate (crit only) →
RefineFix → ActiveStatusBonus → MasteryFix → AttrFix → FinalRateBonus
```

---

## Key Data Models

### PlayerBuild
- `base_X` / `bonus_X` stat split; `equipped: Dict[str, Optional[int]]`
- `refine_levels: Dict[str, int]`; `weapon_element: Optional[int] = None`
- `target_mob_id`, `active_status_levels`, `mastery_levels`
- `is_riding_peco`, `is_ranged_override`, `no_sizefix`
- `is_katar` — REMOVED, derived from weapon_type == W_KATAR

### BattleResult
```python
@dataclass
class BattleResult:
    normal: DamageResult
    crit: Optional[DamageResult]  # None if not crittable
    crit_chance: float
    hit_chance: float             # placeholder, E1 not yet implemented
```
Branches diverge at BaseDamage. Crit: atkmax forced; DEF skipped via
`idef=idef2=1` (values remain readable); `crit_atk_rate` applied pre-defense
(battle.c:5333 — functionally identical since DEF bypassed).

### Target — pipeline fields
`def_`, `vit`, `luk`, `size`, `race`, `element`, `element_level`, `is_boss`, `level`

### DamageStep — required fields
`name`, `value`, `note`, `formula`, `hercules_ref`

### DataLoader (singleton)
`from core.data_loader import loader`
- `get_monster(mob_id) -> Target`
- `get_monster_data(mob_id) -> Optional[Dict]`
- `get_items_by_type(item_type) -> list`

### BuildManager
`resolve_weapon(item_id, refine=0, element_override=None) -> Weapon`
Missing ID → WARNING + Unarmed fallback (ATK 0, wlv 1, neutral).

---

## Data Architecture

- **Build file:** stats, item IDs, refine, buffs, masteries, flags, weapon_element, target_mob_id
- **item_db.json:** intrinsic item properties (ATK, type, wlv, element, DEF, scripts)
- **mob_db.json:** all Target pipeline fields — never hardcode in builds or GUI

### Parser Completeness Rule
Scrapers capture ALL fields from .conf files. JSON = authoritative local copy.
Never filter at scrape time. `_scraped_at` timestamp on every output.

### Build File Schema
```json
{
  "name": "My LK", "job_id": 7, "base_level": 99,
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

## Completed Work

- Pipeline core + all modifiers
- A1–A7: formula fixes (int_ rename, SizeFix, pipeline order, refine position, DEX scaling)
- B1–B6: data fixes (SC cleanups, preset migration)
- C4, C5: refineable flag, derived is_ranged/is_katar
- C6: crit system (BattleResult, eligibility whitelist, katar bug fix, dual branch)
- D1–D3: scrapers expanded (2760 items: weapon/armor/card/ammo; all mob fields)
- Display fixes: overrefine step restored; SizeFix avg/min collapse fixed (7954002)
- Test builds: 6 rocalc saves imported; all equipment slots decoded via SaveLocal()
  field map; dual wield resolved; item/DB mismatch flagging in place

---

## Open Items

### C — Pipeline Gaps

**C1. Damage Variance** — three discrete uniform sources:
- Weapon ATK range: `rnd(atkmin, atkmax)` — crit forces atkmax
- Overrefine: `rnd(1, overrefine_max)` — NOT maxed on crit
- VIT DEF: `rnd(0, variance_max-1)` — bypassed on crit; current avg off by 0.5
Track as `(min, max, scale)` tuples for closed-form distribution (scaled uniform sum).
Keep variance sources and deterministic multipliers strictly separated.

**C2. FinalRateBonus** — `short/long_damage_rate` are map-level in Hercules, not
global BattleConfig. Verify before fixing.

**C3. StatusCalculator** — ASPD, HP, SP are placeholders.

### D — Data Infrastructure
**D4.** Card effects — blocked on D5.
**D5.** Script parsing — late stage, after GUI stable.

### E — Additional Pipeline Mechanics
**E1.** Hit/Miss — `80 + HIT - FLEE`% hit chance; Perfect Dodge `1+[LUK/10]+bonus`%.
`hit_chance` placeholder on BattleResult. Implement before output is meaningful.

**E2.** Damage Bonus/Reduction — card/gear size/race/element/special multipliers.
`(1+SizeBonus/100) * (1+RaceBonus/100) * ...` — step scaffold after AttrFix,
blocked on D5 for values.

**E3.** Bane skills — Beast/Demon Bane, Dragonology. After VIT DEF, before RefineFix.

**E4.** Katar second hit — fraction of primary total. Verify fraction from source.

**E5.** SC_IMPOSITIO in BATK — likely feeds `bonus_batk`. Verify against source.

**E6.** Forged weapon Verys — flat +5/Very after elemental modifier.

**E7.** Cart Revolution double elemental fix — `attr_fix` twice (weapon elem then
ELE_NEUTRAL), results multiply. Investigate Ghost targets before implementing.

**E8.** GS_GROUNDDRIFT — separate `50*lv` neutral component with own elemental fix.

---

## GUI Vision

### Progressive Disclosure
Default: summary card + step list (name + value). Hover: note + formula.
Toggle: hercules_ref per step. ttk.Treeview fully replaced.
Crittable attacks: normal + crit columns from BaseDamage onward.

### Required Features
1. Outgoing damage calc — normal + crit columns
2. Incoming damage calc
3. Stat point planner
4. Skill browser/selector
5. Equipment browser — all slots (weapon/armor/shield/garment/footwear/accessories)
6. Monster DB — search, filter, select target
7. Custom inputs
8. Saved builds
9. Comparison tool

**Propose layout before writing any code.**

### Results View
Summary card: normal range, crit range, crit%, hit%.
Step list: normal + crit columns from BaseDamage. Hover: note+formula.
"Show Source" toggle: hercules_ref per step.

---

## Coding Conventions
- Modifiers: `@staticmethod def calculate(...)` — no instantiation
- `result.add_step(...)` for every calculation — never silently mutate
- All magic numbers cite Hercules source in comments
- No global state outside `loader`; no `sudo`

---

## Verification & Testing

6 rocalc builds in saves/ with real stats and equipment. Scaffold builds
(knight_bash, spear_peco) retain placeholder stats — do not use for verification.
AK77 Hunter build has [MISMATCH] flags on items due to item DB version drift —
review before using as test fixture.

Proper tests need: known reference values (in-game or rocalc), full input spec,
isolated modifier coverage, VIT=0 targets for variance isolation.
Design pytest framework first — propose structure before implementing.
Fixtures must document expected value sources.