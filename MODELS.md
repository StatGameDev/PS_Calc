# PS_Calc — Data Models Reference

_Load this file when working on core/models/, core/calculators/, or any session
touching PlayerBuild, BattleResult, or data loading._

---

## Key Models

### PlayerBuild (core/models/build.py)
- `base_X` / `bonus_X` stat split (STR/AGI/VIT/INT/DEX/LUK)
- `equipped: Dict[str, Optional[int]]` — item IDs by slot
- `refine_levels: Dict[str, int]`
- `weapon_element: Optional[int]`
- `target_mob_id, active_status_levels, mastery_levels`
- `is_riding_peco, is_ranged_override, no_sizefix`
- `is_katar` — REMOVED, always derived from `weapon_type == W_KATAR`
- `server: str` — `"standard"` or `"payon_stories"`

Build file canonical schema: see build_manager.py. Fields: name, job_id, base_level,
server, base_stats, bonus_stats, target_mob_id, equipped, refine, weapon_element,
active_buffs, mastery_levels, flags.

### BattleResult (core/models/damage.py)
```python
@dataclass
class BattleResult:
    normal: DamageResult
    crit: Optional[DamageResult]  # None if not crittable
    crit_chance: float
    hit_chance: float             # placeholder until E1 implemented
```

### DamageStep — required fields
`name, value, note, formula, hercules_ref`

### Target — pipeline fields (core/models/target.py)
`def_, vit, luk, size, race, element, element_level, is_boss, level`
Never hardcode these in builds or GUI — always sourced from mob_db.json.

---

## DataLoader (singleton)

```python
from core.data_loader import loader
loader.get_monster(mob_id) -> Target
loader.get_monster_data(mob_id) -> Optional[Dict]
loader.get_items_by_type(item_type) -> list
```

## BuildManager

```python
resolve_weapon(item_id, refine=0, element_override=None) -> Weapon
# Missing ID → WARNING + Unarmed fallback (ATK 0, wlv 1, neutral)
```

---

## Data Architecture Rules

- `item_db.json`: intrinsic item properties (ATK, type, wlv, element, DEF, scripts).
- `mob_db.json`: all Target pipeline fields.
- Scrapers capture ALL fields from .conf files. Never filter at scrape time.
  `_scraped_at` timestamp on every output. JSON is the authoritative local copy.

---

## Project Structure (key paths)

    core/
    ├── config.py               ← BattleConfig (includes critical_min)
    ├── data_loader.py          ← singleton
    ├── build_manager.py        ← save/load/resolve_weapon
    ├── models/                 ← build, status, weapon, skill, target, damage
    ├── calculators/
    │   ├── status_calculator.py
    │   ├── battle_pipeline.py  ← _run_branch(is_crit) -> BattleResult
    │   └── modifiers/          ← one file per pipeline step
    └── data/pre-re/
        ├── skills.json
        └── db/
            ├── item_db.json    ← 2760 items
            └── mob_db.json     ← 1007 mobs

    gui/
    ├── app_config.py           ← UI_SCALE, font size constants
    ├── layout_config.json      ← section order, panel assignment, compact rules
    ├── themes/dark.qss         ← master stylesheet
    ├── main_window.py
    ├── panel_container.py      ← QSplitter, FOCUS state logic
    ├── panel.py                ← QScrollArea, StepsBar
    ├── section.py              ← Section base class
    └── sections/               ← one file per section
